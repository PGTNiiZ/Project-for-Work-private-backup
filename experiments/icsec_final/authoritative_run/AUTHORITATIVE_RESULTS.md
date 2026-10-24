AUTHORITATIVE RESULTS — ICSEC 2026

Source: experiments/icsec_final/authoritative_run/.
All workflow metrics below are recomputed by evaluate_authoritative.py from the new row-level decision artifacts, not copied from runner summaries.

A. Dataset and candidate generation

| Quantity | Value | Local source |
|---|---:|---|
| Eligible profiles | 36,804 | candidates/candidate_scope.json |
| All-platform labeled positives | 29,247 | candidates/candidate_scope.json |
| Cross-platform labeled positives | 29,243 | candidates/candidate_scope.json |
| Same-platform positives | 4 | candidates/candidate_scope.json |
| Possible cross-platform pairs | 449,149,239 | candidates/candidate_scope.json |
| Exact-tier pairs | 12,403 | candidates/candidate_scope.json |
| Model-scored candidate pairs | 2,073,842 | candidates/candidate_scope.json |
| Workflow candidate pairs | 2,086,245 | candidates/candidate_scope.json |
| Covered cross-platform positives | 25,931 | candidates/candidate_scope.json |
| Cross-platform blocking misses | 3,312 | candidates/candidate_scope.json and candidates/blocking_missed_positives.parquet |
| Retrieval recall | 88.6742% | candidates/candidate_scope.json |
| Candidate-space reduction | 99.5355% | candidates/candidate_scope.json |

Invariant checks: exact-tier + model-scored = workflow; covered + blocking misses = cross-platform positives; all-platform = cross-platform + same-platform. All are true in candidate_scope.json.

B. Per-outer workflow results

| Seed | Method | Precision | Recall | F1 | FP | FN | REVIEW | U | Exact | Scored | Misses |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 101 | GB-17 | 0.990148 | 0.728756 | 0.839577 | 64 | 2392 | 2 | 2520.2 | 3698 | 194836 | 1025 |
| 101 | GB-18 | 0.993058 | 0.729322 | 0.840998 | 45 | 1907 | 512 | 2048.2 | 3698 | 194836 | 1025 |
| 101 | GB-18-GA | 0.990291 | 0.762746 | 0.861751 | 66 | 1534 | 902 | 1756.2 | 3698 | 194836 | 1025 |
| 202 | GB-17 | 0.996395 | 0.665215 | 0.797801 | 21 | 2223 | 720 | 2337.0 | 3670 | 178298 | 1012 |
| 202 | GB-18 | 0.995143 | 0.727908 | 0.840802 | 31 | 2374 | 0 | 2436.0 | 3670 | 178298 | 1012 |
| 202 | GB-18-GA | 0.993542 | 0.758166 | 0.860040 | 43 | 1603 | 784 | 1767.4 | 3670 | 178298 | 1012 |
| 303 | GB-17 | 0.986310 | 0.747406 | 0.850398 | 92 | 2181 | 72 | 2372.2 | 3668 | 181705 | 1031 |
| 303 | GB-18 | 0.993671 | 0.672756 | 0.802313 | 38 | 2172 | 802 | 2328.2 | 3668 | 181705 | 1031 |
| 303 | GB-18-GA | 0.982871 | 0.763532 | 0.859428 | 118 | 1537 | 1084 | 1881.4 | 3668 | 181705 | 1031 |

C. Mean ± sample SD across outer seeds

| Method | Precision | Recall | F1 | FP | FN | REVIEW | U |
|---|---:|---:|---:|---:|---:|---:|---:|
|     GB-17
Name: 0, dtype: str | 0.990951 ± 0.005090 | 0.713792 ± 0.043091 | 0.829259 ± 0.027775 | 59.000000 ± 35.763109 | 2265.333333 ± 111.688555 | 264.666667 ± 395.880453 | 2409.800000 ± 97.215637 |
|     GB-18
Name: 1, dtype: str | 0.993957 ± 0.001072 | 0.709996 ± 0.032258 | 0.828038 ± 0.022279 | 38.000000 ± 7.000000 | 2151.000000 ± 234.207173 | 438.000000 ± 406.088660 | 2270.800000 ± 200.170627 |
|     GB-18-GA
Name: 2, dtype: str | 0.988901 ± 0.005469 | 0.761481 ± 0.002898 | 0.860406 ± 0.001204 | 75.666667 ± 38.423083 | 1558.000000 ± 39.000000 | 923.333333 ± 151.133495 | 1801.666667 ± 69.277798 |

D. GA trade-offs

All comparisons are paired by outer seed and use the same row-level workflow artifacts.
- Seed 101: GA minus GB-18 F1 = +0.020753; U change = -292.0; FP change = +21; FN change = -373; REVIEW change = +390.
- Seed 202: GA minus GB-18 F1 = +0.019238; U change = -668.6; FP change = +12; FN change = -771; REVIEW change = +784.
- Seed 303: GA minus GB-18 F1 = +0.057114; U change = -446.8; FP change = +80; FN change = -635; REVIEW change = +282.

E. Scope definitions

- Exact-tier decisions are rows in exact_tier_decisions.parquet and are included in workflow metrics.
- Model-scored decisions are rows in model_scored_decisions.parquet.
- Blocking misses are rows in blocking_missed_positives.parquet and are NO_MATCH positives added to workflow FN.
- Workflow decisions are the exact, model-scored, and blocking-missed row artifacts concatenated; workflow metrics are recomputed from workflow_decisions.parquet.
- Retrieval recall is covered cross-platform positives / all cross-platform positives.

F. Failure counts

FP, FN, and REVIEW above are the complete workflow counts. Exact/model-scored/blocking row counts are included per seed and method; exact and blocking rows are identical across methods within each seed, while model-scored decisions differ by method.

G. Limitations

The package uses the current cached feature artifacts pair_features17.parquet and pair_bert_cos.parquet as declared inputs; their upstream feature-generation environment is not separately captured. The package itself captures current source hashes, current input hashes, environment, package versions, split manifests, models, calibrators, GA policies, decisions, and metric outputs. The old primary split and old bootstrap are not used.
