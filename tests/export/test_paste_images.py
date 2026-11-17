import base64
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage
from prometheus.export.images import embed_html_images


def test_paste_embeds_local_images_and_reports_unreadable_sources(tmp_path):
    image = QImage(10, 10, QImage.Format_RGB32); image.fill(QColor('red'))
    data = QByteArray(); buffer = QBuffer(data); buffer.open(QIODevice.WriteOnly); assert image.save(buffer, 'PNG'); buffer.close()
    path = tmp_path / 'sample.png'; path.write_bytes(bytes(data))
    source = f'<p>Text<img src="{path.as_uri()}"><img src="https://example.com/x.png"></p>'
    result, issues = embed_html_images(source)
    assert 'data:image/png;base64,' + base64.b64encode(bytes(data)).decode() in result
    assert 'https://example.com' not in result
    assert len(issues) == 1 and 'https://example.com/x.png' in issues[0]
    assert 'Text' in result
