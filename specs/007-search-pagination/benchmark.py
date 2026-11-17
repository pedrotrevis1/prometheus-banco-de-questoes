"""Offscreen pagination benchmark using only synthetic, in-memory banks."""
import base64
import json
import os
import platform
import sqlite3
import statistics
import tempfile
import time

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6 import __version__ as pyside_version
from PySide6.QtCore import QCoreApplication, QEvent, qVersion, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QApplication
import prometheus.app as mod
from prometheus.storage.migrations import MIGRATIONS


app = QApplication([])
benchmark_dir = tempfile.mkdtemp(prefix='prometheus-bench-config-')
mod.ExamGeneratorApp.get_data_dir = lambda self: benchmark_dir
mod.ExamGeneratorApp.show_confirm = lambda *args: False


def fail_on_alert(self, title, message, *args):
    raise RuntimeError(f'Benchmark application error ({title}): {message}')


mod.ExamGeneratorApp.show_alert = fail_on_alert
orig_query, orig_html, original_card = mod.page_questions, mod.html_fragment, mod.QuestionCard
metrics = {}


def timed_query(*args, **kwargs):
    start = time.perf_counter()
    bounds, rows = orig_query(*args, **kwargs)
    metrics['query'] += time.perf_counter() - start
    metrics['result_total'] = bounds.total
    metrics['result_ids'] = [row[0] for row in rows]
    return bounds, rows


def timed_html(*args, **kwargs):
    start = time.perf_counter()
    result = orig_html(*args, **kwargs)
    metrics['html'] += time.perf_counter() - start
    return result


class MeasuredCard(original_card):
    def __init__(self, *args, **kwargs):
        start = time.perf_counter()
        super().__init__(*args, **kwargs)
        metrics['cards'] += time.perf_counter() - start


mod.page_questions = timed_query
mod.html_fragment = timed_html
mod.QuestionCard = MeasuredCard
image = QImage(128, 128, QImage.Format_RGB32)
image.fill(QColor('blue'))
raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly)
if not image.save(buffer, 'PNG'):
    raise RuntimeError('Could not create synthetic benchmark image')
buffer.close()
png = base64.b64encode(bytes(raw)).decode()
light = '--light' in os.sys.argv
print(json.dumps({'python': platform.python_version(), 'pyside': pyside_version, 'qt': qVersion(),
                  'platform': platform.platform(), 'machine': platform.machine(),
                  'qt_platform': 'offscreen', 'image_bytes': 0 if light else len(bytes(raw))}), flush=True)

for count in (2500, 5000):
    conn = sqlite3.connect(':memory:')
    conn.create_function('CASEFOLD', 1, lambda value: str(value or '').casefold())
    for migration in MIGRATIONS:
        migration(conn)
    prompt = ('<p>Questão curta</p>' if light else '<p>' + ('Texto de exemplo para avaliação. ' * 50)
              + '</p><img src="data:image/png;base64,' + png + '">')
    alt = '<p>Alternativa</p>' if light else '<p>' + ('alternativa ' * 25) + '</p>'
    conn.executemany('''INSERT INTO questoes (id, assunto, dificuldade, tipo, enunciado, alternativa_a,
                     alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                     ((i, 'Bio', 'Fácil', 'Múltipla Escolha', prompt, alt, alt, alt, alt, alt, 'C')
                      for i in range(1, count + 1)))
    conn.commit()
    w = mod.ExamGeneratorApp(); w.conn = conn; w.tabs.setCurrentIndex(1); w.show(); app.processEvents()
    samples = []
    for idx in range(11):
        page = 1 + (idx % (count // 50))
        metrics = {'query': 0.0, 'html': 0.0, 'cards': 0.0}
        start = time.perf_counter()
        w.move_search_page(page)
        app.processEvents(); QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete); app.processEvents()
        metrics['total'] = time.perf_counter() - start
        live = w.scroll_content.findChildren(original_card)
        visible = [w.scroll_layout.itemAt(i).widget() for i in range(w.scroll_layout.count())]
        expected = list(range((page - 1) * 50 + 1, page * 50 + 1))
        if (metrics.get('result_total') != count or metrics.get('result_ids') != expected
                or len(live) != 50 or len(visible) != 50
                or [card.q_id for card in visible] != expected):
            raise AssertionError(f'Invalid page {page}: total={metrics.get("result_total")}, '
                                 f'query IDs={metrics.get("result_ids")}, live={len(live)}, visible={len(visible)}')
        metrics['live_cards'] = len(live)
        samples.append(metrics)
    summary = {'rows': count, 'prompt_chars': len(prompt), 'alternative_chars': len(alt),
               'cold_ms': {k: round(samples[0][k] * 1000, 2) for k in ('query', 'html', 'cards', 'total')},
               'warm_median_ms': {k: round(statistics.median(s[k] for s in samples[1:]) * 1000, 2)
                                  for k in ('query', 'html', 'cards', 'total')},
               'warm_max_total_ms': round(max(s['total'] for s in samples[1:]) * 1000, 2),
               'max_live_cards': max(s['live_cards'] for s in samples)}
    print(json.dumps(summary), flush=True)
    w.close(); conn.close(); w.deleteLater(); QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
