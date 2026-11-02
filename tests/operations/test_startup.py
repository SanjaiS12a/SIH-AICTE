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
    def test_dependency_guard_rejects_only_this_workspace_vite_processes(self):
        script=r'''
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($env:CONTROLLER_PATH,[ref]$tokens,[ref]$errors)
$fn=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Assert-DependenciesIdle'},$true)
Invoke-Expression $fn.Extent.Text
$repoRoot='C:\SyntheticWorkspace'
function Get-CimInstance { [pscustomobject]@{CommandLine=$env:FAKE_NODE_COMMAND} }
Assert-DependenciesIdle
'''
        for command,expected in [(r'node C:\SyntheticWorkspace\frontend\node_modules\vite\bin\vite.js preview',1),(r'node C:\UnrelatedWorkspace\frontend\node_modules\vite\bin\vite.js preview',0)]:
            env=os.environ.copy();env.pop('PSModulePath',None);env.update(CONTROLLER_PATH=str(ROOT/'scripts/start.ps1'),FAKE_NODE_COMMAND=command)
            result=subprocess.run(['powershell.exe','-NoProfile','-Command',"$ErrorActionPreference='Stop';"+script],env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
    def test_demo_requires_audit_before_any_workspace_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir();shutil.copy(ROOT/'scripts/start.ps1',root/'scripts')
            result=self.invoke(root,'-Demo','-Action','Check')
            self.assertNotEqual(result.returncode,0);self.assertIn('-Demo requires -Audit',result.stderr)
            self.assertFalse((root/'.run').exists());self.assertFalse((root/'tests').exists())

    def test_demo_environment_is_restored_in_the_calling_process(self):
        script=r'''
$env:DEMO_MODE='prior-demo';$env:ENABLE_REVIEWED_FACTS='prior-facts';$env:ENABLE_INCIDENT_GROUPS='prior-groups'
& $env:CONTROLLER_PATH -Demo -Audit -Action Check
if ($env:DEMO_MODE -ne 'prior-demo' -or $env:ENABLE_REVIEWED_FACTS -ne 'prior-facts' -or $env:ENABLE_INCIDENT_GROUPS -ne 'prior-groups') { throw 'Demo overrides leaked.' }
Write-Output 'OVERRIDES_RESTORED'
'''
        env=os.environ.copy();env.pop('PSModulePath',None);env['CONTROLLER_PATH']=str(ROOT/'scripts/start.ps1')
        result=subprocess.run(['powershell.exe','-NoProfile','-Command',"$ErrorActionPreference='Stop';"+script],env=env,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('OVERRIDES_RESTORED',result.stdout)

    def test_demo_bootstrap_preserves_existing_profile_and_environment_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir();shutil.copy(ROOT/'scripts/start.ps1',root/'scripts')
            result=self.invoke(root,'-Demo','-Audit','-Action','Check');self.assertNotEqual(result.returncode,0)
            metadata=root/'tests/results/logs/readiness-run.json';before=metadata.read_bytes()
            profile=json.loads(before);self.assertTrue(profile['project'].startswith('sih-readiness-demo-'))
            self.assertTrue(Path(profile['directory']).resolve().is_relative_to(root.resolve()))
            result=self.invoke(root,'-Demo','-Audit','-Action','Check');self.assertNotEqual(result.returncode,0)
            self.assertEqual(metadata.read_bytes(),before)

    def test_demo_online_bootstrap_is_scoped_and_missing_assets_use_pinned_downloader(self):
        script=r'''
function node { $global:LASTEXITCODE=0; 'v24.0.0' }
function docker {
    [IO.File]::AppendAllText($env:DOCKER_TRACE,($args -join '|')+"`n")
    $global:LASTEXITCODE=0
    if ($args[0] -eq 'image') { $global:LASTEXITCODE=1; return }
    if ($args[0] -eq 'inspect') { return 'healthy' }
    if ($args -contains 'ps') { return 'synthetic-db' }
    if ($args -contains 'download_model') { throw 'PINNED_DOWNLOAD_REQUESTED' }
    return 'synthetic-result'
}
$env:DEMO_MODE='prior'
try { & $env:CONTROLLER_PATH -Audit -Demo -Action Prepare; throw 'Bootstrap did not reach downloader.' }
catch { if ($_.Exception.Message -notmatch 'PINNED_DOWNLOAD_REQUESTED') { throw } }
if ($env:DEMO_MODE -ne 'prior') { throw 'Environment leaked after failed preparation.' }
Write-Output 'BOOTSTRAP_SCOPED'
exit 0
'''
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir();shutil.copy(ROOT/'scripts/start.ps1',root/'scripts')
            env=os.environ.copy();env.pop('PSModulePath',None);env.update(CONTROLLER_PATH=str(root/'scripts/start.ps1'),DOCKER_TRACE=str(root/'docker.log'))
            result=subprocess.run(['powershell.exe','-NoProfile','-Command',"$ErrorActionPreference='Stop';"+script],env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            trace=(root/'docker.log').read_text(encoding='utf-8-sig')
            self.assertIn('build|-t|aicte-coordination:local',trace);self.assertIn(':/models:rw',trace)
            self.assertIn('download_model',trace);self.assertIn('HF_HUB_OFFLINE=0',trace)

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
