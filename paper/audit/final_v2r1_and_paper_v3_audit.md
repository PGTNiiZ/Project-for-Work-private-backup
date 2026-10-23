# Final Independent Audit — Authoritative V2R1 and Paper V3

Date: 2026-09-05
Auditor scope: code + artifacts + manuscript, after the integrity repair and
verification rerun.

## Packages

- `experiments/icsec_final/authoritative_run_v2/` — historical pre-repair run
  (preserved unchanged; excluded as the paper's numerical source).
- `experiments/icsec_final/authoritative_run_v2r1/` — integrity-repaired
  verification rerun (seeds 101/202/303), the ONLY numerical source for the
  paper from now on.
- `paper/overleaf_v3/` — corrected manuscript source.
- `paper/final_submission_v3/ICSEC2026_anonymous_submission.pdf` — upload
  candidate (5 pages, tectonic build, anonymous).

## What was repaired (implementation)

1. Sealed-label access by construction: preflight validation now inspects
   sealed artifacts only via SHA-256, parquet footer/schema, row count, and a
   label-free pair-key read (`sealed_guard.py: sealed_artifact_metadata`).
   The ground-truth column is materialized only through the single
   final-evaluation interface; a process-wide guard over
   `pandas.read_parquet` / `pyarrow.parquet.read_table` raises on any
   pre-final materialization of a sealed `actual` column.
2. Pre-label prediction freeze: canonicalized sealed-test predictions are
   written and SHA-256 hashed into `pre_label_prediction_freeze.json`
   (hash, row count, pair-key hash, model/policy identifiers, timestamp)
   BEFORE any label access; final evaluation refuses to start without it and
   re-hashes afterwards (`prediction_immutability.json`).
3. Runtime-derived audit: `process_label_access_audit.json` per seed records
   every sealed-artifact event (phase, resource, operation, columns,
   materialized, allowed, order). No hard-coded zeros.
4. Fresh provenance: `provenance/v2r1_manifest.json` records git commit
   1e0a2db (dirty tree noted), dataset SHA, current source hashes for all
   nine scientific modules, frozen input hashes, and the recovered MiniLM
   revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (from the local HF hub
   refs; frozen feature cache retained by SHA-256, values unchanged).
5. Documentation: `PROTOCOL_V2R1.md` (lifecycle, GA arithmetic 60 × 200 =
   12,000 realized calls, true bounds incl. tr ≤ 0.90 / cd ≤ 0.60 and repair
   clips) and `FEATURE_SCHEMA_V2R1.md` (bert_cos range [-1,1]; name_sim =
   max Jaro–Winkler over the four cross-field comparisons).

Scientific behavior was NOT changed: same data, features, GB config,
sampling, calibration, policy definitions/bounds, optimizer seeds/behavior
(no GA caching added), budgets, and metric formulas. Recall remains the
frozen decision-recall definition; the manuscript now defines it explicitly.

## Verification evidence

- Preflight gate: `paper/audit/v2r1_integrity_preflight.md` — SAFE TO RERUN:
  YES (all integrity tests passed before seeds were executed).
- Rerun: one execution, seeds 101/202/303, written only to
  `authoritative_run_v2r1/` (v2 untouched; v2 SHA256SUMS re-verified intact).
- V2 vs V2R1: per-seed `summary.json` bit-identical (all 3 seeds); row-level
  workflow decision parquets (pair_key, decision, actual) identical for all
  5 methods × 3 seeds. Selected B0/B1/B2/B3 policies identical.
- Independent recomputation: `independent_metrics.json` per seed equals the
  runner summary for every method/metric (abs tol 1e-12).
- Hash manifests: per-seed `SHA256SUMS.txt` fully verified post-run (0 bad).
- Label-access audit: per-seed pre-final label-value materializations = 0;
  the first (and only) materializations occur in FINAL_EVALUATION (5 per
  seed, one per method) through `LazySealedLabelStore.read`. Pre-final
  events are footer inspections and pair-key-only reads, all with
  `label_column_materialized: false`.
- Prediction freeze: pre-label SHA == current file SHA == post-evaluation
  SHA for all 3 seeds (950,305 / 969,255 / 1,000,015 rows).
- Optimizer budgets (`optimizer_budget_transparency.json`): realized
  objective calls 12,000/12,000 (B2/B3) for every seed; unique vectors —
  B2: 12,000/12,000/12,000; B3: 8,414/8,488/8,874 (no caching added).
- Tests: 12/12 v2r1 failure-injection tests (pre-final materialization
  raises; bypass raises; missing/changed prediction hash blocks evaluation;
  pair-key change fails; stale lineage fails; duplicate-key join fails;
  unfrozen policy/model fails) + full suite 96 passed.

## Manuscript (paper/overleaf_v3) corrections applied

- Policy boundaries: "at or above t_m … below t_r", band t_r ≤ p < t_m.
- B1/B2 non-nested domains stated explicitly; B1→B2 contrast relabeled as a
  class-and-domain transition; B2→B3 remains the clean optimizer contrast.
- Decision recall defined (positive REVIEW excluded from FN denominator,
  reported in the REVIEW column; blocking misses counted as FN).
- GA disclosure: 200 evaluated populations, no deduplication, unique-vector
  counts 8,414/8,488/8,874 vs Sobol's 12,000 distinct points, equal realized
  call budget.
- Sealed-label and prediction-freeze wording now describes exactly what the
  v2r1 implementation enforces (footer/schema/pair-key-only preflight,
  single final-evaluation materialization interface, pre-label prediction
  hash gate, process-wide runtime instrumentation).
- Semantic-feature claim softened ("is consistent with" handcrafted
  dominance).
- Figure annotations corrected to raw-mean deltas (+0.0015, +0.0401);
  figures regenerated; Table II/values unchanged (v2r1 == v2).

## Final verdict

AUTHORITATIVE V2R1:
PASS

SCIENTIFIC RESULTS VS V2:
IDENTICAL

PRE-FINAL SEALED LABEL VALUE MATERIALIZATIONS:
0

TEST LABEL USED IN MODEL FITTING:
NO

TEST LABEL USED IN CALIBRATION:
NO

TEST LABEL USED IN POLICY SELECTION:
NO

PREDICTION HASHED BEFORE FINAL LABEL ACCESS:
YES

PREDICTION PRE/POST HASH MATCH:
YES

ENTITY DISJOINTNESS:
PASS

B2/B3 OBJECTIVE CALLS:
12000 / 12000

B2 UNIQUE POLICIES:
seed 101: 12000, seed 202: 12000, seed 303: 12000

B3 UNIQUE POLICIES:
seed 101: 8414, seed 202: 8488, seed 303: 8874

INDEPENDENT METRIC RECOMPUTATION:
PASS

PROVENANCE:
PASS

HASH MANIFEST:
PASS

TESTS:
PASS (96 passed, incl. 12 v2r1 failure-injection tests)

PAPER V3 NUMERICAL LINEAGE:
PASS (all table/narrative values sourced from v2r1 == v2 artifacts)

IEEE PAGE LIMIT:
PASS (5 pages)

ANONYMITY:
PASS (Anonymous Submission byline; hidelinks; no author identifiers in PDF
text or metadata)

FINAL PDF:
paper/final_submission_v3/ICSEC2026_anonymous_submission.pdf

SUBMISSION STATUS:
READY
