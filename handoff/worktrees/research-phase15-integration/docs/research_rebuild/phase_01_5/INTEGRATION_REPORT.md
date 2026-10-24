# Phase 1.5 — Integration Report

## Decision

**Technical implementation closure: Gates 4–7 PASS for the new/future contracts, with historical/approval limitations described below. Phase 2: NO-GO.** The implementation is isolated and uncommitted, not a production runner or scientific authorization. Gates 1–3 remain researcher-reported approved but documentary evidence NOT VERIFIED; Gate 8 is PENDING HUMAN APPROVAL; Gate 9 is NOT FROZEN.

## New direct evidence

- Current available-environment test run: Gate 4 10/10; Gate 5 10/10 (includes 2 read-only real-data tests); Gate 6 17/17; Gate 7 24/24; total 61 run, 61 passed, 0 failed/errors/skips. Suite runner: locked Python 3.11 `unittest`; `pytest` absent in system and temporary environments, no dependencies installed. Synthetic wiring test now exercises split→Feature17→Feature18 contract→pair adapter→evaluator→manifest; all fixture labels/vectors are synthetic and no model was executed.
- `gate_05/REAL_SNAPSHOT_VERIFICATION.json` records read-only candidate snapshot SHA-256 `17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1`, 36,807×21, 3 unmapped rows excluded by explicit rule, 36,804 eligible profiles, 15,297 entities, deterministic 5-fold entity assignment with both-endpoint role routing. The V2 candidate table had 2,086,245 pairs: retained 604,123 same-role and counted/dropped 1,482,122 cross-role pairs. Snapshot remains candidate-only; no signed approval found.
- Earlier closure evidence retained a historical V2 row-level replay (194,726 rows: 3,631 exact, 190,061 scored, 1,034 misses; metrics documented in `GATE_4_7_CLOSURE_REPORT.md`). This implementation task did not rerun metrics or evaluate TEST. Recomputed join evidence maps all 193,692 exact/scored hashed keys to explicit endpoints in `candidates/workflow.parquet`; 1,034 blocking misses lack endpoint rows and the historical split-role manifest remains unverified. The new adapter is exercised only with synthetic development records in the integration test.
- Gate 7 COMPLETE lifecycle now requires a real `artifact_root`; the isolated on-disk test verifies chunk bytes, dataset/source/schema/pair-population hashes, schema compatibility, pair-key order/coverage, stale/incomplete/duplicate/path-escape/tamper rejection. No historical cache was touched and resume remains unsupported.
- Local MiniLM cache and persisted artifact alignment were verified read-only; revision, weights, tokenizer bundle hashes, shapes and ID-order results are in `gate_05/REAL_SNAPSHOT_VERIFICATION.json`. Historical embeddings still lack a binding manifest/encoder preprocessing implementation. `FEATURE18_CONTRACT_V1.json` defines a future-only exact text and pooling contract; the implementation appends one `bert_cos` column but does not execute MiniLM.

## Historical and protocol findings

Historical E2/E3 aliases remain unresolved: no pair-keyed identity mapping was found. Preserve only the new-study definitions E1=LR-17, E2=GB-17, E3=GB-18; do not back-apply these labels to historical outputs.

`EXPERIMENT_CONFIG_V1.json` proposes five folds (seed 20261010) with rotating TEST/CALIBRATION/POLICY_VALIDATION/TRAIN roles; C0 and C1 retrieval (k 10/20/50, primary 20); E1–E3 scorer definitions; P0–P5 policies; 9 cost scenarios (FN=1, FP={1,2,5}, REVIEW={0.05,0.1,0.2}); five optimizer seeds (101,202,303,404,505); and 2,048 objective calls per method/seed/fold/scenario (planned aggregate 1,382,400, not executed). Statistical contrast, interval settings, multiplicity, practical margin, cost rationale, adaptive calibration reuse, compute ceiling and several C1 decisions remain open. No training, optimization, or new final TEST evaluation occurred.

Historical preflight evidence records seven unauthorized/failed pre-final label-access attempts and one final read; the field labelled `PRE-FINAL TEST-LABEL READS` is ambiguous against the implementation's separate counters. Treat this as an instrumentation/evidence reconciliation item, not proof of seven successful reads or proof of zero successful reads. A scientific owner/auditor must resolve historical exposure before protocol freeze.

## Changed scope and worktree state

This task's implementation and report updates are in `/Users/thawaree.kha/research-phase15-integration/docs/research_rebuild/phase_01_5/`; the previously present untracked `experiments/icsec_final/authoritative_run_v2/{FEATURE_SCHEMA.md,features.py}` source copies were not changed. No primary-worktree files, dataset, historical cache, model, or lockfile were written. Primary still reports 197 Git status entries. Integration branch `research/phase15-integration-review` remains at base SHA `1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b`; no commit, merge, rebase, cherry-pick, or push. Worker branches remain separate.

## Implementation inventory and scoped closure

- Gate 4: `gate_04/feature18_contract.py`, `FEATURE18_CONTRACT_V1.json`, `test_feature18_contract.py`. Future contract pins model ID/revision/weights/tokenizer, deterministic text normalization, mean pooling + L2 normalization, exact snapshot-order IDs, 384 dimensions, and exactly one appended `bert_cos`. Does not execute the model or certify historical embedding generation.
- Gate 5: `gate_05/snapshot_split.py`, `real_snapshot_audit.py`, `test_snapshot_split.py`, `test_real_snapshot_pipeline.py`, and generated `REAL_SNAPSHOT_VERIFICATION.json`. Rechecks exact expected snapshot SHA before parsing, excludes only missing entity-map rows, verifies fold determinism and routes both endpoints by role.
- Gate 6: `gate_06/pair_adapter.py`, `test_pair_adapter.py`; Gate 7: `run_manifest.py` now requires on-disk artifact-root validation for COMPLETE, with `tests/test_artifact_bytes_lifecycle.py`. `test_cross_gate_integration.py` connects split→Feature17→synthetic Feature18→adapter→evaluator→manifest.
- Technical Gate statuses: 4 PASS for future contract (historical lineage unresolved); 5 PASS against candidate snapshot only (human approval absent); 6 PASS for future A–F adapter/evaluator contract (historical misses/roles unresolved); 7 PASS for isolated byte-verified lifecycle only (production caches/resume not verified).

## Remaining authorization and scientific blockers

Researcher/data owner: provide signed dataset/exclusion, entity-mapping and label-authority records; data owner/institution: provide reuse/privacy/ethics evidence; scientific owner: resolve Protocol A–F decisions and approve/freeze explicitly. See `HUMAN_APPROVAL_REQUEST.md`, `NEXT_ACTIONS.md` and the matrix. Until then, Phase 2 stays NO-GO.
