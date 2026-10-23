# Pre-v2 repair audit

Audit scope: implementation and protocol repair only. Historical `experiments/icsec_final/authoritative_run/` was not used as a write target, and no authoritative outer experiment was executed.

## 1. Files modified

Created the new v2 directory and components:

- `experiments/icsec_final/authoritative_run_v2/REPAIR_PROTOCOL.md`
- `experiments/icsec_final/authoritative_run_v2/PROTOCOL.md`
- `experiments/icsec_final/authoritative_run_v2/FEATURE_SCHEMA.md`
- `experiments/icsec_final/authoritative_run_v2/BASELINE_PROTOCOL.md`
- `experiments/icsec_final/authoritative_run_v2/CLAIM_PROTOCOL.md`
- `experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md`
- `experiments/icsec_final/authoritative_run_v2/__init__.py`
- `experiments/icsec_final/authoritative_run_v2/features.py`
- `experiments/icsec_final/authoritative_run_v2/label_sealing.py`
- `experiments/icsec_final/authoritative_run_v2/pipeline.py`
- `experiments/icsec_final/authoritative_run_v2/policies.py`
- `experiments/icsec_final/authoritative_run_v2/provenance.py`
- `tests/test_authoritative_v2_repair.py`
- synthetic dry-run marker and summary under `experiments/icsec_final/authoritative_run_v2/dry_run/`

No manuscript file was changed. No historical authoritative artifact was intentionally changed.

## 2. name_sim correction

The v2 implementation in `features.py` computes only the maximum of four Jaro–Winkler comparisons over normalized `userName`/`fullName` fields. Empty fields are omitted and an all-missing pair is exactly 0.0. It accepts no predecessor score, decision, model output, label, entity ID, or split. The historical gated cache and predecessor artifact are not a v2 dependency.

## 3. Feature-cache invalidation/regeneration plan

The audit-required disposition is applied in protocol, not by overwriting v1: regenerate `scored_pairs_enriched.parquet` and `pair_features17.parquet`; default to regenerating `pair_bert_cos` unless exact keys, profile hash, and pinned MiniLM revision are independently verified. Rebuild from authoritative normalized input, deterministic pair keys, corrected handcrafted features, and pinned MiniLM embeddings. Refit GB-17/GB-18 and calibration because the corrected feature input changes the model lineage. `FEATURE_SCHEMA.md` defines all 17 GB-17 columns and GB-18's exact one-column `bert_cos` addition.

## 4. Physical test-label isolation

`PublicPairData` rejects `actual`, `label`, `ground_truth`, and `user_folder` in pre-final rows. `SealedLabels` is a separate store and raises `LabelAccessError` for every phase except `final_evaluation`, recording phase/resource/allow/source in an audit log. `V2EvaluationBoundary` exposes the final join only after its phase is explicitly changed to `final_evaluation`. The required architecture and zero pre-final-read invariant are frozen in `PROTOCOL.md`; the old resident-label cache is not reused.

## 5. B0 implementation

`b0_decide` implements the fixed protocol policy: MATCH for p >= 0.98, REVIEW for 0.95 <= p < 0.98, and NO_MATCH otherwise. It performs no validation search.

## 6. B1 implementation

`b1_search` searches the same two-threshold simple family as B0 with deterministic unscrambled Sobol points, policy-validation labels only, and the declared cost objective. No name promotion or demotion rule exists in B1.

## 7. B2 implementation

`b2_sobol_search` searches the four-parameter `[t_match,t_review,c_promote,c_demote]` class with deterministic Sobol points, the same bounds, and the same objective as B3.

## 8. B3 implementation

`b3_ga_search` uses the same four-parameter decision function and bounds as B2. It uses seeded GA evolution with explicit evaluation counting. It receives only arrays supplied by the policy-validation caller; the module has no sealed-label access path.

## 9. B2/B3 budget comparison

Every objective evaluation is counted, including duplicate vectors. B3 stops at the declared budget, and B2 is called with that measured realized count. The frozen nominal legacy configuration is 60 × 40 = 12,000, but the actual count is recorded rather than assumed. The synthetic smoke test exercised 16 evaluations for each optimizer and independently reported equal realized counts.

## 10. Provenance repair

`provenance.py` provides fail-closed SHA-256 hashing and deterministic manifests. `PROTOCOL.md` requires hashes for source, transformed input, candidate manifests, corrected feature caches, MiniLM assets, splits, models, calibrators, policies, predictions, decisions, metrics, and final reports. Missing inputs raise `FileNotFoundError`; no unverifiable predecessor cache can enter v2.

## 11. Data-governance boundary

`DATA_GOVERNANCE.md` records only facts established by the root-cause audit. It makes no claim of consent, IRB approval, formal license, or redistribution permission. Raw profiles, names, usernames, biographies, URLs, images, entity IDs, pair IDs, and linkable row-level artifacts are excluded from any release until permission and ethics requirements are established. Code where permitted, configuration, hashes, non-identifying manifests, aggregates, and aggregate error categories are the safe boundary.

## 12. Tests added

`tests/test_authoritative_v2_repair.py` covers deterministic/uncensored name similarity, missing-value behavior, absence of score/label arguments, denied and allowed sealed-label phases, rejection of forbidden public fields, final-join gating, fixed B0 behavior, shared B2/B3 semantics, and equal realized optimizer budgets.

## 13. Test results

Targeted repair tests: 9 passed.
Repository suite: 54 passed in 10.99 seconds.
Compilation check for v2 modules and tests: passed.

## 14. Dry-run status

A synthetic infrastructure smoke test was executed and recorded under `authoritative_run_v2/dry_run/summary.json`, explicitly marked `NOT_MANUSCRIPT_EVIDENCE`. It exercised B0/B1/B2/B3 decision/search paths and verified equal B2/B3 budget metadata. It used no project data and was not used to tune scientific parameters.

## 15. Remaining blockers

The real v2 runner still requires execution-time wiring of the rebuilt candidate/features/model chain, pinned MiniLM asset capture, sealed-label file placement, entity-role split manifests, and final SHA-256 closure. The full outer seeds 101/202/303 have not been run. Licensing, redistribution permission, collection/ToS evidence, consent/notification, and ethics/IRB status remain unresolved. Consequently, v2 results and Paper V2 remain blocked.

NAME_SIM REPAIR:
PASS

TEST LABEL ISOLATION:
PASS

CONTROLLED BASELINES:
PASS

OPTIMIZER BUDGET FAIRNESS:
PASS

PROVENANCE READY:
PASS

TESTS:
PASS

RESEARCH DESIGN AFTER REPAIR:
VALID

SAFE TO RUN AUTHORITATIVE_V2:
NO

SAFE TO WRITE PAPER V2:
NO

NEXT ACTION:
Wire and preflight the fresh leakage-safe v2 runner and regenerate all affected caches before executing outer seeds 101, 202, and 303.
