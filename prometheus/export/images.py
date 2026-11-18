"""Preflight and render locally available images without network access."""
import base64
import os
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit

from docx.image.image import Image
from docx.shared import Inches
from PySide6.QtGui import QImage


class ImageReadError(ValueError):
    pass


@dataclass(frozen=True)
class ImageData:
    blob: bytes
    width: int
    height: int


@dataclass(frozen=True)
class ImageIssue:
    question_id: int
    source: str
    reason: str


class _ImageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'img':
            self.sources.append(dict(attrs).get('src', ''))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def image_sources(html):
    parser = _ImageParser(); parser.feed(html or ''); parser.close()
    return parser.sources


def read_image(source):
    if not source:
        raise ImageReadError('Imagem sem endereço.')
    try:
        if source.lower().startswith('data:'):
            header, encoded = source.split(',', 1)
            if not header.lower().startswith(('data:image/png;', 'data:image/jpeg;')) or not header.lower().endswith(';base64'):
                raise ImageReadError('Formato de imagem incorporada não suportado.')
            blob = base64.b64decode(encoded, validate=True)
        else:
            parsed = urlsplit(source)
            if parsed.scheme.lower() == 'file' and parsed.netloc in ('', 'localhost'):
                local_path = unquote(parsed.path)
                if os.name == 'nt' and re.match(r'^/[A-Za-z]:/', local_path):
                    local_path = local_path[1:]
                path = Path(local_path)
            elif (not parsed.scheme and not parsed.netloc) or (os.name == 'nt' and re.match(r'^[A-Za-z]:[\\/]', source)):
                path = Path(source)
            else:
                raise ImageReadError('Imagem externa não pode ser baixada.')
            blob = path.read_bytes()
        qimage = QImage.fromData(blob)
        if qimage.isNull():
            raise ImageReadError('Imagem inválida ou não legível.')
        Image.from_blob(blob)
        return ImageData(blob, qimage.width(), qimage.height())
    except ImageReadError:
        raise
    except Exception as exc:
        raise ImageReadError('Imagem inválida ou não legível.') from exc


def inspect_question_images(questions, include_answers=True):
    from prometheus.domain.exam_questions import as_exam_question
    issues = []
    for question in questions:
        question = as_exam_question(question)
        contents = [question.statement]
        if question.kind == 'multiple_choice':
            contents.extend(question.alternatives)
        elif include_answers:
            contents.append(question.answer)
        for content in contents:
            for source in image_sources(content):
                try:
                    read_image(source)
                except ImageReadError as exc:
                    issues.append(ImageIssue(question.id, source, str(exc)))
    return issues


def append_image(paragraph, image, display_width_px, text_width_inches, display_height_px=None):
    if display_width_px and display_width_px > 0:
        width = display_width_px
    elif display_height_px and display_height_px > 0:
        width = display_height_px * image.width / image.height
    else:
        width = image.width
    paragraph.add_run().add_picture(BytesIO(image.blob), width=Inches(min(width / 96, text_width_inches)))


class UnexportableImages(ValueError):
    def __init__(self, issues):
        self.issues = tuple(issues)
        ids = ', '.join(str(value) for value in sorted({issue.question_id for issue in self.issues}))
        super().__init__('Imagens não exportáveis nas questões: ' + ids)


def ensure_exportable(questions, *, include_answers=True, acknowledge=False, acknowledged=None):
    issues = inspect_question_images(questions, include_answers=include_answers)
    allowed = {(issue.question_id, issue.source) for issue in issues} if acknowledge else set(acknowledged or ())
    unapproved = [issue for issue in issues if (issue.question_id, issue.source) not in allowed]
    if unapproved:
        raise UnexportableImages(unapproved)
    return allowed


def _data_uri(image):
    if image.blob.startswith(b'\x89PNG\r\n\x1a\n'):
        kind, blob = 'png', image.blob
    elif image.blob.startswith(b'\xff\xd8\xff'):
        kind, blob = 'jpeg', image.blob
    else:
        from PySide6.QtCore import QByteArray, QBuffer, QIODevice
        qimage = QImage.fromData(image.blob)
        raw = QByteArray(); buffer = QBuffer(raw)
        if not buffer.open(QIODevice.WriteOnly) or not qimage.save(buffer, 'PNG'):
            raise ImageReadError('Não foi possível incorporar a imagem.')
        buffer.close(); kind, blob = 'png', bytes(raw)
    return 'data:image/' + kind + ';base64,' + base64.b64encode(blob).decode('ascii')


def _attribute_value_span(tag, wanted):
    """Locate an actual attribute value, skipping quoted values of other attributes."""
    match = re.match(r'<\s*[^\s/>]+', tag)
    pos = match.end() if match else len(tag)
    while pos < len(tag):
        while pos < len(tag) and tag[pos].isspace():
            pos += 1
        if pos >= len(tag) or tag[pos] in '/>':
            break
        start = pos
        while pos < len(tag) and not tag[pos].isspace() and tag[pos] not in '=/>':
            pos += 1
        name = tag[start:pos].lower()
        if pos == start:
            pos += 1
            continue
        while pos < len(tag) and tag[pos].isspace():
            pos += 1
        if pos >= len(tag) or tag[pos] != '=':
            continue
        pos += 1
        while pos < len(tag) and tag[pos].isspace():
            pos += 1
        start = pos
        if pos < len(tag) and tag[pos] in "\"'":
            quote = tag[pos]; pos += 1
            while pos < len(tag) and tag[pos] != quote:
                pos += 1
            pos = min(pos + 1, len(tag))
        else:
            while pos < len(tag) and not tag[pos].isspace() and tag[pos] != '>':
                pos += 1
        if name == wanted:
            return start, pos
    return None


class _PasteParser(HTMLParser):
    def __init__(self, fallback=None):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.issues = []
        self.fallback = fallback

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        if tag.lower() != 'img':
            self.parts.append(raw)
            return
        source = dict(attrs).get('src', '')
        try:
            replacement = _data_uri(read_image(source))
        except ImageReadError:
            if self.fallback is None:
                self.issues.append(source)
                return
            replacement = self.fallback
        span = _attribute_value_span(raw, 'src')
        if span is None:
            self.issues.append(source)
            return
        self.parts.append(raw[:span[0]] + '"' + replacement + '"' + raw[span[1]:])

    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag): self.parts.append(f'</{tag}>')
    def handle_data(self, data): self.parts.append(data)
    def handle_entityref(self, name): self.parts.append('&' + name + ';')
    def handle_charref(self, name): self.parts.append('&#' + name + ';')
    def handle_comment(self, data): self.parts.append('<!--' + data + '-->')
    def handle_decl(self, decl): self.parts.append('<!' + decl + '>')
    def handle_pi(self, data): self.parts.append('<?' + data + '>')
    def unknown_decl(self, data): self.parts.append('<![' + data + ']>')


def embed_html_images(html, fallback_image=None):
    sources = image_sources(html)
    fallback = _data_uri(fallback_image) if fallback_image is not None else None
    parser = _PasteParser(fallback if len(sources) == 1 else None)
    parser.feed(html or ''); parser.close()
    result = ''.join(parser.parts)
    if fallback is not None and not sources:
        tag = '<img src="' + fallback + '">'
        result, count = re.subn(r'(?i)</body\s*>', lambda match: tag + match.group(), result, count=1)
        if not count:
            result += tag
    return result, parser.issues


def clipboard_image_data(value):
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    try:
        image = QImage(value)
    except (TypeError, ValueError) as exc:
        raise ImageReadError('Não foi possível ler a imagem copiada.') from exc
    if image.isNull():
        raise ImageReadError('Não foi possível ler a imagem copiada.')
    if image.width() > 500:
        from PySide6.QtCore import Qt
        image = image.scaledToWidth(500, Qt.SmoothTransformation)
    raw = QByteArray(); buffer = QBuffer(raw)
    if not buffer.open(QIODevice.WriteOnly) or not image.save(buffer, 'PNG'):
        raise ImageReadError('Não foi possível incorporar a imagem copiada.')
    buffer.close()
    return ImageData(bytes(raw), image.width(), image.height())
