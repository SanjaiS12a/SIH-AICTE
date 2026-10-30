# Recovery and offline follow-up — 30 October 2026

This follows the completed institution frontend release `0cd0186`, not the earlier backend-only report. Phase 1 includes the directory, coordinator forms and five profile sections; the latest production build, 60 backend tests and 23 browser tests (nine dedicated institution scenarios) passed before this follow-up. No application code changed here.

## Complete database restore

Restored `backups/institution-phase1-before-20261030.dump` using PostgreSQL `pg_restore --exit-on-error` into a newly created, separate database, `coordination_phase1_restore_20261030_222220`. The restore completed successfully; this was not just an archive listing.

Assertions verified the recorded snapshot counts both before and after migrating the restored copy:

| Record | Snapshot/restored count |
|---|---:|
| Institutions | 30 |
| Cases | 7,553 |
| Case actions | 7,821 |

Ran migrations 0005–0007 against only the restored copy using a process-local `POSTGRES_DB` override. The institution version default was 1. Authenticated coordinator API checks against that database returned HTTP 200 for institution registry, profile, paginated cases and paginated history. The sampled profile/case-list totals agreed at 1,275; its history endpoint counted 1,329 actions.

The working database stayed selected for normal API/worker services. Its counts before/after the check remained **41 institutions, 7,687 cases, 7,975 actions**. The difference from the older backup is expected: later browser runs registered explicitly synthetic institutions and complaints. The recovery database is retained for inspection; the working database was not replaced, reset or rolled back.

This is a database-only backup. Private attachment files, model weights and other local assets require their own preservation; restoring database references does not restore those files. The previously recorded snapshot SHA-256 is `2c8d86e49913f3224425202716b4bf537e69edb7b4424107005bc9fc24bd8e4c`.

## Network-disabled cold model check

Started a fresh application-image container with `docker run --rm --network none`, the existing models directory mounted read-only, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and `local_files_only=True`.

- Loaded the local tokenizer with padding/truncation disabled; the sample encoded to eight wordpieces.
- Loaded the local MiniLM encoder on CPU and generated a finite, normalized 384-dimensional embedding.
- Assertions passed without any network interface beyond container loopback. No weights were downloaded and no model was trained or promoted.
- The timed tokenization/model-load/inference region took 0.67 seconds **after Python imports**. Full tool invocation took approximately 9.64 seconds, including container startup/import overhead. These are single smoke-check observations, not a throughput or p95 benchmark.

## Remaining physical-offline check

The latest browser suite blocked external requests and exercised the bundled UI. The new container check proves cold local model/tokenizer availability without a network. Neither establishes a full laptop startup/demonstration after physically disconnecting internet. That final rehearsal remains unverified, including cold database/frontend startup under that condition.

Main remains unchanged at `5fba35f`; the backend recovery checkpoint remains `dfa6e5d`. This follow-up adds verification documentation only and does not begin Phase 2.
