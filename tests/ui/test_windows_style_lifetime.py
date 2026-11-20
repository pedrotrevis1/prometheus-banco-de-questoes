"""Keep native style crashes isolated from the pytest process."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows application style")
def test_successive_windows_reuse_the_application_selection_style(tmp_path):
    script = r'''
import sys
from PySide6.QtWidgets import QApplication
from prometheus.app import ExamGeneratorApp

app = QApplication([])
ExamGeneratorApp.get_data_dir = lambda self: sys.argv[1]
ExamGeneratorApp.show_confirm = lambda *args: False
first = ExamGeneratorApp()
style = QApplication.style()
first.close()
for _ in range(3):
    window = ExamGeneratorApp()
    assert QApplication.style() is style
    first.chk_include_answers.sizeHint()
    window.show()
    app.processEvents()
    window.close()
'''
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2], env=env,
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
