"""Construct exam and answer-key documents from already ordered questions."""
import html
import re

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from PySide6.QtGui import QFont, QTextCharFormat, QTextDocument

from prometheus.export.images import ImageReadError, append_image, embed_html_images, ensure_exportable, read_image
from prometheus.domain.exam_questions import as_exam_question


def _footer(doc, version_number):
    paragraph = doc.sections[0].footer.paragraphs[0]
    if version_number is not None:
        paragraph.add_run(f'Versão {version_number} | ')
    paragraph.add_run('Página ')
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    run = OxmlElement('w:r'); value = OxmlElement('w:t'); value.text = '1'
    run.append(value); field.append(run)
    paragraph._p.append(field)


def _append_html(doc, question_id, content, prefix, acknowledged):
    paragraph = doc.add_paragraph()
    if prefix:
        run = paragraph.add_run(prefix); run.bold = True; run.font.size = Pt(12)
    content = content or ''
    if not re.search(r'<(?:!doctype|/?html|/?body|/?p|/?div|/?span|/?br|/?img|/?b|/?strong|/?i|/?em|/?u|/?sup|/?sub)\b', content, re.IGNORECASE):
        content = html.escape(content).replace('\n', '<br>')
    content, newly_missing = embed_html_images(content)
    for source in newly_missing:
        if (question_id, source) not in acknowledged:
            raise ValueError(f'Imagem da questão {question_id} não pôde ser exportada.')
    q_doc = QTextDocument(); q_doc.setHtml(content)
    section = doc.sections[0]
    text_width = (section.page_width - section.left_margin - section.right_margin) / 914400
    block = q_doc.begin()
    while block.isValid():
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid():
                fmt = fragment.charFormat()
                if fmt.isImageFormat():
                    image_format = fmt.toImageFormat(); source = image_format.name()
                    if (question_id, source) not in acknowledged:
                        try:
                            image = read_image(source)
                        except ImageReadError as exc:
                            raise ValueError(f'Imagem da questão {question_id} não pôde ser exportada.') from exc
                        append_image(paragraph, image, image_format.width(), text_width, image_format.height())
                else:
                    text = fragment.text()
                    if text:
                        run = paragraph.add_run(text); run.font.name = 'Arial'; run.font.size = Pt(12)
                        run.bold = fmt.fontWeight() == QFont.Bold
                        run.italic = fmt.fontItalic(); run.underline = fmt.fontUnderline()
                        run.font.strike = fmt.fontStrikeOut()
                        run.font.superscript = fmt.verticalAlignment() == QTextCharFormat.AlignSuperScript
                        run.font.subscript = fmt.verticalAlignment() == QTextCharFormat.AlignSubScript
                        if fmt.fontPointSize() > 0:
                            run.font.size = Pt(fmt.fontPointSize())
            iterator += 1
        block = block.next()
        if block.isValid():
            paragraph = doc.add_paragraph()


def _write_answer_key(doc, questions, version_number, acknowledged):
    title = 'Gabarito Oficial' + (f' — Versão {version_number}' if version_number is not None else '')
    doc.add_heading(title, level=1)
    for index, question in enumerate(questions, start=1):
        if question.kind == 'multiple_choice':
            p = doc.add_paragraph(); p.add_run(f'{index}) ').bold = True; p.add_run(str(question.answer or ''))
        elif question.answer and question.answer.strip():
            _append_html(doc, question.id, question.answer, f'{index}) Resolução Esperada:\n', acknowledged)
        else:
            p = doc.add_paragraph(); p.add_run(f'{index}) Resolução Esperada: ').bold = True
            p.add_run('Sem resolução cadastrada no sistema.')


def build_exam_documents(questions, *, version_number=None, answer_placement='end', acknowledge_images=False, acknowledged_images=None):
    if answer_placement not in ('end', 'separate', 'none'):
        raise ValueError('invalid answer placement')
    questions = [as_exam_question(question) for question in questions]
    acknowledged = ensure_exportable(questions, include_answers=answer_placement != 'none',
                                    acknowledge=acknowledge_images, acknowledged=acknowledged_images)
    exam = Document(); _footer(exam, version_number)
    if version_number is not None:
        exam.add_paragraph(f'Versão {version_number}')
    for index, question in enumerate(questions, start=1):
        _append_html(exam, question.id, question.statement, f'{index}) ', acknowledged)
        if question.kind == 'multiple_choice':
            for letter, alternative in zip('ABCDE', question.alternatives):
                _append_html(exam, question.id, alternative or '', f'{letter}) ', acknowledged)
        exam.add_paragraph('')
    key = None
    if answer_placement == 'end':
        exam.add_page_break(); _write_answer_key(exam, questions, version_number, acknowledged)
    elif answer_placement == 'separate':
        key = Document(); _footer(key, version_number)
        _write_answer_key(key, questions, version_number, acknowledged)
    return exam, key


def exam_content_fingerprint(doc, *, version_number=None):
    """Fingerprint visible student content, independent of incidental run XML."""
    from hashlib import sha256
    from docx.text.paragraph import Paragraph

    body = [element for element in doc._element.body if element.tag == qn('w:p')]
    if version_number is not None:
        body = body[1:]
    for index, element in enumerate(body):
        styles = element.xpath('./w:pPr/w:pStyle')
        text = ''.join(element.xpath('.//w:t/text()'))
        if styles and styles[0].get(qn('w:val')) == 'Heading1' and text.startswith('Gabarito Oficial'):
            body = body[:index]
            if body and not ''.join(body[-1].xpath('.//w:t/text()')) and body[-1].xpath('.//w:br[@w:type="page"]'):
                body.pop()
            break
    content = []
    for element in body:
        paragraph = Paragraph(element, doc)
        tokens = []
        for run in paragraph.runs:
            font = run.font
            style = (font.name, font.size.pt if font.size else None, bool(run.bold),
                     bool(run.italic), bool(run.underline), bool(font.strike),
                     bool(font.superscript), bool(font.subscript))
            for child in run._r:
                if child.tag in (qn('w:t'), qn('w:tab'), qn('w:br'), qn('w:cr')):
                    value = child.text or '' if child.tag == qn('w:t') else ('\t' if child.tag == qn('w:tab') else '\n')
                    if value:
                        if tokens and tokens[-1][0] == 'text' and tokens[-1][1] == style:
                            tokens[-1] = ('text', style, tokens[-1][2] + value)
                        else:
                            tokens.append(('text', style, value))
                elif child.tag == qn('w:drawing'):
                    for blip in child.xpath('.//a:blip'):
                        relation = blip.get(qn('r:embed'))
                        extents = child.xpath('.//wp:extent')
                        dimensions = tuple((extent.get('cx'), extent.get('cy')) for extent in extents)
                        if relation:
                            tokens.append(('image', sha256(doc.part.related_parts[relation].blob).hexdigest(), dimensions))
        content.append(tuple(tokens))
    return sha256(repr(content).encode('utf-8')).digest()
