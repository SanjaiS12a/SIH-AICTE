# Repository organization and public-data model experiment

30 October 2026. Recovery checkpoint: `checkpoint/pre-training-091c125`. Main remains unchanged.

## Organization and environment

All test bodies and evidence are under `tests/`: `backend/`, `browser/`, `research/` and `results/`. Former `reports/` contents moved into `tests/results/`; logs, Playwright output/traces and HTML reports are in ignored subdirectories there. A small `backend/cases/tests.py` discovery shim preserves the existing Django test command. Frontend test path mapping reuses installed Playwright dependencies; no new application dependency was added. Benchmark/training output paths and Compose mounts were updated.

The existing PostgreSQL 17 + pgvector stack is retained. An ignored local `.env` was created with a generated Django secret while retaining existing database credentials. `.env.example` documents DB name/user/password and host-side address/port. Compose reads this file automatically; native Django reads process environment variables. The current volume's database password was not changed. Updating `.env` alone does not rotate an existing PostgreSQL user's password.

Git excludes `.env` variants except the example, both virtual environments, downloaded/derived raw datasets, private files, backups, model weights, large teammate bundles, run logs, traces and transient progress files. `artifacts/` contains the local model handoff, outside Git.

## Data actually acquired

| Source | Inspected/usable data | Use |
|---|---|---|
| Google PAWS-Wiki Final | 49,401 train; 8,000 official dev; 8,000 official test pairs | Human-labelled paraphrase/different-meaning experiment |
| Google PAWS-Wiki Swap-only | 30,397 auxiliary train pairs | Same publisher and label semantics |
| Cleaned public training set | **79,656 pairs**, 24,659 positives; 112 duplicate rows and 30 conflicting pair groups removed | Actual training input; no padding with invented pairs |
| Dev partition | 3,727 validation; 4,273 calibration pairs | Connected normalized-sentence groups kept together |
| CFPB Jan–Feb 2025 archive | 811,019 records inspected; 4,100 student-loan rows; **2,191 distinct non-empty narratives** retained after masking | Financial/education-language context only; no incident labels |
| CFPB August 2026 archive | 667,140 metadata rows; zero usable student-loan narratives | Recorded limitation; not counted as complaint-text training |
| Indian government tweets, Mendeley | Previously acquired/audited 3,700 annotated tweets | Complaint/unknown classes, not incident pairs; excluded from this model training |
| AICTE/DARPG | No verified open AICTE complaint-text download found; DARPG access described for registered participants | No restricted records acquired or substituted |

All PAWS files were checked against publisher-mirror SHA-256 identifiers. No normalized sentence overlaps train/evaluation, validation/calibration or dev/test partitions. Longest measured input was 86 wordpieces; no summaries were silently truncated. Official PAWS test remains unchanged. Raw/derived complaint files omit identifying metadata where possible, apply masking and remain outside Git; manual privacy review remains necessary before sharing.

Primary sources: [Google PAWS and licence](https://github.com/google-research-datasets/paws), [CFPB public complaint data](https://www.consumerfinance.gov/data-research/consumer-complaints/), [CFPB archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/), [Mendeley dataset/licence](https://data.mendeley.com/datasets/w2cp7h53s5/1), [DARPG access conditions](https://innovateindia.mygov.in/darpg-challenge-2024/). Checksums, profiles and acquisition details are in `public-pairs-audit.json`, `complaint-context-2025-audit.json`, `complaint-context-audit.json` and `source-register.json`.

## Completed GPU experiment

An isolated Windows CUDA environment uses PyTorch 2.9.1+cu128 and the project's Sentence Transformers 5.7.0 / Transformers 5.22.0 dependencies. Application PyTorch and the active portal model were not replaced. GPU operation, model forward/backward and finite loss were verified. An exploratory microbatch-8 run was discarded; final training restarted from the untouched baseline with seed 26264.

The final run used RTX 3050 A 4 GB, CUDA float16 AMP with FP32 weights, ContrastiveLoss/cosine margin 0.5, AdamW learning rate 1e-5, linear warmup/decay, effective/microbatch 32 and one predeclared epoch. All 79,656 pairs were processed in 2,490 batches. Training took **798.63 seconds (13m 19s)**; the experiment including evaluation and packaging took **887.44 seconds (14m 47s)**. Peak CUDA tensor allocation was **0.849 GiB**; this excludes driver, other applications and allocator reservation. Counts fit this particular dataset/input-length profile, not every future BERT workload.

Both operating thresholds were chosen on calibration data before the frozen official test was evaluated. No test-based checkpoint/hyperparameter adjustment was performed.

| Frozen evaluation | Baseline | Candidate |
|---|---:|---:|
| PAWS test precision | 81.13% | **83.83%** |
| PAWS test recall | 3.65% | **47.79%** |
| PAWS test F1 | 0.0698 | **0.6088** |
| Previously used synthetic education pair F1 | 0.8000 | 0.8000 |
| Synthetic education Recall@5 | 70.0% | **82.5%** |

These public F1 figures use each model's independently calibrated precision-constrained operating point. They are not accuracy percentages. Candidate public test precision falls below 85%, and synthetic retrieval falls below 90%; pair F1 did not improve on that regression. **The candidate is experimental and not approved for portal activation.** Real AICTE incident accuracy remains unvalidated. Public paraphrase labels and complaint issue/category labels were never presented as same-incident ground truth.

## Teammate handoff and checks

`artifacts/minilm-public-paraphrase-candidate.zip` (83,488,294 bytes) contains model.safetensors, tokenizer/vocabulary, architecture/pooling configuration, model revision, evaluation JSON, licences and offline CPU-loading instructions. Share the full ZIP/folder. Its SHA-256 is `ce4e232f7fa668d639c14d1aebe1c6998741d6a7f618ea63734128477a79b461`; the `.sha256` sidecar and `artifacts/MODEL_CARD.md` accompany it.

The actual ZIP was checksum-verified, safely extracted and loaded on CPU in a fresh Docker container with `--network none`. Normalized finite `(2, 384)` embeddings passed assertions. This extraction/load/inference region took 4.633 seconds after imports. Baseline weight checksum matches the earlier verified experiment; candidate weights differ. Details are in `model-package-verification.json` and `public-paraphrase-training.json`.

- **60 backend tests passed** after path/config changes (17.820s).
- **23 Playwright/Edge tests passed** from the centralized directory (3.9m).
- **Two research unit tests passed**, plus the existing parser/redaction/family-split assertion checks.
- New preparation/training/collection scripts compile. No frontend product source changed in this organization/training task; the preceding production build remains valid.

Skipped: automatic model activation, raw-data/weight publication to Git and a physical-disconnection laptop rehearsal. The existing release/backfill and independent-review gates remain necessary before any project deployment of these weights.
