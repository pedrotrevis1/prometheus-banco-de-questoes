import os
import unittest

os.environ['QT_QPA_PLATFORM'] = 'offscreen'


class SmokeTest(unittest.TestCase):
    def test_import(self):
        import prometheus.app
        self.assertTrue(prometheus.app.ExamGeneratorApp)


def test_pytest_entrypoint_collects_from_repository_root():
    import os
    from pathlib import Path
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    executable = Path(sys.executable).parent / ('pytest.exe' if os.name == 'nt' else 'pytest')
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    result = subprocess.run([str(executable), '--collect-only', '-q', 'tests/domain/test_richtext.py'],
                            cwd=root, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
