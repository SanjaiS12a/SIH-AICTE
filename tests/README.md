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
