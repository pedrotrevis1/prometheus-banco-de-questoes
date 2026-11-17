import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication, QMessageBox
from prometheus.app import ClipboardRichTextEdit


def test_pasted_local_image_survives_original_removal_and_exports(tmp_path, monkeypatch):
    from PySide6.QtGui import QColor, QImage
    from prometheus.export.documents import build_exam_documents
    app = QApplication.instance() or QApplication([])
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: warnings.append(args))
    image = QImage(192, 96, QImage.Format_RGB32); image.fill(QColor('blue'))
    path = tmp_path / 'local.png'; assert image.save(str(path))
    original = path.read_bytes()
    editor = ClipboardRichTextEdit(); mime = QMimeData()
    mime.setHtml(f'<p><img data-src="unused" src="{path.as_uri()}" width="80" height="40"></p>')
    editor.insertFromMimeData(mime)
    stored = editor.toHtml()
    assert 'data:image/png;base64,' in stored
    assert not warnings
    path.unlink()
    question = [1, '', '', 'Dissertativa', stored, '', '', '', '', '', '']
    exam, _ = build_exam_documents([question], answer_placement='none')
    output = tmp_path / 'exam.docx'; exam.save(output)
    from docx import Document
    reopened = Document(output)
    assert len(reopened.inline_shapes) == 1
    assert any(part.blob == original for part in reopened.part.related_parts.values() if hasattr(part, 'blob'))
    editor.close()


def test_remote_image_paste_warns_and_preserves_text(monkeypatch):
    app = QApplication.instance() or QApplication([])
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda parent, title, text: warnings.append((title, text)))
    editor = ClipboardRichTextEdit()
    mime = QMimeData(); mime.setHtml('<p>Conteúdo<img src="https://example.com/no.png"></p>')
    editor.insertFromMimeData(mime)
    assert 'Conteúdo' in editor.toPlainText()
    assert 'https://example.com' not in editor.toHtml()
    assert warnings and 'https://example.com/no.png' in warnings[0][1]
    editor.close()


def test_html_with_image_data_but_no_img_tag_retains_image(monkeypatch):
    from PySide6.QtGui import QImage, QColor
    app = QApplication.instance() or QApplication([])
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda parent, title, text: warnings.append(text))
    editor = ClipboardRichTextEdit(); mime = QMimeData()
    mime.setHtml('<p>Texto</p>')
    image = QImage(10, 10, QImage.Format_RGB32); image.fill(QColor('red')); mime.setImageData(image)
    editor.insertFromMimeData(mime)
    assert 'Texto' in editor.toPlainText()
    assert 'data:image/png;base64,' in editor.toHtml()
    assert not warnings
    editor.close()


def test_html_unreadable_image_uses_single_clipboard_image_when_available(monkeypatch):
    from PySide6.QtGui import QImage, QColor
    app = QApplication.instance() or QApplication([])
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda parent, title, text: warnings.append(text))
    editor = ClipboardRichTextEdit(); mime = QMimeData()
    mime.setHtml('<p>Texto<img src="file:///missing.png"></p>')
    image = QImage(10, 10, QImage.Format_RGB32); image.fill(QColor('red')); mime.setImageData(image)
    editor.insertFromMimeData(mime)
    assert 'data:image/png;base64,' in editor.toHtml()
    assert not warnings
    editor.close()
