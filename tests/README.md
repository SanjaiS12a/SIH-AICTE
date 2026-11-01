# Tests and results

All verification sources and selected evidence live here.

- `backend/`: Django workflow, permission, migration, import and concurrency tests.
- `browser/`: Playwright/Edge regressions and the supplied-workbook walkthrough.
- `operations/`: Windows controller safety checks.
- `performance/`: frozen-model encoder and reminder measurements.
- `fixtures/`: fictional, repeatable demonstration inputs.
- `results/`: curated verification reports; `results/runs/` and `results/logs/` are ignored per-run evidence.

Use the separate audit stack in [the project README](../README.md). Browser verification defaults to port 5174 and rejects working-demo ports 5173 and 8000. Do not use the working application's private storage for verification.

```powershell
# With the audit stack already prepared and running:
$run = Get-Content tests/results/logs/readiness-run.json | ConvertFrom-Json
$env:AUDIT_RESULTS = $run.directory
docker compose -p $run.project -f compose.audit.yaml exec -T api python manage.py test cases --noinput
.venv/Scripts/python.exe -m unittest discover -s tests/operations -v
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5174'
$env:AUDIT_ARTIFACT_DIR = Join-Path $run.directory ('browser-' + (Get-Date -Format yyyyMMdd-HHmmss))
Push-Location frontend
npx playwright test
Pop-Location
```

`backend/cases/tests.py` retains Django's existing discovery entry point. Its test bodies remain in `tests/backend`. A discovered count is not a passing result.

Start with [the six-case workbook](fixtures/sih-walkthrough/start-here-6-cases.xlsx) and [START-HERE](../START-HERE.md). The [readiness report](results/readiness-verification.md) distinguishes current checks, diagnostic performance runs and unresolved gates. Historical research evidence does not establish real-world AICTE accuracy. This release cycle does not train or activate an experimental model.

Keep credentials, private uploads, database archives, downloaded datasets and weights out of Git. Physical-offline verification requires actual network disconnection; intercepted requests alone are not equivalent.

The [Case Intelligence Milestone A report](results/case-intelligence-a-verification.md) records the navigation/comparison changes, dedicated browser coverage and before/after desktop/mobile screenshots. Later intelligence and protocol milestones remain separate.
