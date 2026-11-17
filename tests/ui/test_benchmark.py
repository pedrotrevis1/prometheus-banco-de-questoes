import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'specs/007-search-pagination/benchmark.py'


def benchmark_env():
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['QT_QPA_PLATFORM'] = 'offscreen'
    return env


def test_light_benchmark_measures_real_cards():
    result = subprocess.run([sys.executable, str(SCRIPT), '--light'], cwd=ROOT, env=benchmark_env(),
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    assert [row['rows'] for row in records[1:]] == [2500, 5000]
    assert all(row['max_live_cards'] == 50 for row in records[1:])


def test_benchmark_propagates_search_failure():
    code = ("import runpy, prometheus.app as app\n"
            "def fail(*args, **kwargs): raise RuntimeError('synthetic query failure')\n"
            "app.page_questions = fail\n"
            f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n")
    result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=benchmark_env(),
                            capture_output=True, text=True, timeout=120)
    assert result.returncode != 0
    assert 'synthetic query failure' in result.stderr
