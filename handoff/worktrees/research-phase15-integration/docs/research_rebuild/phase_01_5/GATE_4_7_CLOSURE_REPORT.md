# Gate 4–7 Closure Evidence Report

## Executive finding

A technical implementation closure candidate for Gates 4–7 now passes against the future A–F contracts: deterministic Feature18 assembly, hash-gated candidate snapshot split/routing, explicit pair-key adaptation, evaluator integration, and artifact-byte lifecycle. Historical embedding lineage, full historical evaluator compatibility, approved snapshot status, and production-cache compatibility remain limited exactly as noted below. Technical PASS does not close Gates 1–3, 8, or 9 and does not authorize Phase 2.

## Gate 4 — ordered features and Feature18 lineage

Authoritative V2 source: `experiments/icsec_final/authoritative_run_v2/features.py`; registry: `gate_04/FEATURE_REGISTRY.json`; schema: `experiments/icsec_final/authoritative_run_v2/FEATURE_SCHEMA.md`. The 17 ordered columns agree between source and registry. The future versioned contract adds exactly one final `bert_cos` column. New-study definitions remain E1=LR-17, E2=GB-17, E3=GB-18; no historical alias is inferred. Existing four Gate 4 tests and six new Feature18 contract tests execute successfully.

The local cache contains `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, weight file SHA-256 `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`; tokenizer bundle SHA-256 `78a3daa92dcec076e80baaa628a6553bcbd0b431a214eb02d72c8b5672e69e09` (individual file hashes in `gate_05/REAL_SNAPSHOT_VERIFICATION.json`). Cache module graph is Transformer→Pooling→Normalize; pooling config is mean-token attention-mask pooling, 384 dimensions, max length 256, followed by L2 normalization. Existing file hashes verified from bytes:

- `experiments/profile_embeddings_minilm.npy`, 56,535,680 bytes, SHA-256 `b8d5844b8f7c51fd21e390824269baa57e4564be69cf6e41a8f7f19a795981f0`.
- `experiments/profile_embeddings_minilm_ids.npy`, 294,584 bytes, SHA-256 `ceb4b0ae81b49c631594aa1ec4bd0b0ce8ec362e028967367ee7ffcba61caea5`.
- `experiments/pair_bert_cos.parquet`, 13,456,136 bytes, SHA-256 `687e93cb46b12df3ae47b26f2eeaafafcf16f6a566146e3d5198d4cefeef97b7`.
- V2 `features/gb17.parquet`, 31,869,249 bytes, SHA-256 `960fe07b6e46abae8502d4bc8fae6dd8a0589f5bb61d7faea9ae07534f85a057`.
- V2 `features/bert_cos.parquet`, 13,456,233 bytes, SHA-256 `9c5693483020ae2a9937d979474df30ec5156e4b20632ad8a6e9866393947297`.

`gate_04/FEATURE18_CONTRACT_V1.json` is an explicit future-only contract: NFKC+casefold each field, collapse whitespace, join nonempty `fullName`, `bio`, `location` with one ASCII space and use `[empty]` if all are blank; apply the pinned mean-pooling/normalization contract; pair cosine is a final float32 `bert_cos`. `feature18_contract.py` rejects revision/hash/pooling/text mismatches, non-integer or misordered profile IDs, missing pair endpoints, wrong vector dimensions and non-normalized vectors. The existing MiniLM ID array is exactly equal to candidate snapshot `profile_row_id` order (36,807 IDs); embedding shape is 36,807×384 float32 with norms 0.99999982–1.00000012. V2 Feature17 and `bert_cos` artifacts have identical ordered pair endpoints for 2,073,842 rows; the first 16 persisted cosine values match independently computed embedding dot products. These facts verify byte/schema/alignment properties but do not prove which text serialization/model revision generated the historical embedding array; no binding manifest or encoder preprocessing implementation was found. Historical E2/E3 aliases remain unresolved. No model weights were downloaded/replaced or embeddings generated.

## Gate 5 — candidate snapshot, folds and roles

Read-only V2 candidate snapshot named in `experiments/icsec_final/authoritative_run_v2/provenance/preflight_manifest.json`: `data_for_project/normalized_profiles_with_profile_id.csv`. Byte size 19,790,271; SHA-256 `17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1`; shape 36,807 × 21; platform counts Twitter 13,960 / Google+ 11,890 / Instagram 10,957; 3 rows have null `user_folder` and `profile_id`. There are 15,297 non-null entity groups; `profile_row_id` is non-null and unique for all 36,807 rows, with no row-ID-to-entity/platform conflicts; 121 rows participate in duplicate `(platform,userName)` values. The related upstream `data_for_project/merged_profiles.csv` is 36,807 × 22 with SHA-256 `a758408b8e94b9802e8522989a17aa019ba68c2e668e17bf8df6d7fe75349d05` and the same 3 null entity rows.

`gate_05/snapshot_split.py` now hash-gates before reading, enforces unique profile-row IDs and the three unmapped-row exclusion rule, re-runs fold assignment on reversed entity input to verify determinism, hashes the entity-role assignment, and routes only when both endpoints belong to the same role. The isolated report `gate_05/REAL_SNAPSHOT_VERIFICATION.json` records the candidate-only result: 36,804 eligible rows / 15,297 entities; 5-fold entity-atomic assignment; entity role counts TRAIN 6,115 / TEST 3,062 / CALIBRATION 3,061 / POLICY_VALIDATION 3,059. All 2,086,245 rows in `candidates/workflow.parquet` were checked; 604,123 same-role pairs retained and 1,482,122 cross-role pairs counted/dropped (AUTO_EXACT: 12,362 kept/41 dropped; MODEL_SCORED: 591,761 kept/1,482,081 dropped). Exact SHA, assignment digest, excluded-ID digest and role counts are in the JSON report. No raw profile/entity IDs are exported. Approval is still NOT VERIFIED; the data owner must confirm the 3 exclusions before research use.

## Gate 6 — evaluator and archived decision replay

Synthetic evaluator tests: 10/10 pass. Separately, read-only replay of archived `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B0_workflow.parquet` (historical V2 outcome; not a new final evaluation, no policy/model selection) found 194,726 rows, 3,631 AUTO_EXACT, 190,061 MODEL_SCORED, and 1,034 BLOCKING_MISS. All 194,726 hashed pair keys are unique; scopes are disjoint. Outcome codes interpreted using V2 `policies.py` (NO_MATCH=0, REVIEW=1, MATCH=2). Independently recomputed counts:

- TP=5,873; FP=32; FN=2,454 including 1,034 blocking misses; TN among candidates=185,865.
- Positive REVIEW=479; negative REVIEW=23.
- Positive denominator=8,806; automatic precision=0.9945808637; automatic recall=0.6669316375; automatic F1=0.7984501394.
- Utility `2*FP + FN + 0.1*REVIEW` = 2,568.2; candidate coverage=0.9974082564.

The V2 candidate workflow stores explicit `profile_row_id_a/b`; source `real_adapters.py` defines its pair key as SHA-256 of `v2-pair:<lower-row-id>:<higher-row-id>`. The new `gate_06/pair_adapter.py` recomputes this key and requires endpoint IDs directly or a unique explicit pair-key mapping, then verifies both endpoint entities and roles. Independent real rejoin of `B0_workflow.parquet` keys to candidate endpoints mapped all 193,692 AUTO_EXACT/MODEL_SCORED decision keys without ambiguity. The 1,034 BLOCKING_MISS rows are absent from candidate endpoint artifact; historical split-role manifest was not verified. The helper was not invoked for a historical evaluator run in this task, and no new TEST evaluation or policy/model selection occurred. This closes the future A–F adapter/evaluator contract only; historical all-scope compatibility remains partial.

Related governance evidence: `provenance/preflight_manifest.json` records 7 unauthorized attempts, 7 failures, a field named `PRE-FINAL TEST-LABEL READS: 7`, and 1 final read. Source implementations distinguish denied attempts from actual file reads. The preflight field semantics are not reconciled; historical TEST-label exposure therefore remains NOT VERIFIED. Do not claim either seven successful reads or zero successful reads without the raw audit log/source reconciliation.

## Gate 7 — manifest and cache

The single v1 schema/writer/reader/cache implementation is `gate_07/RUN_MANIFEST_SCHEMA.json` and `gate_07/run_manifest.py`. COMPLETE finalization and cache validation now require an `artifact_root`, reject paths escaping that root, and hash actual bytes for every chunk before accepting lifecycle state. The isolated test fixture contains real on-disk chunk, dataset, source, schema and pair-population bytes; it compares their actual SHA-256 values, writes/reads a manifest, and validates exact key order/coverage. Tests cover duplicate keys, missing/escaped paths, tampered bytes, incorrect digest, incomplete/partial runs and stale-cache rejection. Gate 7 suite: 24 tests passed, no failures/errors/skips. No historical or production cache was changed or tested.

Limitations: the generic helper validates artifact metadata and chunk keys; production artifacts were not verified through this helper. Resume behavior is not implemented. Any report claiming this was real-cache byte verification is incorrect.

## Test commands and environment

The previous temporary environment exists at `/tmp/phase15-integration-uv-env` and has pandas, pyarrow, rapidfuzz and scientific dependencies, but not `pytest`; attempts to invoke `python -m pytest` failed with `No module named pytest`. No dependency was installed. The tests are stdlib `unittest`, so the executable rerun used:

`/tmp/phase15-integration-uv-env/bin/python -m unittest discover -s docs/research_rebuild/phase_01_5/gate_04/tests -p 'test_*.py' -v`

`/tmp/phase15-integration-uv-env/bin/python -m unittest discover -s <suite_dir> -p 'test_*.py' -v` ran against independent suite roots, including the real candidate snapshot integration. Captured runner totals: Gate 4 = 10, Gate 5 = 10 (including 2 real-data tests), Gate 6 = 17, Gate 7 = 24 (17 manifest, 2 cross-gate, 5 byte-lifecycle); 61 run, 61 passed, 0 failures, 0 errors, 0 skips. The cross-gate test now exercises split→Feature17→synthetic Feature18 contract→pair adapter→evaluator→byte-verified manifest. It is a synthetic wiring test, not model execution or scientific evidence. `pytest` remains unavailable; no dependencies were installed. No training, GA/optimizer, new final TEST evaluation, dataset write, or historical artifact edit occurred.

## Closure decision

Technical closure status: Gate 4 PASS for the future versioned Feature18 contract; historical embedding-generation lineage remains NOT VERIFIED. Gate 5 PASS for deterministic role-safe routing against this candidate snapshot only; approval/exclusions remain unverified. Gate 6 PASS for future A–F pair adapter/evaluator interface; historical all-scope compatibility remains PARTIAL because 1,034 blocking misses and the historical role manifest are unavailable. Gate 7 PASS for isolated on-disk byte-verified manifest lifecycle; production/historical caches and resume are not verified/supported. These are technical statuses only. Gates 1–3 remain documentary NOT VERIFIED, Gate 8 remains PENDING HUMAN APPROVAL, Gate 9 remains NOT FROZEN; Phase 2 is NO-GO.
