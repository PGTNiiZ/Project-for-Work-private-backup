# ICSEC 2026 authoritative v2 final-runner audit

Status: implementation and synthetic verification only. No authoritative outer seed was executed, and no final scientific result was opened or inspected.

## 1. Canonical commands

Non-manuscript complete-path verification executed:

`uv run python3.11 experiments/code/run_icsec_authoritative_v2.py --synthetic-final`

This produced `experiments/icsec_final/authoritative_run_v2/dry_run/final_runner_synthetic/`, marked `NOT_MANUSCRIPT_EVIDENCE: true`.

The scientific invocation remains explicitly blocked by the command-line gate because the repository does not yet provide the required sealed-label artifact and role-pair manifest adapter:

`uv run python3.11 experiments/code/run_icsec_authoritative_v2.py --execute-final --outer-seeds 101 202 303`

It was not executed.

## 2. Final optimizer budget determination

The preflight value 16 is a synthetic dry-run budget only. The frozen final budget is 12,000 objective evaluations per outer split: the nominal GA configuration is population 60 x 40 generations. B3 records every realized evaluation, including duplicates, and B2 must receive that same realized count. The implementation defines `FINAL_BUDGET = 12000`; synthetic verification deliberately used 16 and is not evidence.

Sources: `BASELINE_PROTOCOL.md:3-16`, `REPAIR_PROTOCOL.md:25-27`, and `major_revision_root_cause.md:131-137`.

## 3. Implemented final stages

`final_runner.py` provides a complete, fail-closed execution sequence for one supplied outer split:

1. Validates the corrected 17-column GB-17 schema, exact GB-18 plus `bert_cos` schema, pair uniqueness, role names, and legacy name-sim marker.
2. Asserts all six entity-role intersections are empty and rejects cross-role/unassigned pair rows.
3. Trains GB-17 and GB-18 using TRAIN rows only, fixed `GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42)`, and records model/config/schema/entity/source hashes.
4. Fits an independent `IsotonicRegression(out_of_bounds='clip')` calibrator for each model with CALIBRATION labels only.
5. Generates policy-validation GB-18 calibrated scores; B0 is fixed, B1 is simple-threshold Sobol, B2 is four-parameter Sobol, and B3 is seeded four-parameter GA.
6. Records B2/B3 class, bounds, shared decision implementation, validation-data hash, objective, and equal realized budget in `fairness.json`; any mismatch fails closed.
7. Hashes models, calibrators, policies, training metadata, and fairness report in `pre_test_freeze.json`; detects both file and in-memory policy changes before sealed prediction.
8. Writes only pair key, model/policy identifier, calibrated probability, and decision in `sealed_predictions/predictions.parquet` before labels are opened.
9. Makes the final label join only in `final_evaluation`, writes label-access audit, and emits separate model-scored and workflow decision rows per B0/B1/B2/B3.
10. Recomputes TP, FP, FN, REVIEW, precision, recall, F1, and U independently from frozen workflow row artifacts and fails on exact mismatch.
11. Hashes all completed outputs into `SHA256SUMS.txt`, excluding that manifest itself, and verifies it.

## 4. Synthetic execution verification

The complete non-manuscript path passed training, calibration, policy selection, pre-test freeze, sealed prediction, final label join, workflow evaluation, independent recomputation, provenance capture, and manifest verification. It reported zero permitted pre-final sealed-label reads. No project candidate/features data and no final seed were used.

## 5. Failure-injection coverage

`tests/test_authoritative_v2_final_runner.py` adds 13 tests, including rejection of:

- pre-final test-label reads;
- overlapping split entities;
- legacy `name_sim` paths;
- wrong GB-17 schema;
- unexpected GB-18 features;
- B2/B3 policy-class unfairness;
- invalid policy budget;
- post-freeze policy mutation;
- tampered row-level decisions causing independent-metric mismatch;
- missing provenance input; and
- tampered final artifact hash.

## 6. Test results

- v2 repair, preflight, and final-runner tests: 26 passed in 2.10 s.
- Full repository suite: 71 passed in 10.88 s.
- Python compilation of the v2 entry point, final runner, and sealing module: passed.

## 7. Remaining blocker

The generic final-runner engine is verified, but the canonical scientific CLI has no safe adapter from the existing regenerated pair/features artifacts to per-seed role-pair manifests plus a separately supplied, lazy-opened sealed-label artifact. The existing `outer_{101,202,303}.json` files contain only aggregate hashed entity manifests, not the pair-to-role assignments required to run the real artifacts without rebuilding or exposing labels. Therefore the engine must not be authorized for authoritative seeds until that adapter and its non-manuscript integration test exist.

No paper file, historical `authoritative_run/` artifact, final seed, or scientific metric was touched.
