import base64
from docx import Document
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage
from prometheus.export.images import inspect_question_images, read_image, append_image, ImageReadError


def encoded_png(width=192, height=96):
    image = QImage(width, height, QImage.Format_RGB32); image.fill(QColor('blue'))
    raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG'); buffer.close()
    return 'data:image/png;base64,' + base64.b64encode(bytes(raw)).decode('ascii')


def test_embedding_replaces_only_the_real_source_attribute(tmp_path):
    from prometheus.export.images import embed_html_images, image_sources
    path = tmp_path / 'local.png'
    path.write_bytes(base64.b64decode(encoded_png().split(',', 1)[1]))
    html = f'''<img data-src="unused" alt='src="decoy"' width="80" height="40" src="{path.as_uri()}">'''
    embedded, issues = embed_html_images(html)
    assert not issues
    assert 'data-src="unused"' in embedded
    assert '''alt='src="decoy"' width="80" height="40"''' in embedded
    assert image_sources(embedded)[0].startswith('data:image/png;base64,')
    assert path.as_uri() not in embedded


def row(qid, statement, alternative='', answer=''):
    return [qid, '', '', 'Múltipla Escolha', statement, alternative, '', '', '', '', answer]


def test_preflight_reports_only_affected_question_ids(tmp_path):
    good = encoded_png()
    rows = [row(1, f'<p><img src="{good}"></p>'),
            row(2, '<img src="https://example.com/image.png">'),
            row(3, '<img src="data:image/png;base64,!!!">'),
            row(4, '<img src="' + str(tmp_path / 'missing.png') + '">')]
    issues = inspect_question_images(rows, include_answers=True)
    assert {issue.question_id for issue in issues} == {2, 3, 4}
    assert all(issue.reason for issue in issues)


def test_image_size_is_preserved_or_capped_proportionally():
    source = encoded_png()
    data = read_image(source)
    doc = Document(); paragraph = doc.add_paragraph()
    append_image(paragraph, data, display_width_px=192, text_width_inches=6)
    shape = doc.inline_shapes[-1]
    assert abs(shape.width.inches - 2) < .01
    assert abs(shape.height.inches - 1) < .01
    append_image(paragraph, data, display_width_px=960, text_width_inches=6)
    shape = doc.inline_shapes[-1]
    assert abs(shape.width.inches - 6) < .01
    assert abs(shape.height.inches - 3) < .01


def test_local_images_are_read_and_remote_urls_are_rejected(tmp_path):
    import pytest
    source = encoded_png()
    data = base64.b64decode(source.split(',', 1)[1]); local = tmp_path / 'image.png'; local.write_bytes(data)
    assert read_image(local.as_uri()).blob == data
    with pytest.raises(ImageReadError): read_image('https://example.com/image.png')


def test_unexportable_images_require_explicit_acknowledgement_before_output(tmp_path):
    import pytest
    from prometheus.export.images import ensure_exportable, UnexportableImages
    questions = [row(42, '<img src="https://example.com/no.png">')]
    output = tmp_path / 'exam.docx'
    with pytest.raises(UnexportableImages) as error:
        ensure_exportable(questions)
    assert {issue.question_id for issue in error.value.issues} == {42}
    assert not output.exists()
    assert ensure_exportable(questions, acknowledge=True) == {(42, 'https://example.com/no.png')}


def test_approving_one_missing_image_does_not_approve_a_different_one():
    import pytest
    from prometheus.export.images import ensure_exportable, UnexportableImages
    questions = [row(42, '<img src="https://example.com/first.png"><img src="https://example.com/second.png">')]
    with pytest.raises(UnexportableImages) as error:
        ensure_exportable(questions, acknowledged={(42, 'https://example.com/first.png')})
    assert [issue.source for issue in error.value.issues] == ['https://example.com/second.png']


def test_embedded_jpeg_is_accepted_and_exported():
    image = QImage(100, 50, QImage.Format_RGB32); image.fill(QColor('red'))
    raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'JPEG'); buffer.close()
    source = 'data:image/jpeg;base64,' + base64.b64encode(bytes(raw)).decode('ascii')
    q = row(1, '<img src="' + source + '">')
    assert inspect_question_images([q]) == []
    data = read_image(source)
    doc = Document(); append_image(doc.add_paragraph(), data, 100, 6)
    assert len(doc.inline_shapes) == 1
    assert abs(doc.inline_shapes[0].width.inches / doc.inline_shapes[0].height.inches - 2) < .01


def test_preflight_checks_alternatives_and_only_included_essay_answers():
    missing = '<img src="https://example.com/unavailable.png">'
    multiple = row(5, '<p>Questão</p>', missing, 'A')
    essay = [6, '', '', 'Dissertativa', '<p>Outra</p>', '', '', '', '', '', missing]
    assert {issue.question_id for issue in inspect_question_images([multiple, essay], include_answers=True)} == {5, 6}
    assert {issue.question_id for issue in inspect_question_images([multiple, essay], include_answers=False)} == {5}
