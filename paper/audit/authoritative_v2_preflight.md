# ICSEC 2026 authoritative v2 preflight

Date: 2026-09-03
Scope: integration, cache regeneration, and non-scientific preflight only. No outer model training or final test evaluation was executed.

## 1. Canonical runner command

Preflight command executed:

`uv run --with pandas --with pyarrow --with rapidfuzz --with scipy --with scikit-learn --with sentence-transformers python experiments/code/run_icsec_authoritative_v2.py --preflight`

The canonical entry point is `experiments/code/run_icsec_authoritative_v2.py`. It refuses final execution without an explicit authorization flag and the current implementation keeps final execution disabled. The final command is therefore not authorized by this report.

## 2. Files created or modified

Created:

- `experiments/code/run_icsec_authoritative_v2.py`
- `experiments/icsec_final/authoritative_run_v2/candidates/{exact_tier,model_scored,workflow}.parquet`
- `experiments/icsec_final/authoritative_run_v2/features/gb17.parquet`
- `experiments/icsec_final/authoritative_run_v2/features/bert_cos.parquet`
- `experiments/icsec_final/authoritative_run_v2/preflight/candidate_scope.json`
- `experiments/icsec_final/authoritative_run_v2/provenance/preflight_manifest.json`
- `experiments/icsec_final/authoritative_run_v2/splits/outer_{101,202,303}.json`
- `experiments/icsec_final/authoritative_run_v2/SHA256SUMS.txt`
- `tests/test_authoritative_v2_preflight.py`

Modified:

- `experiments/icsec_final/authoritative_run_v2/features.py`
- `experiments/icsec_final/authoritative_run_v2/PROTOCOL.md`
- `experiments/icsec_final/authoritative_run_v2/BASELINE_PROTOCOL.md`

Protected and unchanged:

- `experiments/icsec_final/authoritative_run/`
- `paper/overleaf/main.tex`

## 3. Feature-cache disposition and regenerated hashes

| Existing cache | Disposition | v2 replacement |
|---|---|---|
| `experiments/scored_pairs_enriched.parquet` | REGENERATE; historical only, label-bearing and confounded | v2 pair-key candidate manifests plus separate labels at final evaluation |
| `experiments/pair_features17.parquet` | REGENERATE; historical only | `features/gb17.parquet` |
| `experiments/pair_bert_cos.parquet` | REGENERATE; provenance incomplete | `features/bert_cos.parquet` |
| historical predecessor `match_decisions.parquet` | UNVERIFIABLE_HISTORICAL; absent and excluded | none |
| v1 models/probabilities/decisions | HISTORICAL ONLY | none |

SHA-256:

- `features/gb17.parquet`: `960fe07b6e46abae8502d4bc8fae6dd8a0589f5bb61d7faea9ae07534f85a057`
- `features/bert_cos.parquet`: `9c5693483020ae2a9937d979474df30ec5156e4b20632ad8a6e9866393947297`
- `candidates/exact_tier.parquet`: `92556d0574800b25ed3df72e1d84e343a1fbd08b4525ecf667600ef77aafc9cd`
- `candidates/model_scored.parquet`: `2e22d025b77f7c350239f0e1680f8d07e8cef8cb5017edc3e3ebe883bb9f2aa9`
- `candidates/workflow.parquet`: `30d168d48d8ca610ce3be5ea46bfccd124aa6676044ab68d58f56a8ef5b480b0`

## 4. Corrected name_sim production path

The v2 feature generator calls only `build_handcrafted_features` and `corrected_name_sim`. The corrected function normalizes raw username/full-name values and computes the maximum of four Jaro-Winkler comparisons. It accepts no score, decision, model, label, entity, or split argument.

An AST-based dependency check covered the runner, feature module, pipeline module, and policy module. No executable import or call to the historical experiment library, historical R2 feature builder, predecessor score path, or legacy name gate was found.

## 5. GB-17 schema validation

Passed. `gb17.parquet` contains exactly the two pair-row identifiers followed by the 17 frozen handcrafted columns in frozen order. Feature columns are `float32`; no `actual`, `label`, or `user_folder` column is present. The regenerated artifact contains 2,073,842 model-scored rows.

## 6. GB-18 schema validation

Passed at schema level. GB-18 is the exact GB-17 ordered representation plus one `bert_cos` column. The regenerated MiniLM artifact contains 2,073,842 pair-keyed rows and `float32` cosine values.

## 7. MiniLM provenance

The old cache was not trusted because its upstream model revision and generation environment were incomplete. It was regenerated with identifier `sentence-transformers/all-MiniLM-L6-v2`, normalized embeddings, and profile text `fullName + bio + location`, using `[empty]` for empty text. The output hash is recorded above and the model identifier/transformation logic are recorded in `provenance/preflight_manifest.json`.

## 8. Label-sealing verification

Synthetic runner-path preflight deliberately attempted reads during TRAIN, CALIBRATION, POLICY_VALIDATION, B0, B1, B2, and B3. All seven unauthorized reads raised `LabelAccessError`. The final-evaluation read succeeded.

Reported audit value: `PRE-FINAL TEST-LABEL READS = 7` denied attempts and zero allowed pre-final reads. No real test labels were loaded by the preflight process.

The final evaluator still requires implementation of the complete scientific execution path before this can authorize outer runs.

## 9. B0 validation

Passed in the frozen policy module. B0 is fixed at `(t_match, t_review) = (0.98, 0.95)`, with no validation tuning, optimizer, or test-label access.

## 10. B1 validation

Passed at policy-definition level. B1 uses only the two-threshold simple family and deterministic Sobol validation search. It has no `c_promote`, `c_demote`, or expanded name-based decision logic.

## 11. B2/B3 equivalence

Passed for the shared decision function and preflight search path. Both use the four-parameter genome, common bounds, common policy-validation arrays, and the same utility objective. The same genome produced identical decisions. No test labels were supplied.

## 12. Search-budget fairness

Synthetic preflight budget:

- B2 objective evaluations: 16
- B3 objective evaluations: 16
- difference: 0 / 0%

The production budget remains frozen as an execution-time measured budget. B2 must receive the realized B3 count, including duplicate candidates and initialization behavior, before any final run.

## 13. Tie-breaking rule

Frozen before final execution: strict improvement retains the first candidate in deterministic generation order. Independent GA trial ties are resolved by smallest GA seed. Test values do not participate.

## 14. Split-manifest validation

Manifests for seeds 101, 202, and 303 were generated with roles TRAIN, CALIBRATION, POLICY_VALIDATION, and SEALED_TEST. Each manifest records positive profile counts and `entity_overlap_check: passed`. No model training or final evaluation was run for these seeds.

## 15. Candidate counts

All recomputed values equal the declared current-input scope:

- eligible profiles: 36,804
- all-platform positives: 29,247
- cross-platform positives: 29,243
- same-platform positives: 4
- possible cross-platform pairs: 449,149,239
- exact-tier pairs: 12,403
- model-scored candidate pairs: 2,073,842
- workflow candidates: 2,086,245
- covered positives: 25,931
- blocking misses: 3,312
- retrieval recall: 88.6742%
- candidate-space reduction: 99.5355%

All three candidate-count invariants passed.

## 16. Provenance coverage

Preflight manifest covers Python/platform, normalized input, runner and v2 source files, frozen protocols, historical-cache classifications/hashes, regenerated candidates, corrected GB-17 cache, MiniLM cache, feature schema, and final-seed non-execution status. `SHA256SUMS.txt` records the regenerated v2 artifacts.

Final model, calibrator, policy, prediction, row-decision, and metric hashes cannot be recorded before the final scientific execution and are intentionally absent.

## 17. Tests

- Targeted repair and preflight tests: 13 passed.
- Full repository suite: 58 passed.
- Final-result inspection for seeds 101/202/303: none.

## 18. Remaining blockers

1. The canonical entry point currently performs the complete safe preflight and regeneration path but deliberately refuses final scientific execution; the GB training/calibration/policy-selection/final-evaluation writer must be wired before authorization.
2. Final execution must create sealed-test label input separately, perform final-only exact-tier/blocking-miss joins, write row-level decisions, and independently recompute metrics.
3. Final provenance closure must include models, calibrators, policies, predictions, decisions, metrics, and post-report hashes.
4. Dataset licensing, redistribution permission, collection/Terms-of-Service evidence, consent/notification, and ethics/IRB status remain unresolved.
5. No final v2 performance result or GA-specific claim exists.

V2 RUNNER WIRED:
FAIL

AFFECTED CACHES REGENERATED:
PASS

NAME_SIM PRODUCTION PATH:
PASS

TEST LABEL PHYSICAL SEAL:
PASS

B0/B1 ISOLATION:
PASS

B2/B3 POLICY EQUIVALENCE:
PASS

OPTIMIZER BUDGET FAIRNESS:
PASS

CANDIDATE SCOPE:
PASS

PROVENANCE PREFLIGHT:
PASS

TESTS:
PASS

SCIENTIFIC RESULTS INSPECTED:
NO

SAFE TO RUN AUTHORITATIVE_V2:
NO

SAFE TO WRITE PAPER V2:
NO

NEXT ACTION:
Implement and verify the final sealed-evaluation runner stages, then rerun preflight before authorizing outer seeds 101, 202, and 303.
