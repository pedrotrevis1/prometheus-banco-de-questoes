import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import pytest
from PySide6.QtWidgets import QApplication
from prometheus.export.documents import build_exam_documents
from prometheus.export.images import UnexportableImages


@pytest.fixture(scope='module', autouse=True)
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_single_exam_has_no_header_or_version_and_uses_chosen_order():
    questions = [[2, '', '', 'Dissertativa', '<p>Segunda</p>', '', '', '', '', '', '<p>Resposta B</p>'],
                 [1, '', '', 'Dissertativa', '<p>Primeira</p>', '', '', '', '', '', '<p>Resposta A</p>']]
    exam, key = build_exam_documents(questions, answer_placement='end')
    text = '\n'.join(paragraph.text for paragraph in exam.paragraphs)
    assert key is None and text.index('Segunda') < text.index('Primeira')
    assert 'Versão' not in text and 'Gabarito Oficial' in text
    assert not any(p.text for p in exam.sections[0].header.paragraphs)
    assert 'PAGE' in exam.sections[0].footer._element.xml
    assert '<w:t>1</w:t>' in exam.sections[0].footer._element.xml


def test_numbered_version_and_separate_matching_answer_key():
    question = [7, '', '', 'Múltipla Escolha', '<p>Pergunta</p>', 'um', 'dois', 'três', 'quatro', 'cinco', 'C']
    exam, key = build_exam_documents([question], version_number=2, answer_placement='separate')
    exam_text = '\n'.join(p.text for p in exam.paragraphs)
    key_text = '\n'.join(p.text for p in key.paragraphs)
    assert 'Versão 2' in exam_text and 'Gabarito' not in exam_text
    assert 'Versão 2' in key_text and 'C' in key_text
    assert 'Versão 2' in exam.sections[0].footer.paragraphs[0].text
    assert 'Versão 2' in key.sections[0].footer.paragraphs[0].text
    assert 'PAGE' in key.sections[0].footer._element.xml


def test_bad_image_must_be_acknowledged_before_document_is_built():
    question = [21, '', '', 'Dissertativa', '<p>x</p><img src="https://example.com/missing.png">', '', '', '', '', '', '']
    with pytest.raises(UnexportableImages) as error:
        build_exam_documents([question])
    assert error.value.issues[0].question_id == 21
    exam, _ = build_exam_documents([question], acknowledge_images=True)
    assert any('x' in p.text for p in exam.paragraphs)


def test_png_image_is_embedded_and_preserves_proportions():
    import base64
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QColor, QImage
    image = QImage(192, 96, QImage.Format_RGB32); image.fill(QColor('blue'))
    raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG'); buffer.close()
    src = 'data:image/png;base64,' + base64.b64encode(bytes(raw)).decode('ascii')
    q = [1, '', '', 'Dissertativa', '<p>Imagem</p><img src="' + src + '" width="192">', '', '', '', '', '', '']
    exam, _ = build_exam_documents([q], answer_placement='none')
    assert len(exam.inline_shapes) == 1
    assert abs(exam.inline_shapes[0].width.inches - 2.0) < .01
    assert abs(exam.inline_shapes[0].height.inches - 1.0) < .01


def test_acknowledged_missing_image_source_is_omitted_after_warning():
    question = [22, '', '', 'Dissertativa', '<p>Texto</p><img>', '', '', '', '', '', '']
    with pytest.raises(UnexportableImages):
        build_exam_documents([question], answer_placement='none')
    exam, _ = build_exam_documents([question], answer_placement='none', acknowledge_images=True)
    assert any('Texto' in p.text for p in exam.paragraphs)


def test_rendered_fingerprint_includes_actual_image_bytes():
    import base64
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QColor, QImage
    from prometheus.export.documents import exam_content_fingerprint
    def make_question(color):
        image = QImage(10, 10, QImage.Format_RGB32); image.fill(QColor(color))
        raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
        assert image.save(buffer, 'PNG'); buffer.close()
        src = 'data:image/png;base64,' + base64.b64encode(bytes(raw)).decode('ascii')
        return [1, '', '', 'Dissertativa', '<img src="' + src + '">', '', '', '', '', '', '']
    red, _ = build_exam_documents([make_question('red')], version_number=1, answer_placement='none')
    blue, _ = build_exam_documents([make_question('blue')], version_number=2, answer_placement='none')
    assert exam_content_fingerprint(red, version_number=1) != exam_content_fingerprint(blue, version_number=2)


def test_fingerprint_ignores_invisible_run_boundaries_labels_and_answer_keys():
    from prometheus.export.documents import exam_content_fingerprint
    def question(text, answer):
        return [1, '', '', 'Dissertativa', text, '', '', '', '', '', answer]
    first, _ = build_exam_documents([question('<p>AB</p>', 'one')], version_number=1, answer_placement='end')
    second, _ = build_exam_documents([question('<p>A<span style="color:red">B</span></p>', 'two')], version_number=2, answer_placement='none')
    assert exam_content_fingerprint(first, version_number=1) == exam_content_fingerprint(second, version_number=2)
    bold, _ = build_exam_documents([question('<p>A<b>B</b></p>', '')], version_number=3, answer_placement='none')
    assert exam_content_fingerprint(first, version_number=1) != exam_content_fingerprint(bold, version_number=3)


def test_fingerprint_distinguishes_question_order_and_image_dimensions():
    import base64
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QColor, QImage
    from prometheus.export.documents import exam_content_fingerprint
    def question(qid, text):
        return [qid, '', '', 'Dissertativa', text, '', '', '', '', '', '']
    first = question(1, 'Primeira'); second = question(2, 'Segunda')
    forward, _ = build_exam_documents([first, second], answer_placement='none')
    reverse, _ = build_exam_documents([second, first], answer_placement='none')
    assert exam_content_fingerprint(forward) != exam_content_fingerprint(reverse)
    image = QImage(192, 96, QImage.Format_RGB32); image.fill(QColor('blue'))
    raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG'); buffer.close()
    src = 'data:image/png;base64,' + base64.b64encode(bytes(raw)).decode('ascii')
    small, _ = build_exam_documents([question(1, f'<img src="{src}" width="96">')], answer_placement='none')
    large, _ = build_exam_documents([question(1, f'<img src="{src}" width="192">')], answer_placement='none')
    assert exam_content_fingerprint(small) != exam_content_fingerprint(large)


@pytest.mark.parametrize('kind', ['PNG', 'JPEG'])
@pytest.mark.parametrize(('attributes', 'expected_width', 'expected_height'), [
    ('height="48"', 1.0, .5),
    ('width="96"', 1.0, .5),
    ('width="96" height="48"', 1.0, .5),
    ('width="96" height="80"', 1.0, .5),
    ('', 2.0, 1.0),
    ('height="960"', 6.0, 3.0),
])
def test_stored_image_dimensions_are_proportional_and_capped(kind, attributes, expected_width, expected_height):
    import base64
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QColor, QImage
    image = QImage(192, 96, QImage.Format_RGB32); image.fill(QColor('blue'))
    raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, kind); buffer.close()
    src = f'data:image/{kind.lower()};base64,' + base64.b64encode(bytes(raw)).decode('ascii')
    question = [1, '', '', 'Dissertativa', f'<img src="{src}" {attributes}>', '', '', '', '', '', '']
    exam, _ = build_exam_documents([question], answer_placement='none')
    shape = exam.inline_shapes[0]
    assert shape.width.inches == pytest.approx(expected_width, abs=.01)
    assert shape.height.inches == pytest.approx(expected_height, abs=.01)
