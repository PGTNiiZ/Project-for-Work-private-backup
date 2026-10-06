# ICSEC 2026 V2 final evidence audit

## Verdict

The authoritative V2 evidence passes numerical, isolation, fairness, scope, provenance, hash, and test gates. Only `experiments/icsec_final/authoritative_run_v2/` is authoritative; V1 is excluded.

## Numerical consistency

For every seed (101, 202, 303) and method (GB17_B0, B0, B1, B2, B3), TP, FP, FN, REVIEW, precision, recall, F1, and `U = 2*FP + FN + 0.1*REVIEW` were recomputed from frozen WORKFLOW Parquet rows. Recomputed dictionaries match both `summary.json` and `independent_metrics.json` exactly.

## Test-label isolation

All three executions report `PRE-FINAL TEST LABEL READS = 0`. Each recorded label access has phase `FINAL_EVALUATION` and `allowed = true`. Sealed predictions were written and included in the pre-evaluation freeze before the lazy keyed label join.

## B2/B3 fairness

For every seed, B2 and B3 use the same expanded four-parameter policy class, bounds, validation data, decision implementation, and objective. Each realized exactly 12,000 objective evaluations. Fairness reports pass for all seeds.

## Entity disjointness

Frozen split manifests contain TRAIN, CALIBRATION, POLICY_VALIDATION, and SEALED_TEST roles with passed overlap assertions. Routed pairs are same-role only; cross-role pairs remain excluded rather than reassigned.

## Workflow scope

Each workflow decision artifact is uniquely keyed and decomposes into AUTO_EXACT, MODEL_SCORED, and BLOCKING_MISS rows. Blocking misses are positive NO_MATCH rows and therefore contribute to workflow FN and recall without being scored by either classifier. Global scope remains 36,804 eligible profiles, 29,243 cross-platform positives, 25,931 candidate-covered positives, and 3,312 blocking misses.

## Controlled findings

GB-18+B0 versus GB-17+B0 changes only the semantic cosine feature. Mean workflow F1 changes from 0.8494 to 0.8510, while the variation across seeds is larger than this difference; no substantive semantic-feature benefit is supported.

B0 to B1 isolates validation tuning in the simple policy class. Mean F1 rises from 0.8510 to 0.8910 and mean U falls from 2364.2 to 1864.6, with higher recall and review volume and a modest FP increase.

B1 to B2 changes to the expanded policy under Sobol search. Mean U falls slightly (1864.6 to 1860.0), but mean F1 and recall decline slightly while review volume rises. This is a small operating-trade-off change, not a broad accuracy gain.

B2 to B3 isolates optimizer choice. Mean results are nearly identical: F1 0.8901 versus 0.8903 and U 1860.0 versus 1858.2. B3 improves U in seed 101, ties in seed 202, and is 0.1 worse in seed 303. A clear, consistent GA-specific benefit is not supported. The paper story must center validation-selected three-way decision policies, not GA superiority.

## Provenance and hashes

Per-seed source/model/calibrator/policy/prediction/decision/metric artifacts are covered by verified per-seed manifests. `final_evidence.json`, `FINAL_RESULTS.md`, and the final root `SHA256SUMS.txt` were generated after independent recomputation. The root manifest excludes itself and was verified.

## Tests

Final test result is recorded in `paper/audit/final_paper_v2_report.md` after manuscript packaging.

NUMERICAL CONSISTENCY: PASS

TEST LABEL ISOLATION: PASS

B2/B3 FAIRNESS: PASS

ENTITY DISJOINTNESS: PASS

WORKFLOW SCOPE: PASS

PROVENANCE: PASS

HASH VERIFICATION: PASS
