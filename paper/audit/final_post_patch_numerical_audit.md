# Final Post-Patch Numerical Audit

## Verdict

FINAL POST-PATCH NUMERICAL AUDIT: **PASS**

The sole experimental source used by `paper/overleaf/main.tex` is `experiments/icsec_final/authoritative_run/`. No result from the historical primary split, historical repeated-outer summaries, old bootstrap analysis, R0–R6 family, stale sensitivity metadata, or unverifiable blocking artifact remains in the manuscript.

## Authoritative evidence chain

- Protocol: `authoritative_run/PROTOCOL.md`
- Candidate scope: `authoritative_run/candidates/candidate_scope.json`
- Per-partition metrics: `authoritative_run/raw_metrics_by_outer.csv`
- Aggregate metrics: `authoritative_run/aggregate_metrics.csv`
- Independent row-level consistency result: `authoritative_run/consistency_report.json` (`status: PASS`, nine method/partition rows)
- Label-access result: `authoritative_run/label_access_audit.json` (`test_label_requests_before_final: 0`)
- Integrity manifest: `authoritative_run/SHA256SUMS.txt`

The SHA-256 manifest was checked after the manuscript patch: all 93 listed files returned `OK`. No authoritative artifact was edited.

## Candidate and label scope

| Manuscript quantity | Authoritative value | Source field | Check |
|---|---:|---|---|
| Eligible profiles | 36,804 | `profiles_eligible` | PASS |
| Eligible Twitter / Google+ / Instagram | 13,959 / 11,889 / 10,956 | `platform_counts` | PASS |
| All-platform labeled positives | 29,247 | `all_platform_positives` | PASS |
| Cross-platform labeled positives | 29,243 | `cross_platform_positives` | PASS |
| Same-platform positives excluded | 4 | `same_platform_positives` | PASS |
| Possible cross-platform pairs | 449,149,239 | `possible_cross_platform_pairs` | PASS |
| Exact-tier pairs | 12,403 | `exact_tier_pairs` | PASS |
| Model-scored candidate pairs | 2,073,842 | `model_scored_candidate_pairs` | PASS |
| Total workflow candidates | 2,086,245 | `workflow_candidate_pairs` | PASS |
| Candidate-covered cross-platform positives | 25,931 | `candidate_covered_cross_platform_positives` | PASS |
| Cross-platform blocking misses | 3,312 | `cross_platform_blocking_misses` | PASS |
| Retrieval recall | 88.6742% | `retrieval_recall` | PASS |
| Candidate-space reduction | 99.5355% | `candidate_space_reduction` | PASS |

Recomputed invariants:

- 12,403 + 2,073,842 = 2,086,245.
- 25,931 + 3,312 = 29,243.
- 29,243 + 4 = 29,247.
- The manuscript explicitly uses 29,243, not 29,247, as the cross-platform retrieval denominator.

## Model, calibration, policy, and split constants

All implementation constants in the manuscript agree with `PROTOCOL.md`:

- GB-17: the authoritative 17-feature list.
- GB-18: GB-17 plus `bert_cos` only.
- Gradient Boosting: 300 estimators, learning rate 0.05, maximum depth 6, random state 42.
- Deterministic training ratio: three negatives per positive.
- Calibration: isotonic regression with clipped out-of-range values on calibration entities only.
- Fixed thresholds: MATCH at 0.98; REVIEW from 0.95 to below 0.98.
- Genome: `[t_match, t_review, c_promote, c_demote]` with the frozen constraints.
- GA: population 60, 40 generations, 12 elites, uniform crossover, mutation probability 0.30, Gaussian sigma 0.02, seeds 7/42/123/999/2025.
- Decision objective: `U = 2*FP + FN + 0.1*REVIEW`; described only as illustrative operational utility / a declared scenario-specific decision objective.
- Outer seeds: 101, 202, and 303; 30% sealed test; remaining development entities assigned 70%/15%/15% to training/calibration/GA validation.
- Cross-role pairs are dropped; entity overlap is zero; test-label requests before final evaluation are zero.

## Aggregate result table

Values below are the exact manuscript rounding of `aggregate_metrics.csv`.

| Method | Precision | Recall | F1 | FP | FN | REVIEW | U |
|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 0.9910 ± 0.0051 | 0.7138 ± 0.0431 | 0.8293 ± 0.0278 | 59.0 ± 35.8 | 2265.3 ± 111.7 | 264.7 ± 395.9 | 2409.8 ± 97.2 |
| GB-18 | 0.9940 ± 0.0011 | 0.7100 ± 0.0323 | 0.8280 ± 0.0223 | 38.0 ± 7.0 | 2151.0 ± 234.2 | 438.0 ± 406.1 | 2270.8 ± 200.2 |
| GB-18-GA | 0.9889 ± 0.0055 | 0.7615 ± 0.0029 | 0.8604 ± 0.0012 | 75.7 ± 38.4 | 1558.0 ± 39.0 | 923.3 ± 151.1 | 1801.7 ± 69.3 |

All 42 rounded cells (seven metrics × mean/SD × three methods) were checked programmatically against the authoritative CSV.

## Per-partition table

The paper reports authoritative F1 values rounded to four decimals:

| Seed | GB-17 | GB-18 | GB-18-GA |
|---:|---:|---:|---:|
| 101 | 0.8396 | 0.8410 | 0.8618 |
| 202 | 0.7978 | 0.8408 | 0.8600 |
| 303 | 0.8504 | 0.8023 | 0.8594 |

Each value was checked against `raw_metrics_by_outer.csv`.

## Derived narrative comparisons

Derived directly from authoritative rows/aggregates:

- GA minus GB-18 F1 by seed: +0.0208, +0.0192, and +0.0571 after manuscript rounding.
- Mean recall change: +0.051486 (0.7100 to 0.7615 in manuscript).
- Mean F1 change: +0.032368.
- Mean FP change: +37.667.
- Mean FN change: -593.0.
- Mean REVIEW change: +485.333.
- Mean U change: -469.133 (reported as a 469.1 decrease).

The manuscript presents these as an operating trade-off and makes no claim of universal superiority, statistical significance, optimization of measured business cost, or improved blocking.

## Historical-evidence exclusion

A source scan confirmed removal of:

- Historical primary role counts and primary-split performance.
- Historical conditional-bootstrap intervals and claims.
- Historical failure/missingness counts and platform-pair metrics.
- Historical sensitivity results and 5/1/0.02 metadata.
- Historical repeated-outer means, SDs, FN values, utilities, and per-seed values that differ from the authoritative package.
- Unverifiable historical blocking constants.

The manuscript contains no references to a “primary split” or “frozen primary” evidence family. Outer-partition variation is the only uncertainty summary.

## Citation, formatting, and test checks

- Abstract length: 228 words.
- Bibliography closure: 16 citation keys; every cited key exists and every bibliography entry is cited.
- Main tables use the IEEEtran body font; local `small`/`footnotesize` table reductions were removed.
- Full automated suite: 45 tests passed.
- Final PDF: 5 pages; compiled twice with no undefined citations, undefined references, or overfull boxes.
- Three underfull-box warnings remain cosmetic and produced no visible gaps or overlap.
- All PDF font resources are embedded; all five pages were rendered and visually inspected.
- PDF metadata author is `Anonymous`, and the extracted-text/source anonymity scans found no author identity, affiliation, acknowledgement, local path, machine username, or author-controlled URL.
