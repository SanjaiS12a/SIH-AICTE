"""Controller failures must be nonzero, before starting or stopping services."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StartupTests(unittest.TestCase):
    def invoke(self, root, *args):
        env = os.environ.copy()
        env.pop('PSModulePath', None)
        return subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-File', str(root / 'scripts/start.ps1'), *args], capture_output=True, text=True, timeout=60, env=env)

    def test_prepared_audit_assets(self):
        result = self.invoke(ROOT, '-Action', 'Check', '-Audit')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unowned_pid_is_not_stopped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / '.run').mkdir()
            shutil.copy(ROOT / 'scripts/start.ps1', root / 'scripts')
            (root / '.run/frontend-5173.json').write_text(json.dumps({'pid': os.getpid(), 'created': '0'}))
            result = self.invoke(root, '-Action', 'Stop')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('refusing to stop', result.stderr)

    def test_corrupt_weights_fail_before_service_start(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['scripts/start.ps1', 'backend/model-manifest.json', 'backend/calibration.json',
                         'backend/licenses/minilm-LICENSE.txt', 'models/minilm/revision.json',
                         'models/minilm/tokenizer.json', 'models/minilm/config.json', 'models/minilm/1_Pooling/config.json']:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / name, target)
            (root / 'models/minilm/model.safetensors').write_bytes(b'corrupt')
            result = self.invoke(root, '-Action', 'Check')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('checksum mismatch', result.stderr)


if __name__ == '__main__':
    unittest.main()
