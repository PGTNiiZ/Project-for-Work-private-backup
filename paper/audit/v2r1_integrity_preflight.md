# V2R1 Integrity Preflight — Gate Before Final Verification Rerun

Date: 2026-09-05
Package under test: experiments/icsec_final/authoritative_run_v2r1/
Historical package: experiments/icsec_final/authoritative_run_v2/ (preserved, untouched)

## Repairs under test
1. Label-free preflight validation (`validate_input_artifacts_label_free`):
   SHA-256, parquet footer schema, row count, pair-key-only reads. The sealed
   `actual` column is never materialized pre-final.
2. Process-wide `SealedLabelGuard` (patches pandas.read_parquet and
   pyarrow.parquet.read_table): any pre-final materialization of a registered
   sealed artifact's label column raises `SealedLabelViolation`. Audit counts
   are derived from runtime events, never hard-coded.
3. Pre-label prediction freeze: canonicalized predictions are SHA-256 hashed
   into `pre_label_prediction_freeze.json` BEFORE label access;
   FINAL_EVALUATION refuses without it and re-verifies pre/post hashes.

## Evidence
- Failure-injection suite `tests/test_v2r1_integrity.py`: 12/12 passed
  (pre-final materialization raises; column-request bypass raises; label-free
  inspection allowed; missing freeze manifest blocks final evaluation;
  prediction tamper detected; pair-key tamper detected; unfrozen policy
  rejected; stale lineage hash rejected; duplicate final join keys rejected;
  audit counts derived, not hard-coded; full synthetic run passes with
  0 pre-final materializations and freeze manifest inside SHA256SUMS).
- Full repository suite: 96/96 passed (13.08s), `-p no:cacheprovider`.
- Real-input gate (`validate_gate`, seeds 101/202/303) executed under the
  installed guard: PASS with 0 pre-final label materializations and
  6 audited non-materializing sealed accesses (footer + pair-key per seed).
- Frozen protocol hashes (v2 `frozen_protocol_hashes.json`): all match.
- v2 frozen inputs (candidates, features, routing, splits, scientific_inputs)
  are consumed verbatim; per-artifact SHA-256 verified against v2 manifests.
- MiniLM revision recovered from local HF hub refs/main:
  1110a243fdf4706b3f48f1d95db1a4f5529b4d41; frozen bert_cos cache SHA-256
  9c5693483020ae2a9937d979474df30ec5156e4b20632ad8a6e9866393947297 retained,
  NOT regenerated.

## Checklist
SEALED LABEL VALUE ACCESS:            PASS
PRE-FINAL LABEL VALUE MATERIALIZATIONS: 0
PREDICTIONS HASHED BEFORE LABEL ACCESS: PASS
PREDICTION IMMUTABILITY:              PASS (pre/post SHA verified in tests)
ENTITY DISJOINTNESS:                  PASS (validate_roles; zero overlap all role pairs)
B2/B3 POLICY EQUIVALENCE:             PASS (same class, bounds, objective, decide_four_parameter)
B2/B3 OBJECTIVE-CALL BUDGET:          12000 / 12000
PROVENANCE:                           PASS (fresh v2r1 manifest from current sources; no stale v2 hashes)
TESTS:                                PASS (96/96 repository-wide; 12/12 integrity)

SAFE TO RERUN:
YES
