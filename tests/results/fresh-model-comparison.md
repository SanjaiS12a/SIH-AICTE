# Fresh comparison: original MiniLM versus project fine-tuning

Measured on 31 October 2026. **Keep the original model active.** The PAWS candidate performed worse on the new education diagnostic and on threshold-independent MRPC ranking. No retraining, activation or embedding backfill was performed.

“Original” means the published all-MiniLM-L6-v2 without this project's additional training. It is already a pretrained sentence encoder, not a randomly initialized BERT. “Fine-tuned” means our one-epoch, 79,656-pair PAWS candidate; it has not been trained on reviewed AICTE incident labels.

## Fresh data and protocol

1. **1,725 public MRPC test pairs:** 1,147 paraphrases and 578 non-paraphrases, with human news-text annotations. Download pinned to dataset revision `bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c`; SHA-256 `a623ed1cbdf445b11f8e249acbf649d7d3a5ee58c918554c40cbd8307e488693`. [Dataset card](https://huggingface.co/datasets/nyu-mll/glue) and [original Microsoft paper](https://aclanthology.org/I05-5002/). MRPC is not an education-complaint dataset. Original dataset licensing applies; raw news text is stored locally under ignored research storage and is not redistributed in Git.
2. **36 freshly authored synthetic education pairs:** 12 same-incident paraphrases, 12 distinct incidents with changed references/years, and 12 different-category issues at a fictional institution. Categories include refunds, documents, laboratory safety, scholarships, faculty, admissions, hostel water, accessibility, examinations, salaries, fees and fire safety. The fixture and labels were written before model scores were inspected. They lack independent human review.
3. Checked every sentence against **all four previous PAWS partitions** and all previous education regression records, using NFKC/casefold/whitespace normalization. **Zero overlapping pairs found; all 1,761 new pairs retained.** This check does not detect every semantic near-duplicate or establish absence from the base model's upstream pretraining. The [base model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) describes its broad prior training.
4. Reused each model's earlier frozen PAWS threshold for MRPC and its earlier frozen synthetic-domain threshold for education. No threshold search, new calibration, checkpoint selection or training was performed. The script refuses to overwrite the first saved result. Source/protocol checkpoint: `0d99e1d`; pre-change recovery checkpoint: `checkpoint/pre-fresh-comparison-54eacb1`.
5. Both models used the same CUDA environment, normalized 384-dimensional embeddings and batch size 32. Maximum inputs were 54 wordpieces for MRPC and 32 for education, below the 256-wordpiece limit. No silent truncation. Weights were checksummed before and after inference and did not change.

## Public MRPC results

| Measure | Original MiniLM | PAWS fine-tuned candidate |
|---|---:|---:|
| ROC-AUC, threshold-independent; higher is better | **0.7363** | 0.6624 |
| Average precision, threshold-independent; higher is better | **0.8369** | 0.7790 |
| Previously frozen PAWS cosine threshold | 0.9988845 | 0.9723374 |
| Precision at frozen threshold | Undefined: no positive predictions | 89.47% |
| Recall at frozen threshold | 0.00% | 5.93% |
| F1 at frozen threshold | 0.00% | 11.12% |
| Correct positive / incorrect positive predictions | 0 / 0 | 68 / 8 |
| Missed positive pairs | 1,147 | 1,079 |
| Accuracy | 33.51% | 36.99% |
| Embedding and scoring time, 3,393 unique sentences | 2.810 seconds | 2.552 seconds |

The candidate's precision exceeds 85% on this test, but it misses **94.1%** of true paraphrases at the transferred threshold. The original model predicts no paraphrases at its exceptionally strict PAWS threshold; precision is therefore undefined, although the shared metrics helper stores zero. This demonstrates poor transfer of those old operating thresholds, not that the original encoder has no useful semantic ability. ROC-AUC and average precision avoid that threshold issue and both favour the original model. Accuracy alone is misleading here because of class balance and near-all-negative predictions.

## Synthetic education incident diagnostic

| Measure | Original MiniLM | PAWS fine-tuned candidate |
|---|---:|---:|
| Previously frozen domain cosine threshold | 0.7072743 | 0.5108501 |
| Precision | **45.45%** | 25.00% |
| Recall | **83.33%** | 33.33% |
| F1 | **58.82%** | 28.57% |
| Same-incident paraphrases correctly identified | **10 / 12** | 4 / 12 |
| Distinct-reference/year incidents correctly separated | 0 / 12 | 0 / 12 |
| Different-category issues correctly separated | 12 / 12 | 12 / 12 |
| Embedding and scoring time, 36 unique sentences | 0.041 seconds | 0.041 seconds |

This is an intentionally difficult **same-incident** diagnostic. The application also suggests **related issues**, so these distinct-incident negatives may legitimately deserve human coordination review. These numbers must not be presented as application review-worthy-suggestion accuracy. They show why neither embedding similarity nor a high score should automatically confirm a duplicate incident.

Example, refund incident RF-731:

| Pair | Original cosine | Candidate cosine |
|---|---:|---:|
| Same incident, paraphrased description | 0.8131 | 0.1945 |
| Similar wording, changed incident reference and year | 0.9708 | 0.7574 |

Both rank the misleading lexical match above the true paraphrase in this example. The score is cosine similarity, not a confidence percentage.

## Performance and reproducibility

- Environment: isolated training Python, PyTorch 2.9.1+cu128, RTX 3050 A laptop GPU; two CPU threads. Application dependencies were unchanged.
- Model load time after framework imports: original 1.231 seconds, candidate 0.574 seconds. Original was loaded first; filesystem/GPU warm-up order affects these figures. These are single inference runs, not p95 benchmarks, simultaneous-user tests, full cold starts, upload timings or queue latency measurements.
- Two focused unit tests passed for overlap exclusion, authored labels and threshold/confusion-matrix accounting. The full measured run completed successfully. No application source changed, so backend/browser/build suites were not repeated for this research-only change.
- Run commands are in `tests/README.md`. All scores and metadata are in `tests/results/fresh-model-comparison.json`; all **3,522 model/pair predictions** are in `tests/results/fresh-model-predictions.csv` without MRPC text. Command log: ignored `tests/results/logs/fresh-model-comparison.log`.
- Both local model weight hashes and the team-sharing candidate package remain unchanged. The portal's baseline and its deployment threshold were not modified; the old domain comparison thresholds above are not a new deployment policy.

## Decision and limits

The fine-tuned candidate does **not** earn promotion from these results. Keep it available as an experimental artifact and keep the original active. Next useful training evidence would be independently reviewed education complaint pairs covering same incident, related issue and unrelated cases, with institution/reference/date differences and grouped held-out families. Additional epochs or a larger public paraphrase corpus alone do not establish suitability.

No new training or automatic decisions were added. This test supplies public out-of-domain and small synthetic diagnostic evidence, not real AICTE accuracy, production-scale performance or full offline verification.
