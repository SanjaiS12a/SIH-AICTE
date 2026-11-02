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
    def test_physical_offline_guard_rejects_up_adapters_without_changing_network(self):
        script=r'''
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($env:OFFLINE_SCRIPT,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Offline script parse failed.' }
$function=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Disconnected-Adapters'},$true)
Invoke-Expression $function.Extent.Text
function Get-NetAdapter { [pscustomobject]@{Name='Synthetic';Status=$env:ADAPTER_STATE;InterfaceDescription='Test only'} }
Disconnected-Adapters
'''
        for state,expected in [('Up',1),('Disconnected',0)]:
            env=os.environ.copy();env.pop('PSModulePath',None)
            env.update(OFFLINE_SCRIPT=str(ROOT/'scripts/verify-physical-offline.ps1'),ADAPTER_STATE=state)
            result=subprocess.run(['powershell.exe','-NoProfile','-Command',"$ErrorActionPreference='Stop';"+script],env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,expected,result.stdout+result.stderr)

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

    def test_worker_readiness_requires_running_container_and_current_cluster_logs(self):
        script = r'''
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($env:CONTROLLER_PATH,[ref]$tokens,[ref]$errors)
$function=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Wait-Worker'},$true)
Invoke-Expression $function.Extent.Text
$composeArgs=@('compose')
function docker {
    $global:LASTEXITCODE=0
    if ($args[0] -eq 'inspect') { return ('{"Running":'+$env:WORKER_RUNNING+',"StartedAt":"2026-11-01T00:00:00Z"}') }
    if ($args[0] -eq 'logs') { return 'ready for work; Q Cluster synthetic-test [coordination] running.' }
    return 'workspace-worker'
}
Wait-Worker
'''
        for running, expected in [('true',0),('false',1)]:
            env=os.environ.copy();env.pop('PSModulePath',None)
            env.update(CONTROLLER_PATH=str(ROOT/'scripts/start.ps1'),WORKER_RUNNING=running)
            result=subprocess.run(['powershell.exe','-NoProfile','-Command',"$ErrorActionPreference='Stop';"+script],env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
            if running=='false':self.assertIn('Worker exited before becoming ready',result.stderr)


if __name__ == '__main__':
    unittest.main()
