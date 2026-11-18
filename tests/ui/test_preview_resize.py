import os
import sqlite3

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication
from prometheus.app import ExamGeneratorApp
from prometheus.storage.migrations import MIGRATIONS


@pytest.fixture
def preview_window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *a: False)
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda *a: None)
    window = ExamGeneratorApp()
    conn = sqlite3.connect(':memory:')
    conn.create_function('CASEFOLD', 1, lambda v: str(v or '').casefold())
    for migration in MIGRATIONS[:3]: migration(conn)
    conn.executemany('INSERT INTO questoes (id, assunto, tipo, enunciado) VALUES (?, ?, ?, ?)',
                     [(i, 'Bio', 'Dissertativa', '<p>' + 'conteúdo ' * 300 + '</p>') for i in range(1, 4)])
    conn.commit(); window.conn = conn
    window.load_questions(); window.resize(1250, 850); window.tabs.setCurrentIndex(1); window.show()
    for _ in range(5): app.processEvents()
    yield window
    window.close(); conn.close()


def send_mouse(handle, kind, origin, delta, button, buttons):
    local = handle.rect().center()
    event = QMouseEvent(kind, QPointF(local), QPointF(origin + QPoint(0, delta)), button, buttons, Qt.NoModifier)
    QApplication.sendEvent(handle, event)
    for _ in range(3): QApplication.processEvents()


@pytest.mark.parametrize('expanded', [False, True])
def test_large_drag_is_bounded_and_outer_geometry_stable(preview_window, expanded):
    window = preview_window
    card = window.scroll_layout.itemAt(0).widget()
    if expanded:
        card.btn_toggle.setChecked(True); card.toggle_expansion(); QApplication.processEvents()
    handle = card.resize_handle
    origin = handle.mapToGlobal(handle.rect().center())
    outer = (window.geometry(), window.scroll_area.viewport().geometry(), window.lbl_page_count.mapToGlobal(QPoint(0, 0)), window.tree_search_subjects.mapToGlobal(QPoint(0, 0)))
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    for displacement in (100, 300, 600, 1000):
        send_mouse(handle, QEvent.MouseMove, origin, displacement, Qt.NoButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 1000, Qt.LeftButton, Qt.NoButton)
    assert card.view_panel.height() <= window.scroll_area.viewport().height()
    assert (window.geometry(), window.scroll_area.viewport().geometry(), window.lbl_page_count.mapToGlobal(QPoint(0, 0)), window.tree_search_subjects.mapToGlobal(QPoint(0, 0))) == outer
    assert window.scroll_area.verticalScrollBar().value() == 0
    before = card.view_panel.height()
    send_mouse(handle, QEvent.MouseMove, origin, 1200, Qt.NoButton, Qt.NoButton)
    assert card.view_panel.height() == before


def test_manual_expanded_size_survives_reflow_and_toggle_resets(preview_window):
    window = preview_window
    card = window.scroll_layout.itemAt(0).widget()
    card.btn_toggle.setChecked(True); card.toggle_expansion(); QApplication.processEvents()
    handle = card.resize_handle; origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 60, Qt.NoButton, Qt.LeftButton)
    manual = card.view_panel.height()
    card._fit_initial_preview(); QApplication.processEvents()
    assert card.view_panel.height() == manual
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 60, Qt.LeftButton, Qt.NoButton)
    card.btn_toggle.setChecked(False); card.toggle_expansion(); QApplication.processEvents()
    assert card.view_panel.height() <= 150
    assert card.view_panel.isReadOnly()
    assert card.view_panel.verticalScrollBar().maximum() > 0


def test_shrinking_window_clamps_manual_size_without_restoring_it(preview_window):
    window = preview_window
    card = window.scroll_layout.itemAt(0).widget(); handle = card.resize_handle
    origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 1000, Qt.NoButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 1000, Qt.LeftButton, Qt.NoButton)
    initial = card.view_panel.height()
    window.resize(1250, 600)
    for _ in range(5): QApplication.processEvents()
    reduced = card.view_panel.height()
    assert reduced < initial and reduced <= window.scroll_area.viewport().height()
    window.resize(1250, 850)
    for _ in range(5): QApplication.processEvents()
    assert card.view_panel.height() == reduced


@pytest.mark.parametrize('widget_class', ['text', 'tree'])
def test_shared_non_preview_handles_keep_their_resize_behavior(qt_app, widget_class):
    from prometheus.app import ResizableTextEdit, ResizableTreeWidget
    widget = ResizableTextEdit() if widget_class == 'text' else ResizableTreeWidget()
    widget.show(); QApplication.processEvents()
    handle = widget._resize_handle; origin = handle.mapToGlobal(handle.rect().center())
    original = widget.height()
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 30, Qt.NoButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 30, Qt.LeftButton, Qt.NoButton)
    assert widget.height() == original + 30
    widget.close()


@pytest.fixture
def qt_app():
    return QApplication.instance() or QApplication([])


def test_card_reflow_moves_next_card_by_same_amount(preview_window):
    window = preview_window
    first = window.scroll_layout.itemAt(0).widget()
    second = window.scroll_layout.itemAt(1).widget()
    before_height = first.height()
    before_y = second.mapToGlobal(QPoint(0, 0)).y()
    before_text = first.view_panel.toPlainText()
    handle = first.resize_handle; origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 80, Qt.NoButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 80, Qt.LeftButton, Qt.NoButton)
    assert first.height() - before_height > 0
    assert second.mapToGlobal(QPoint(0, 0)).y() - before_y == first.height() - before_height
    assert first.view_panel.toPlainText() == before_text


def test_page_disposal_after_resizing_image_preview(preview_window):
    import base64
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QCoreApplication
    from PySide6.QtGui import QColor, QImage
    window = preview_window
    image = QImage(256, 256, QImage.Format_RGB32); image.fill(QColor('blue'))
    raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG'); buffer.close()
    embedded = base64.b64encode(bytes(raw)).decode('ascii')
    image_html = '<p>Imagem</p><img src="data:image/png;base64,' + embedded + '">'
    window.conn.execute('UPDATE questoes SET enunciado = ? WHERE id = 1', (image_html,))
    window.conn.executemany('INSERT INTO questoes (id, tipo, enunciado) VALUES (?, ?, ?)',
        [(i, 'Dissertativa', '<p>Imagem</p><img src="data:image/png;base64,' + embedded + '">') for i in range(4, 52)])
    window.conn.commit(); window.load_questions(); QApplication.processEvents()
    assert window.scroll_layout.count() == 50
    card = window.scroll_layout.itemAt(0).widget(); handle = card.resize_handle
    assert 'data:image/png;base64,' in card.view_panel.toHtml()
    origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 100, Qt.NoButton, Qt.LeftButton)
    window.move_search_page(2)
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete); QApplication.processEvents()
    assert window.scroll_layout.count() == 1
    assert window.scroll_layout.itemAt(0).widget().q_id == 51


def test_loss_of_mouse_grab_ends_drag(preview_window):
    card = preview_window.scroll_layout.itemAt(0).widget()
    handle = card.resize_handle; origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 40, Qt.NoButton, Qt.LeftButton)
    before = card.view_panel.height()
    QApplication.sendEvent(handle, QEvent(QEvent.UngrabMouse))
    send_mouse(handle, QEvent.MouseMove, origin, 100, Qt.NoButton, Qt.LeftButton)
    assert card.view_panel.height() == before


def test_short_preview_fits_without_modifying_content(preview_window):
    window = preview_window
    window.conn.execute("UPDATE questoes SET enunciado = '<p>Curto</p>' WHERE id = 1")
    window.conn.commit(); window.load_questions()
    for _ in range(3): QApplication.processEvents()
    card = window.scroll_layout.itemAt(0).widget()
    assert card.view_panel.height() <= 150
    assert card.view_panel.toPlainText().startswith('Curto\n')


@pytest.mark.parametrize('fraction', [0.5, 1.0])
def test_drag_does_not_jump_results_scroll_position(preview_window, fraction):
    window = preview_window
    bar = window.scroll_area.verticalScrollBar()
    bar.setValue(int(bar.maximum() * fraction)); QApplication.processEvents()
    before = bar.value()
    card = window.scroll_layout.itemAt(1).widget(); handle = card.resize_handle
    origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 60, Qt.NoButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 60, Qt.LeftButton, Qt.NoButton)
    assert bar.value() == before


def test_release_outside_handle_stops_drag(preview_window):
    card = preview_window.scroll_layout.itemAt(0).widget()
    handle = card.resize_handle; origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 40, Qt.NoButton, Qt.LeftButton)
    release = QMouseEvent(QEvent.MouseButtonRelease, QPointF(-500, -500),
                          QPointF(origin + QPoint(0, 500)), Qt.LeftButton, Qt.NoButton, Qt.NoModifier)
    QApplication.sendEvent(handle, release); QApplication.processEvents()
    before = card.view_panel.height()
    send_mouse(handle, QEvent.MouseMove, origin, 600, Qt.NoButton, Qt.NoButton)
    assert card.view_panel.height() == before


def test_preview_cap_accounts_for_card_controls(preview_window):
    card = preview_window.scroll_layout.itemAt(0).widget()
    handle = card.resize_handle; origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 10000, Qt.NoButton, Qt.LeftButton)
    viewport_height, chrome_height = card._preview_geometry()
    assert card.view_panel.height() <= max(60, viewport_height - chrome_height)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 10000, Qt.LeftButton, Qt.NoButton)


@pytest.mark.parametrize('expanded', [False, True])
def test_visible_preview_growth_and_shrink_reflow(preview_window, expanded):
    window = preview_window
    window.conn.execute("UPDATE questoes SET tipo='Múltipla Escolha', alternativa_a='A', alternativa_b='B', alternativa_c='C', alternativa_d='D', alternativa_e='E', gabarito='A'")
    window.conn.commit()
    window.load_questions()
    for _ in range(10): QApplication.processEvents()
    first = window.scroll_layout.itemAt(0).widget()
    second = window.scroll_layout.itemAt(1).widget()
    if expanded:
        first.btn_toggle.setChecked(True)
        first.toggle_expansion()
        for _ in range(10): QApplication.processEvents()
    handle = first.resize_handle
    origin = handle.mapToGlobal(handle.rect().center())
    viewport = first.view_panel.viewport()
    bar = window.scroll_area.verticalScrollBar()

    def geometry():
        for _ in range(10): QApplication.processEvents()
        preview = first.view_panel
        preview_top = preview.mapTo(first, QPoint(0, 0)).y()
        handle_top = handle.mapTo(first, QPoint(0, 0)).y()
        return (preview.height(), viewport.height(), first.height(), second.pos().y(),
                preview_top, handle_top, bar.value())

    before = geometry()
    viewport_height, chrome = first._preview_geometry()
    assert max(60, viewport_height - chrome) >= before[0] + 60
    text = first.view_panel.toHtml()
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    for displacement in (20, 40, 60):
        send_mouse(handle, QEvent.MouseMove, origin, displacement, Qt.NoButton, Qt.LeftButton)
    grown = geometry()
    assert grown[0] - before[0] == 60
    assert grown[1] - before[1] == 60
    assert grown[2] - before[2] == 60
    assert grown[3] - before[3] == 60
    assert grown[4] + grown[0] <= grown[5]
    assert grown[5] + handle.height() <= grown[2]
    assert grown[6] == before[6]
    send_mouse(handle, QEvent.MouseMove, origin, 0, Qt.NoButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 0, Qt.LeftButton, Qt.NoButton)
    shrunk = geometry()
    assert shrunk[:4] == before[:4]
    assert shrunk[4] + shrunk[0] <= shrunk[5]
    assert shrunk[5] + handle.height() <= shrunk[2]
    assert shrunk[6] == before[6]
    assert first.view_panel.toHtml() == text


@pytest.mark.parametrize('width', [300, 640])
def test_preview_reflow_with_both_card_header_modes(qt_app, width):
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QBoxLayout
    from prometheus.app import QuestionCard
    scroll = QScrollArea()
    content = QWidget()
    layout = QVBoxLayout(content)
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.resize(width, 900)
    cards = [QuestionCard(i, 'Biologia', 'Médio', 'Médio', 'Dissertativa',
                          '<p>' + 'conteúdo ' * 300 + '</p>', False, lambda *a: None,
                          result_viewport=scroll.viewport(), usage_count=2)
             for i in (1, 2)]
    for card in cards:
        layout.addWidget(card)
    layout.addStretch()
    scroll.show()
    for _ in range(10): qt_app.processEvents()
    first, second = cards
    assert (first.header_layout.direction() == QBoxLayout.TopToBottom) == (width == 300)
    before = first.height(), second.pos().y(), first.view_panel.height()
    handle = first.resize_handle
    origin = handle.mapToGlobal(handle.rect().center())
    send_mouse(handle, QEvent.MouseButtonPress, origin, 0, Qt.LeftButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseMove, origin, 40, Qt.NoButton, Qt.LeftButton)
    send_mouse(handle, QEvent.MouseButtonRelease, origin, 40, Qt.LeftButton, Qt.NoButton)
    for _ in range(5): qt_app.processEvents()
    assert first.view_panel.height() == before[2] + 40
    assert first.height() == before[0] + 40
    assert second.pos().y() == before[1] + 40
    scroll.close()
