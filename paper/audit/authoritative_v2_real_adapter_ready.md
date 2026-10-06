# ICSEC 2026 authoritative v2 real-adapter audit

Scope: entity/pair role routing and lazy sealed-test label adapter only. Static routing used the existing label-free real v2 artifacts. It did not train, calibrate, select policies, open real sealed labels, calculate final-method metrics, or execute seeds 101, 202, or 303.

## Real artifact schema

The inspected real artifacts have the following label-free schemas:

- `candidates/exact_tier.parquet`: `profile_row_id_a`, `profile_row_id_b`, `pair_type`; 12,403 rows.
- `candidates/model_scored.parquet`: same schema; 2,073,842 rows.
- `candidates/workflow.parquet`: same schema; 2,086,245 rows.
- `features/gb17.parquet`: the two profile-row identifiers plus the frozen 17 ordered float32 features; 2,073,842 rows.
- `features/bert_cos.parquet`: the two profile-row identifiers plus float32 `bert_cos`; 2,073,842 rows.

No inspected candidate or feature artifact had `actual`, `label`, or `ground_truth` columns.

## Entity and pair routing

`real_adapters.py` adds deterministic entity hashing, canonical SHA-256 pair keys, manifest-to-profile role assignment, same-role routing, label-free artifact validation, lazy sealed labels, and final key-safe joining.

`run_icsec_authoritative_v2.py --static-route-real-artifacts` refreshed the existing role assignments into each frozen split manifest as `entity_role_hashes`; the role algorithm and assignments were not changed. It writes local routed pair artifacts under `routing/outer_{seed}/` and the non-manuscript static report `preflight/routing_static.json`.

The router allows only same-role pairs. It rejects unknown/missing entities, conflicting role hashes, duplicate profile IDs, duplicate canonical pair keys, label columns in routing inputs, and any pair with endpoints assigned to different roles. Cross-role pairs are excluded rather than reassigned.

### Static real-artifact counts

| Seed | Scope | TRAIN | CALIBRATION | POLICY_VALIDATION | SEALED_TEST | Cross-role dropped |
|---:|---|---:|---:|---:|---:|---:|
| 101 | exact-tier | 6,018 | 1,349 | 1,363 | 3,631 | 42 |
| 101 | model-scored | 489,165 | 24,443 | 26,152 | 190,061 | 1,344,021 |
| 101 | workflow | 495,183 | 25,792 | 27,515 | 193,692 | 1,344,063 |
| 202 | exact-tier | 6,115 | 1,264 | 1,303 | 3,680 | 41 |
| 202 | model-scored | 513,112 | 20,693 | 23,164 | 193,851 | 1,323,022 |
| 202 | workflow | 519,227 | 21,957 | 24,467 | 197,531 | 1,323,063 |
| 303 | exact-tier | 6,009 | 1,292 | 1,334 | 3,728 | 40 |
| 303 | model-scored | 481,047 | 24,228 | 24,825 | 200,003 | 1,343,739 |
| 303 | workflow | 487,056 | 25,520 | 26,159 | 203,731 | 1,343,779 |

For every scope and seed, same-role count plus cross-role drops equals that scope's frozen global input count. Routing does not redefine the global candidate universe.

## Sealed-label boundary and final join

`LazySealedLabelStore` accepts only a separate Parquet artifact with exactly `pair_key` and `actual`. It does not open the file before `FINAL_EVALUATION`; every request is recorded. Pre-final requests raise before any file read.

`safe_final_join` rejects a label-bearing prediction artifact, non-64-hex safe keys, duplicate prediction keys, duplicate label keys, missing expected labels, incomplete joins, and many-to-many joins. It uses a canonical key derived from sorted profile-row IDs and therefore is independent of endpoint or label-row order. The final runner now uses this adapter when supplied `sealed_label_path`; exact-tier and blocking-missed decisions are materialized before the final keyed join.

The non-manuscript lazy-label test fixture completed through the final boundary with zero pre-final file reads. It did not use real labels or calculate scientific results.

## Candidate scope verification

The static command fail-closed if the existing global artifacts differ from these frozen counts, which were verified:

- eligible profiles: 36,804;
- all-platform positives: 29,247;
- cross-platform positives: 29,243;
- same-platform positives: 4;
- possible cross-platform pairs: 449,149,239;
- exact-tier pairs: 12,403;
- model-scored pairs: 2,073,842;
- workflow pairs: 2,086,245;
- covered positives: 25,931;
- blocking misses: 3,312;
- retrieval recall: 88.6742%; and
- candidate-space reduction: 99.5355%.

## Tests and provenance

`tests/test_authoritative_v2_real_adapters.py` adds failure coverage for unknown entities, conflicting role assignment, cross-role exclusion, pre-final label access, label-bearing prediction input, duplicate pair keys, incomplete joins, duplicate labels/many-to-many prevention, hidden label-bearing cache paths, and label-dependent routing. `tests/test_authoritative_v2_final_runner.py` adds a lazy real-label-artifact final-boundary test.

The static routing report and all routed artifacts are explicitly marked `NOT_MANUSCRIPT_EVIDENCE`. Routing manifests and artifacts remain local, non-public provenance inputs. The static-command run performed no model or policy operation.

## Remaining authorization gate

The adapters are implemented and schema-compatible, but the scientific command remains deliberately disabled until a controlled producer supplies per-seed development-label artifacts, one physically separate sealed-test label artifact, and blocking-missed pair manifests to the real final-runner CLI. This is an authorization/input-plumbing gate, not permission to execute the final seeds.
