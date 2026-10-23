FINAL EVIDENCE RECONCILIATION AUDIT
ICSEC 2026 — numerical evidence only

Audit date: 2026-09-03
Protected manuscript paths were not edited: paper/overleaf/main.tex, paper/overleaf/references.bib, paper/overleaf/figures/.

Executive disposition

EVIDENCE RECONCILIATION: FAIL
SAFE TO PROCEED TO INDEPENDENT REVIEW: NO

The retrieval counts and the repeated-outer numerical summaries are reproducible within their stated scopes. The primary frozen workflow metrics are not reproducible from one complete, pair-key-aligned evidence chain. The sealed decision file is pair-key aligned with the persisted probability files and is therefore authoritative for model-scored-candidate-only decisions, but it does not reproduce the workflow summary because the exact-tier and blocking constants used by the summary are from a conflicting result family. The blocking-miss row artifact referenced by the run is absent.

A. Artifact lineage

Lineage table (timestamps are filesystem modification timestamps in UTC; a creation timestamp is not separately recorded unless shown in the artifact).

| Artifact/family | Timestamp | Generator/source | Input/source hashes | Split/model/calibration/policy | Scope | Status |
|---|---|---|---|---|---|---|
| experiments/scored_pairs_enriched.parquet | 2026-08-10 07:13:07 | experiments/code/exp_lib.py build_cache; source hash 984adb9c... | SHA-256 396884be...; profiles SHA-256 17a95f75... in primary manifest | Historical cache; labels from user_folder; AUTO_EXACT retained | 2,086,245 workflow pairs | AUTHORITATIVE for candidate-workflow scope |
| experiments/pair_features17.parquet | 2026-08-10 07:13:06 | feature-generation path; exact generator run metadata not persisted | SHA-256 215d2a1e... | 17-feature cached frame | 2,073,842 model-scored rows | AUTHORITATIVE input cache, incomplete generator provenance |
| experiments/pair_bert_cos.parquet | 2026-08-10 07:13:06 | MiniLM feature-generation path; exact generator run metadata not persisted | SHA-256 687e93cb... | bert_cos feature cache | 2,073,842 model-scored rows | AUTHORITATIVE input cache, incomplete generator provenance |
| primary_reproduction/gb17_probabilities.parquet | 2026-09-02 04:21:18 | run_gb_transformer_experiments.py, source SHA-256 52b1aed... | Artifact SHA-256 a00b9b405...; config contains input hashes | seed 42; GB-17; isotonic calibration on model_calibration | 2,073,842 rows, 191,693 test rows | AUTHORITATIVE probability artifact |
| primary_reproduction/gb18_probabilities.parquet | 2026-09-02 04:21:56 | run_gb_transformer_experiments.py, source SHA-256 52b1aed... | Artifact SHA-256 a6cedf1e...; same input hashes | seed 42; GB-18; isotonic calibration on model_calibration | 2,073,842 rows, 191,693 test rows | AUTHORITATIVE probability artifact |
| primary_reproduction/decisions/sealed_test_decisions.parquet | 2026-09-02 04:25:40 | final decision export; exact generating command not recorded | SHA-256 5a9deaf4...; pair keys exactly align with both probability artifacts | manual thresholds 0.98/0.95 and selected GA genome; test labels present after selection | 191,693 model-scored test rows only | VALID BUT DIFFERENT SCOPE |
| primary_reproduction/test_results.csv | 2026-09-02 04:21:59 | run_gb_transformer_experiments.py | SHA-256 a644f4c9...; manifest claims current input hashes | seed 42; workflow constants included by nested_split_constants | workflow-level summary | INCOMPLETE; not reproduced by sealed decisions |
| primary_reproduction/raw_metrics_recomputed.csv | 2026-09-02 04:25:40 | recomputation/export path not recorded separately | SHA-256 7d0392b8... | same claimed primary policy | workflow-level summary | INCOMPLETE; agrees with test_results but not granular decisions |
| primary_reproduction/decisions plus test summaries | generated within the same final run window | exact exporter provenance absent | pair-key join is good; constant lineage is not | exact-tier and blocking constants conflict with current candidate cache | mixed scored/workflow family | INCOMPLETE |
| repeated_outer/outer_{101,202,303} | result files have no creation metadata or source/hash manifest | experiments/code/run_icsec_repeated_outer.py; source SHA-256 not captured in outer package | no full environment snapshot; no input hash manifest | outer seeds 101/202/303; retrain, recalibrate, GA-select per outer split; policy uses 2,1,0.1 | outer workflow metrics | VALID BUT DIFFERENT SCOPE; provenance incomplete |
| repeated_outer/summary.csv and all_results.csv | no recorded creation timestamp | run_icsec_repeated_outer.py | no package hash manifest | same repeated-outer protocol | aggregate/per-outer workflow metrics | AUTHORITATIVE for the repeated-outer numerical family, with limitation |
| blocking-miss artifact at artifacts/decisioning/analysis_decision_matrix/blocking_missed_pairs.csv | absent | recorded path only; source logic is exp_lib.py | manifest claims SHA-256 b43bbaa3... and 1,844,539 bytes, but file is absent | blocking misses are fixed FN constants | row-level misses unavailable | UNVERIFIABLE |
| primary_reproduction/error_analysis/candidate_retrieval_decomposition.csv | 2026-09-02 result family; filesystem creation time not separately recorded | analysis/export path not recorded | aggregate only | cross-platform project scope | retrieval aggregates | AUTHORITATIVE for its aggregate scope; row-level miss evidence missing |
| statistical_analysis/paired_bootstrap_ci.csv | analysis artifact; exact timestamp not recorded | analyze_icsec_primary.py per repository audit | analysis manifest; 2,000 samples | paired conditional bootstrap; exact/blocking constants fixed | scored held-out pairs plus fixed constants | INCOMPLETE pending primary-lineage reconciliation |
| cost_sensitivity.csv | analysis artifact; exact timestamp not recorded | sensitivity analysis path not recorded | CSV itself only | post-hoc scenarios; no retuning | 36 rows = 12 weight scenarios x 3 methods | VALID BUT DIFFERENT SCOPE |

Primary configuration records: split entity_nested_v1, seed 42, GB random_state 42, negative ratio 3.0, isotonic calibration, manual thresholds MATCH >= .98 and REVIEW >= .95, GA seeds [7,42,123,999,2025], population 60, generations 40, elite 12, mutation probability .30, sigma .02, selected seed 999. The primary manifest records the input hashes listed above and generated_at 2026-09-02T11:21:59+07:00. It does not record a valid hash for a present blocking-miss file.

B. sealed_test_decisions conflict explanation

The sealed parquet is not a different model or probability run:

- It has 191,693 rows, exactly the primary test-row count in both probability artifacts.
- Pair keys exactly match both probability artifacts; no left-only or right-only keys were found.
- Stored probabilities match the probability artifacts exactly on every paired row.
- Reapplying the recorded manual thresholds reproduces every stored GB-17 and GB-18 decision.
- Reapplying the recorded GA genome reproduces every stored GB-18-GA decision.

The conflict is therefore not caused by C, a different threshold constant, or a scored-candidate-only decision bug. It is caused at the workflow-constant boundary: the parquet contains model-scored test decisions only, while test_results.csv/raw_metrics_recomputed.csv add exact-tier and blocking-missed constants from a conflicting constant/result family. The current candidate cache independently reports 3,736 exact-tier test positives and 11 exact-tier test negatives; the conflicting primary summary family uses recorded constants equivalent to 3,692 exact-tier TP, 6 exact-tier FP, and 1,028 blocking-missed FN. The missing blocking-miss file prevents independently proving the latter constants.

Independent model-scored-test recomputation from sealed_test_decisions.parquet:

| Method | TP | FP | FN | REVIEW | Precision | Recall | F1 | U = 2FP+FN+0.1REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 0 | 8 | 970 | 3,192 | 0.000000 | 0.000000 | 0.000000 | 1,305.2 |
| GB-18 | 2,655 | 64 | 825 | 623 | 0.976462 | 0.762931 | 0.856590 | 1,015.3 |
| GB-18-GA | 2,994 | 96 | 559 | 847 | 0.968932 | 0.842668 | 0.901400 | 835.7 |

This is a valid scored-candidate-only table and must not be presented as the paper's workflow table.

The old workflow table remains:

| Method | TP | FP | FN | REVIEW | Precision | Recall | F1 | U |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 3,736 | 19 | 1,976 | 3,192 | 0.994940 | 0.425755 | 0.596329 | 2,333.2 |
| GB-18 | 6,391 | 75 | 1,831 | 623 | 0.988401 | 0.728319 | 0.838659 | 2,043.3 |
| GB-18-GA | 6,730 | 107 | 1,565 | 847 | 0.984350 | 0.766952 | 0.862157 | 1,863.7 |

These values agree with the two summary CSVs and manuscript, but not with the complete available granular evidence. They are not cleared for publication.

C. 29,243 vs 29,247 explanation

This discrepancy is exactly four same-platform positives.

Independent grouping of the authoritative profile file by non-empty user_folder gives:

- TOTAL LABELED POSITIVES: 29,247 (all platform pairs within each entity group).
- CROSS-PLATFORM LABELED POSITIVES: 29,243.
- SAME-PLATFORM POSITIVES: 4.

The four-pair difference is exactly confirmed by platform labels; no profile identifiers or pair records are included in this report. The candidate workflow itself is cross-platform only, and its labeled-positive count is 25,931 within that cross-platform scope. exp_lib.py's TOTAL_POS_FULL=29247 is therefore a valid all-platform historical constant, but it is wrong for the paper's cross-platform workflow denominator.

Recommended paper quantity: 29,243 CROSS-PLATFORM LABELED POSITIVES, because the possible-pair denominator, candidate generator, covered-positive count, and miss count are all cross-platform. If the all-platform quantity is retained for diagnostic context, label it explicitly as TOTAL LABELED POSITIVES and state that it includes four same-platform positives excluded from the workflow.

D. 3,312 vs 3,316 explanation

The aggregate relationship is exact:

29,243 cross-platform positives - 25,931 covered cross-platform positives = 3,312 cross-platform blocking misses.

29,247 all-platform positives - 25,931 covered workflow positives = 3,316 all-positive misses.

Thus 3,312 is the correct cross-platform workflow miss count and 3,316 is the all-platform/historical-scope count containing the four same-platform positives. The result is proven from the profile grouping and the candidate artifact aggregates. The row-level blocking-missed CSV is absent, so the individual four rows cannot be inspected; this is a provenance limitation, not a reason to change the aggregate conclusion.

Retrieval denominator and recomputation:

retrieval recall = candidate-covered cross-platform positives / all cross-platform positives
                 = 25,931 / 29,243
                 = 0.8867421263 = 88.6742%

possible cross-platform pairs = 449,149,239
workflow candidate pairs = 2,086,245
candidate-space reduction = 1 - 2,086,245 / 449,149,239
                         = 0.9953551185 = 99.5355%

The report must call the 3,312 value CROSS-PLATFORM BLOCKING MISSES. It must not use 3,316 in that workflow statement.

E. exact-tier/model-scored reconciliation

The candidate artifact contains:

- exact-tier candidate pairs: 12,403
- model-scored candidate pairs: 2,073,842
- total candidate-workflow pairs: 2,086,245
- arithmetic check: 12,403 + 2,073,842 = 2,086,245

The exact tier contains 12,340 positive and 63 negative pairs in the full candidate artifact. The primary test partition currently contains 3,747 exact-tier rows: 3,736 positive and 11 negative. The sealed parquet contains none of these exact-tier rows; its 191,693 rows are the model-scored test scope.

Required scope separation:

- candidate-workflow metrics: exact-tier decisions + model-scored decisions, with blocking misses added as fixed FN constants;
- model-scored metrics: only the 2,073,842 model-scored rows (or 191,693 model-scored test rows);
- exact-tier metrics: only AUTO_EXACT rows;
- blocking-miss constants: positives absent from the candidate workflow, not model-scored rows.

No single current artifact supports a fully authoritative primary workflow table because the exact-tier counts in the current candidate cache disagree with the constants used by the old workflow summaries, and the row-level blocking artifact is missing.

F. utility-weight reconciliation

The frozen implementation and primary config use W_FP=2.0, W_FN=1.0, W_REV=0.1, exactly matching U = 2FP + FN + 0.1REVIEW. The selected primary GA genome (seed 999) has validation cost 589.8 under those weights. The repeated-outer runner uses the same weights.

The cost_sensitivity.csv has two metadata problems:

1. Its note says policies were selected under historical 5/1/0.02 weights, although every row is marked post_hoc_only=True and the frozen primary config says selection used 2/1/0.1.
2. The CSV includes the frozen 2/1/0.1 scenario as one post-hoc sensitivity row, but the table does not itself prove how the policy was selected.

Evidence classification:

- 2/1/0.1: weights actually used to select the frozen primary GA policy and to report frozen U.
- 5/1/0.02: historical weights referenced by stale metadata; not the frozen primary selection weights.
- Other rows in cost_sensitivity.csv: post-hoc sensitivity analysis only; no GA retuning or test-based selection is evidenced.

Do not change the manuscript objective based on this CSV. Correct or regenerate the CSV metadata in a future evidence regeneration, without overwriting the historical file. Mark the sensitivity table as post-hoc and distinguish its historical note from the frozen objective.

G. repeated-outer provenance

Numerical artifacts exist for outer seeds 101, 202, and 303. Each per-outer split manifest records entity_nested_v1, the outer seed, deterministic assignment logic, entity overlap passed, test-label access after selection, selected policy, and exact/blocking constants. The repeated runner source is experiments/code/run_icsec_repeated_outer.py.

Available evidence supports:

- source logic and deterministic outer assignment;
- seed-specific model train/calibration/GA-validation/test separation;
- GB-17 and GB-18 retraining and isotonic calibration;
- GA selection on validation only;
- 2/1/0.1 result calculations;
- internally consistent per-outer results, all_results.csv, and summary.csv.

Limitation: the repeated_outer package has no full environment snapshot, source hash manifest, dataset hash manifest, or per-output artifact hash manifest. Exact package versions and exact source bytes used at execution cannot be reconstructed from that package alone. This is labeled INCOMPLETE provenance, not silently repaired.

H. Authoritative numerical table

H1. Authoritative candidate-generation values

| Quantity | Recomputed value | Scope |
|---|---:|---|
| Profiles in raw input | 36,807 | corpus |
| Possible cross-platform pairs | 449,149,239 | valid profile-row/profile-id implementation scope |
| Workflow candidate pairs | 2,086,245 | cross-platform workflow |
| Exact-tier pairs | 12,403 | candidate workflow |
| Model-scored pairs | 2,073,842 | candidate workflow |
| Cross-platform labeled positives | 29,243 | denominator |
| Covered cross-platform positives | 25,931 | candidate workflow |
| Cross-platform blocking misses | 3,312 | denominator complement |
| Retrieval recall | 88.6742% | 25,931 / 29,243 |
| Space reduction | 99.5355% | 1 - 2,086,245 / 449,149,239 |

H2. Authoritative repeated-outer workflow table

The following values are reproduced from repeated_outer/all_results.csv and aggregate with sample SD (ddof=1):

| Method | Precision mean±SD | Recall mean±SD | F1 mean±SD | FP mean±SD | FN mean±SD | REVIEW mean±SD | U mean±SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 0.990933±0.005101 | 0.713700±0.043052 | 0.829200±0.027744 | 59.0±35.763 | 2266.333±113.390 | 264.667±395.880 | 2410.800±98.920 |
| GB-18 | 0.993967±0.001026 | 0.709933±0.032164 | 0.827967±0.022228 | 38.0±7.000 | 2152.000±232.646 | 438.000±406.089 | 2271.800±198.503 |
| GB-18-GA | 0.988900±0.005437 | 0.761400±0.002816 | 0.860333±0.001137 | 75.667±38.423 | 1559.000±38.105 | 923.333±151.133 | 1802.667±68.308 |

Per-outer rows: seed 101 / 202 / 303 are exactly those in repeated_outer/all_results.csv and repeated_outer/summary.csv; the manuscript rounded values agree. Candidate recall mean±SD is 0.883772±0.000225 and blocking misses are 1023.667±10.214 in this repeated-outer scope.

H3. Primary frozen scored-candidate table

See experiments/icsec_final/reconciliation/independent_recomputation.json and independent_model_scored_metrics.csv. These are the only independently recomputed primary decision metrics cleared as numerical evidence, and they are model-scored-candidate-only. They cannot replace the workflow table without adding a verified exact-tier and blocking-miss constant chain.

H4. Paired bootstrap

The stored paired bootstrap values are internally consistent with the old raw-metric family, including GB-18-GA minus GB-18 F1 difference 0.0234984 [0.0207617, 0.0262447], recall difference 0.0386325 [0.0344160, 0.0427350], FP difference 32 [22,44], FN difference -266 [-299,-234], REVIEW difference 224 [165.975,283], and U difference -179.6 [-214.7025,-144.1000]. Because the underlying primary workflow decisions are not reconciled, these intervals remain INCOMPLETE and are not cleared as final primary evidence.

I. Manuscript values to KEEP

Keep numerically, subject to the scope wording below:

- 36,807 profiles, with the implementation eligibility caveat that valid profile_row_id and valid profile_id are required for candidate generation.
- 449,149,239 possible cross-platform pairs.
- 2,086,245 workflow candidate pairs.
- 12,403 exact-tier pairs and 2,073,842 model-scored pairs.
- 29,243 cross-platform positives, 25,931 covered positives, 3,312 cross-platform misses.
- 88.6742% retrieval recall and 99.5355% space reduction.
- Repeated-outer values in the repeated-outer table, with its provenance limitation.
- U definition and frozen weights 2/1/0.1.

Do not treat the primary frozen workflow precision/recall/F1/FP/FN/U values as cleared merely because they agree with the manuscript and two summary files.

J. Manuscript values to CHANGE

Do not edit yet; these are required changes after a new authoritative primary run:

- Replace the primary frozen workflow table values after regenerating one pair-key-aligned workflow artifact. The current 3,736/19/1,976, 6,391/75/1,831, and 6,730/107/1,565 rows are not independently cleared.
- Replace or explicitly downgrade the stored paired-bootstrap claims after the primary decision lineage is regenerated.
- Correct any use of 3,316 to 3,312 when the statement is cross-platform workflow retrieval.
- Remove or label TOTAL_POS_FULL=29,247 as all-platform historical scope; do not use it as the cross-platform denominator.

K. Manuscript statements needing scope clarification

Required wording-level clarifications:

- State that 29,243 is CROSS-PLATFORM LABELED POSITIVES. If 29,247 is mentioned, define it as TOTAL LABELED POSITIVES including four same-platform positives excluded by the workflow.
- State that 3,312 is CROSS-PLATFORM BLOCKING MISSES. Do not call 3,316 the workflow miss count.
- State that workflow metrics include exact-tier decisions and fixed blocking-miss FN constants, while sealed model metrics cover only model-scored candidates.
- State explicitly that 12,403 + 2,073,842 = 2,086,245.
- State that 88.6742% is retrieval recall, not classifier recall, and uses 25,931/29,243.
- State that U is an illustrative declared utility, not measured economic cost.
- Mark cost_sensitivity.csv scenarios as post-hoc sensitivity and remove the stale implication that frozen selection used 5/1/0.02.
- State the repeated-outer hash/environment limitation.
- State the dual candidate eligibility filter: valid profile_row_id and valid profile_id.

L. Remaining unverifiable evidence

- The row-level blocking_missed_pairs.csv is absent despite a path, byte count, and SHA-256 being recorded in the primary manifest.
- The exact primary command/export provenance for sealed_test_decisions.parquet and raw_metrics_recomputed.csv is not separately recorded.
- The primary workflow constants used by the old summaries cannot be reconstructed from the present cache and available files.
- Exact environment/source/input hash manifests for repeated_outer seeds 101/202/303 are unavailable.
- The stored paired bootstrap and error-decomposition outputs cannot be promoted to fully authoritative primary workflow evidence until the decision-family conflict is resolved.
- No exact environment hash for the feature-cache generation is present.

M. Test results

Command: uv run pytest -q

Result: 45 passed in 11.21s; 0 failed.

Tests passing does not resolve historical artifact lineage or numerical-scope conflicts.

Final artifact classifications

| Artifact family | Classification |
|---|---|
| Current candidate/retrieval aggregate | AUTHORITATIVE |
| Sealed model-scored decisions | VALID BUT DIFFERENT SCOPE |
| Primary test_results.csv and raw_metrics_recomputed.csv workflow summaries | INCOMPLETE |
| Repeated-outer numerical results | AUTHORITATIVE for repeated-outer scope |
| Repeated-outer provenance package | INCOMPLETE |
| Blocking-miss row artifact | UNVERIFIABLE |
| Paired bootstrap | INCOMPLETE |
| Cost sensitivity | VALID BUT DIFFERENT SCOPE |
| exp_lib.py TOTAL_POS_FULL=29247 constant | STALE for cross-platform paper scope |
| Historical 5/1/0.02 metadata note | STALE metadata |

Required next action before review: regenerate a new primary read-only evidence package from one exact pair-key-aligned candidate, exact-tier, blocking-miss, probability, decision, and metric chain, with source/input/environment hashes. Do not edit the manuscript before that regeneration passes.
