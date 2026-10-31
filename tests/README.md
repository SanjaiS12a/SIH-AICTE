# Tests and results

All test sources and their evidence live here:

- `backend/`: Django workflow, import, institution, permission, migration and concurrency tests.
- `browser/`: Playwright/Edge tests using the frontend's installed dependencies.
- `research/`: deterministic research parsing/split tests and model regression checks.
- `results/`: curated reports, measured metrics and screenshots.
- `results/logs/`, `results/playwright/`, `results/playwright-report/`: ignored run logs, traces and HTML output.

From the repository root:

```powershell
docker compose up -d api worker
docker compose exec api python manage.py test cases --noinput
.venv/Scripts/python -m unittest tests.research.test_public_data
.venv/Scripts/python tests/research/check_research_data.py
```

`cases/tests.py` is only a compatibility discovery entrypoint; the test bodies are in `tests/backend`. Compose mounts this folder into the API and worker. Preserve the mount when recreating containers.

From `frontend/`, with the API and bundled preview running:

```powershell
npm run build
npm run preview
# In another terminal inside frontend:
npx playwright test
```

The runner uses `tests/browser`, its own TypeScript path mapping and the result directories above. Large/raw datasets, model weights, private files and credentials do not belong in this folder or Git.

Fresh model comparison (read-only; requires the existing local PAWS audit/splits and both model directories):

```powershell
$env:PYTHONPATH='scripts;.'
.venv-training/Scripts/python -m unittest tests.research.test_fresh_comparison
.venv-training/Scripts/python scripts/compare_fresh_models.py
```

The comparison downloads a checksum-pinned MRPC test file into ignored research storage and checks it against every previous PAWS split and education regression text. It also uses `research/fresh_education_incidents.json`, a new authored diagnostic with distinct-incident negatives. It reuses frozen thresholds, never fits a model, and refuses to overwrite an existing `results/fresh-model-comparison.json`. Preserve the first run rather than tuning against its results. Prediction CSV contains IDs and scores, without MRPC text. The synthetic diagnostic is not an independent accuracy estimate or the application's related-issue review task.
