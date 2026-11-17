import base64, json, os, sqlite3, statistics, tempfile, time
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6 import __version__ as pyside_version
from PySide6.QtCore import QCoreApplication, QEvent, qVersion, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QApplication
import prometheus.app as mod
from prometheus.storage.migrations import migrate_0_to_1

app = QApplication([])
benchmark_dir = tempfile.mkdtemp(prefix='prometheus-bench-config-')
mod.ExamGeneratorApp.get_data_dir = lambda self: benchmark_dir
mod.ExamGeneratorApp.show_confirm = lambda *args: False
mod.ExamGeneratorApp.show_alert = lambda *args: None
orig_query, orig_html, original_card = mod.page_questions, mod.html_fragment, mod.QuestionCard
metrics = {}
def timed_query(*a, **k):
    start = time.perf_counter(); result = orig_query(*a, **k); metrics['query'] += time.perf_counter() - start; return result
def timed_html(*a, **k):
    start = time.perf_counter(); result = orig_html(*a, **k); metrics['html'] += time.perf_counter() - start; return result
class MeasuredCard(original_card):
    def __init__(self, *a, **kw):
        start=time.perf_counter(); super().__init__(*a, **kw); metrics['cards'] += time.perf_counter()-start
mod.page_questions = timed_query; mod.html_fragment = timed_html; mod.QuestionCard = MeasuredCard
image = QImage(128, 128, QImage.Format_RGB32)
image.fill(QColor('blue'))
raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly); image.save(buffer, 'PNG'); buffer.close()
png = base64.b64encode(bytes(raw)).decode()
print(json.dumps({'python': os.sys.version.split()[0], 'pyside': pyside_version, 'qt': qVersion(), 'platform':'macOS offscreen', 'image_bytes':0 if '--light' in os.sys.argv else len(base64.b64decode(png))}), flush=True)
for count in (2500, 5000):
    conn=sqlite3.connect(':memory:'); conn.create_function('CASEFOLD',1,lambda v:str(v or '').casefold()); migrate_0_to_1(conn)
    prompt = '<p>Questão curta</p>' if '--light' in os.sys.argv else '<p>' + ('Texto de exemplo para avaliação. ' * 50) + '</p><img src="data:image/png;base64,'+png+'">'
    alt = '<p>Alternativa</p>' if '--light' in os.sys.argv else '<p>' + ('alternativa ' * 25) + '</p>'
    conn.executemany('INSERT INTO questoes (id, assunto, dificuldade, tipo, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito) VALUES (?,?,?,?,?,?,?,?,?,?,?)', ((i,'Bio','Fácil','Múltipla Escolha',prompt,alt,alt,alt,alt,alt,'C') for i in range(1,count+1))); conn.commit()
    w=mod.ExamGeneratorApp(); w.conn=conn; w.tabs.setCurrentIndex(1); w.show(); app.processEvents()
    samples=[]
    for idx in range(11):
        metrics={'query':0.,'html':0.,'cards':0.}; start=time.perf_counter()
        w.move_search_page(1+(idx % (count//50))); app.processEvents(); QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete); app.processEvents()
        metrics['total']=time.perf_counter()-start
        metrics['live_cards']=len(w.scroll_content.findChildren(original_card)); samples.append(metrics)
    summary={'rows':count,'prompt_chars':len(prompt),'alternative_chars':len(alt),'cold_ms':{k:round(v*1000,2) for k,v in samples[0].items() if k!='live_cards'},'warm_median_ms':{k:round(statistics.median(s[k] for s in samples[1:])*1000,2) for k in ('query','html','cards','total')},'warm_max_total_ms':round(max(s['total'] for s in samples[1:])*1000,2),'max_live_cards':max(s['live_cards'] for s in samples)}
    print(json.dumps(summary),flush=True); w.close(); conn.close(); w.deleteLater(); QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
