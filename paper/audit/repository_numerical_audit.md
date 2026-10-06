Repository, experiment, and numerical audit

Audit scope

Inspected source and artifacts under:
- src/identity_resolution/
- experiments/code/
- experiments/icsec_final/
- tests/
- paper/research_protocol.md
- paper/tables/
- paper/overleaf/main.tex

Protected paths were not modified: paper/overleaf/main.tex, paper/overleaf/references.bib, and paper/overleaf/figures/.

Final verdict

REPOSITORY CONSISTENCY: FAIL
NUMERICAL CONSISTENCY: FAIL
DATA LEAKAGE RISK: LOW

The protocol, manuscript tables, repeated-outer artifacts, source implementation, and unit tests are broadly aligned on the intended frozen ICSEC design. However, the primary sealed-test decision artifact does not reproduce the primary test_results.csv/raw_metrics_recomputed.csv numbers, the candidate-retrieval artifact is absent at the path recorded by the run, and one historical constant in exp_lib.py disagrees with the current primary retrieval artifact. These are material audit failures even though the tests pass and the reported repeated-outer table is internally consistent.

1. Reconstructed implementation audit

| Item | Artifact/source finding | Match to protocol/manuscript |
|---|---|---|
| Candidate generation | src/identity_resolution/workflows/full_candidate.py:35,90-151 uses exact username and external URL tiers, then username_prefix3, fullname_prefix3, and external_domain blocking; cross-platform pairs only; duplicate keys removed. | YES |
| Feature construction | experiments/code/run_gb_transformer_experiments.py:281-356 trains from cached feature frames; pair_features17 plus pair_bert_cos are joined one-to-one. | YES for frozen experiment |
| GB-17 definition | 17 columns in primary_reproduction/config.json and training_metadata.json: three username similarities, three full-name similarities, name_sim, bio Jaccard/length/availability, location Jaro/exact/availability, same-platform, username length difference, full-name word-count difference, username-prefix match. | YES |
| GB-18 definition | GB-17 columns plus bert_cos from cached pair_bert_cos.parquet; same sampled pair hash, labels, model seed, and hyperparameters asserted. | YES |
| Gradient Boosting settings | run_gb_transformer_experiments.py:63-68 and 295-300: GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42). | YES |
| Negative sampling | run_gb_transformer_experiments.py:271-289; deterministic undersample_negatives with 3.0 negatives per positive. Primary metadata: 498,209/6,759 before and 20,277/6,759 after. | YES |
| Isotonic calibration | run_gb_transformer_experiments.py:302-306: IsotonicRegression(out_of_bounds='clip'), fitted on model_calibration only. | YES |
| Fixed thresholds | run_gb_transformer_experiments.py:60-62,260-264 and ThresholdPolicy: MATCH >= .98, REVIEW >= .95, otherwise NO_MATCH. | YES |
| GA genome | exp_r1_ga_redecision.py:3,69-78: [t_m,t_r,c_promote,c_demote]. | YES |
| GA decision logic | exp_r1_ga_redecision.py:69-78 exactly implements high-probability MATCH, review-band name promote/demote, and low-probability NO_MATCH. | YES |
| GA constraints | exp_r1_ga_redecision.py:100-106: .90 <= t_m <= .999; .50 <= t_r <= t_m; .50 <= c_promote <= 1; 0 <= c_demote <= c_promote. | YES |
| Population/generations/elites | run_gb_transformer_experiments.py:384-400: 60/40/12 in full run. | YES |
| Mutation settings | exp_r1_ga_redecision.py:114-120: Gaussian sigma .02, per-gene probability .30; uniform crossover at lines 109-111. | YES |
| Random seeds | model/split seed 42; GA seeds [7,42,123,999,2025]. | YES |
| Entity-disjoint protocol | exp_lib.py:166-221 assigns entity roles and asserts no overlap; cross-role pairs receive drop. | YES, with the caveat below about the outer implementation |
| Train/calibration/GA-validation/test isolation | runner trains only model_train, calibrates only model_calibration, optimizes only ga_validation, and opens test labels at the final evaluation block (lines 722-735). | YES by source and tests |
| Cross-role pair dropping | exp_lib.py:190-195 assigns drop unless both endpoints have the same role; dropped rows are excluded from training/evaluation. | YES |
| Test-label isolation | labels_for blocks test unless allow_test=True; tests/test_nested_protocol.py:136-167 checks changing test labels cannot change the GA genome. | YES by source/tests; primary numeric artifact conflict remains |

Important implementation qualification: run_icsec_repeated_outer.py:37 first rewrites cache split using the outer-seed hash and then calls build_nested_entity_split. The resulting repeated artifacts are consistent with the intended outer seed protocol, but this path should be retained as the authoritative repeated-run implementation rather than inferred from the generic exp_lib docstring, which still describes the older R0-R5 workflow.

2. Historical-family separation

The protocol explicitly declares only GB-17, GB-18, and GB-18-GA as primary. The manuscript main ablation and repeated-outer tables use those three methods only. Historical R0/R3 rows remain in primary_reproduction/summary.json and summary.md as comparison metadata and are explicitly labeled historical/non-primary by the protocol and tables.

No direct historical metric was silently inserted into the manuscript main table. Nevertheless, retaining R0/R3 in the primary summary creates a provenance hazard: primary_reproduction/summary.json:8-33 includes R0 and R3 alongside the frozen family, and its R3-to-GB-18-GA effect is not a controlled GB-family ablation. It must remain clearly non-comparable.

3. Numerical verification: primary frozen split

Source categories:
- Manuscript value: paper/overleaf/main.tex.
- Reported artifact: primary_reproduction/test_results.csv and raw_metrics_recomputed.csv.
- Independent sealed decision artifact: primary_reproduction/decisions/sealed_test_decisions.parquet, recomputed here with the test constants recorded in split_manifest.json (tp_exact=3,692, fp_exact=6, fn_blocking=1,028, total_pos=8,829).

The first two artifact files agree with the manuscript, but the sealed decision artifact disagrees. Therefore the manuscript values are not independently reproducible from the persisted per-pair decisions.

| Method/quantity | MANUSCRIPT VALUE | ARTIFACT VALUE | SOURCE | MATCH |
|---|---:|---:|---|---|
| GB-17 precision | .9949 | .994940 in raw metrics; .9962 from sealed decisions | main.tex:128; raw_metrics_recomputed.csv:2; sealed_test_decisions.parquet | NO |
| GB-17 recall | .4258 | .425755 in raw metrics; .4182 sealed | same | NO |
| GB-17 F1 | .5963 | .596329 in raw metrics; .5891 sealed | same | NO |
| GB-17 FP | 19 | 19 reported; 14 sealed | same | NO |
| GB-17 FN | 1,976 | 1,976 reported; 1,998 sealed | same | NO |
| GB-17 REVIEW | 3,192 | 3,192 in both | same | YES for REVIEW only |
| GB-17 utility/cost | 2,333.2 | 2,333.2 reported; 2,345.2 sealed | same; cost formula in business_cost.py:26-27 | NO |
| GB-18 precision | .9884 | .988401 reported; .9891 sealed | same | NO |
| GB-18 recall | .7283 | .728319 reported; .7189 sealed | same | NO |
| GB-18 F1 | .8387 | .838659 reported; .8326 sealed | same | NO |
| GB-18 FP | 75 | 75 reported; 70 sealed | same | NO |
| GB-18 FN | 1,831 | 1,831 reported; 1,853 sealed | same | NO |
| GB-18 REVIEW | 623 | 623 in both | same | YES for REVIEW only |
| GB-18 utility/cost | 2,043.3 | 2,043.3 reported; 2,055.3 sealed | same | NO |
| GB-18-GA precision | .9843 | .984350 reported; .9850 sealed | same | NO |
| GB-18-GA recall | .7670 | .766952 reported; .7573 sealed | same | NO |
| GB-18-GA F1 | .8622 | .862157 reported; .8562 sealed | same | NO |
| GB-18-GA FP | 107 | 107 reported; 102 sealed | same | NO |
| GB-18-GA FN | 1,565 | 1,565 reported; 1,587 sealed | same | NO |
| GB-18-GA REVIEW | 847 | 847 in both | same | YES for REVIEW only |
| GB-18-GA utility/cost | 1,863.7 | 1,863.7 reported; 1,875.7 sealed | same | NO |

Independent sealed-artifact recomputation details:
- Sealed test rows: 191,693 scored candidates; actual positives in that file: 4,033.
- GB-17 scored decisions: MATCH TP=0, FP=8; NO_MATCH positive count=970; REVIEW=3,192.
- GB-18 scored decisions: MATCH TP=2,655, FP=64; NO_MATCH positive count=825; REVIEW=623.
- GB-18-GA scored decisions: MATCH TP=2,994, FP=96; NO_MATCH positive count=559; REVIEW=847.
- Adding the recorded exact/blocking constants gives respectively (TP,FP,FN,REVIEW): GB-17=(3,692,14,1,998,3,192), GB-18=(6,347,70,1,853,623), GB-18-GA=(6,686,102,1,587,847).

This is the principal numerical failure. The persisted decision file appears to be generated from a different or stale alignment than test_results.csv/raw_metrics_recomputed.csv, despite summary.json claiming those outputs are the primary reproduction.

4. Numerical verification: repeated outer splits

The repeated outer artifacts are internally consistent. all_results.csv was independently aggregated with sample standard deviation (ddof=1), matching summary.csv, paper/tables/repeated_outer_results.md, and main.tex:128-130.

| Method/quantity | MANUSCRIPT VALUE | ARTIFACT VALUE | SOURCE | MATCH |
|---|---:|---:|---|---|
| GB-17 mean precision ± SD | .9909 ± .0051 | .990933 ± .005101 | all_results.csv -> aggregate | YES |
| GB-17 mean recall ± SD | .7137 ± .0431 | .713700 ± .043052 | same | YES |
| GB-17 mean F1 ± SD | .8292 ± .0277 | .829200 ± .027744 | same | YES |
| GB-17 FP/FN/REVIEW | 59.0 ±35.8 / 2266.3 ±113.4 / 264.7 ±395.9 | identical | same | YES |
| GB-17 utility/cost | 2410.8 ±98.9 | 2410.800 ±98.920 | same | YES |
| GB-18 mean precision ± SD | .9940 ± .0010 | .993967 ± .001026 | same | YES |
| GB-18 mean recall ± SD | .7099 ± .0322 | .709933 ± .032164 | same | YES |
| GB-18 mean F1 ± SD | .8280 ± .0222 | .827967 ± .022228 | same | YES |
| GB-18 FP/FN/REVIEW | 38.0 ±7.0 / 2152.0 ±232.6 / 438.0 ±406.1 | identical | same | YES |
| GB-18 utility/cost | 2271.8 ±198.5 | 2271.800 ±198.503 | same | YES |
| GB-18-GA mean precision ± SD | .9889 ± .0054 | .988900 ± .005437 | same | YES |
| GB-18-GA mean recall ± SD | .7614 ± .0028 | .761400 ± .002816 | same | YES |
| GB-18-GA mean F1 ± SD | .8603 ± .0011 | .860333 ± .001137 | same | YES |
| GB-18-GA FP/FN/REVIEW | 75.7 ±38.4 / 1559.0 ±38.1 / 923.3 ±151.1 | identical | same | YES |
| GB-18-GA utility/cost | 1802.7 ±68.3 | 1802.667 ±68.308 | same | YES |
| Per-split F1 and utility | seed 101: .8394/.8408/.8616; seed 202: .7978/.8408/.8600; seed 303: .8504/.8023/.8594; utilities as in main.tex:145-147 | exact rows in repeated_outer/all_results.csv | all_results.csv and per-split test_results.csv | YES |
| GA F1 differences | +.0208, +.0192, +.0571 | independently recomputed from all_results.csv | all_results.csv | YES |
| GA utility differences | lower by 292.0, 668.6, 446.8 | independently recomputed | all_results.csv | YES |
| Repeated candidate recall | .8838 ± .0002 | .883772 ± .000225 | all_results.csv | YES |
| Repeated blocking misses | 1023.7 ±10.2 | 1023.667 ±10.214 | all_results.csv | YES |

5. Retrieval and dataset numerical audit

| Quantity | MANUSCRIPT VALUE | ARTIFACT VALUE | SOURCE | MATCH |
|---|---:|---:|---|---|
| Profiles | 36,807 | 36,807 raw rows; 36,804 rows after full_candidate.py filters both valid profile_row_id and profile_id | main.tex:59; full_candidate.py:50-68; direct read | YES for stated corpus; protocol eligibility is underspecified |
| Platform counts | Twitter 13,960; Google+ 11,890; Instagram 10,957 | same raw counts; valid-pair input counts 13,959/11,889/10,956 | direct read of normalized_profiles_with_profile_id.csv | YES for corpus, but eligibility caveat |
| Possible cross-platform pairs | 449,149,239 | independently recomputed from valid counts: 13,959*11,889 + 13,959*10,956 + 11,889*10,956 = 449,149,239 | full_candidate.py:71-79 and direct recomputation | YES |
| Candidate workflow pairs | 2,086,245 | len(experiments/scored_pairs_enriched.parquet)=2,086,245 | candidate_retrieval_decomposition.csv; cache | YES |
| Space reduction | 99.5355% | 0.9953551185 = 99.53551185% | candidate_retrieval_decomposition.csv; direct formula | YES after rounding |
| Labeled positives | 29,243 | 29,243 in candidate_retrieval_decomposition.csv; exp_lib.py:26 still hard-codes TOTAL_POS_FULL=29,247 | analysis artifact vs source constant | NO: stale source constant |
| Covered positives | 25,931 | 25,931 in decomposition artifact | candidate_retrieval_decomposition.csv | YES to artifact |
| Blocking misses | 3,312 | 3,312 reported, but referenced blocking-missed CSV is absent; analysis metadata says blocking_miss_artifact_rows=3,316 | candidate_retrieval_decomposition.csv; analysis script:233-245 | NO / not independently traceable |
| Retrieval recall | 88.6742% | 25,931/29,243 = .8867421263 | candidate_retrieval_decomposition.csv; direct formula | YES |
| Blocking-miss artifact rows | not stated in manuscript | 3,316 | candidate_retrieval_decomposition.csv | N/A; discrepancy with 3,312 positives must be resolved |

The 449,149,239 denominator is reproducible only after applying the implementation's second validity filter on profile_id. research_protocol.md:15 says rows with valid profile_row_id, but full_candidate.py:54-55 also requires valid profile_id. The protocol should state both filters in any future correction.

The blocking-missed file recorded in primary artifacts at /Users/thawaree.kha/Project-for-Work/artifacts/decisioning/analysis_decision_matrix/blocking_missed_pairs.csv is not present in the inspected repository. The analysis output was found, but the underlying row-level artifact could not be independently checked. Four more rows than positive misses are recorded in metadata; their label/content composition is unknown without the missing file.

6. Confidence intervals, failure analysis, and sensitivity

| Quantity | MANUSCRIPT VALUE | ARTIFACT VALUE | SOURCE | MATCH |
|---|---:|---:|---|---|
| Bootstrap samples | 2,000 | 2,000 | main.tex:94,178; analysis_manifest.json | YES |
| Bootstrap type | paired conditional; exact/blocking constants fixed | same string in paired_bootstrap_ci.csv | analyze_icsec_primary.py:60-99 and CSV | YES |
| GA minus GB-18 F1 difference/CI | +.0235 [.0208,.0262] | .0234984 [.0207617,.0262447] | main.tex:178; paired_bootstrap_ci.csv:11 | YES to stored CI |
| Recall difference/CI | +.0386 [.0344,.0427] | .0386325 [.0344160,.0427350] | CSV:10 | YES |
| FP difference/CI | +32 [22,44] | 32 [22,44] | CSV:12 | YES to stored CI |
| FN difference/CI | -266 [-299,-234] | -266 [-299,-234] | CSV:13 | YES to stored CI |
| REVIEW difference/CI | +224 [166,283] | 224 [165.975,283] | CSV:14 | YES to rounding |
| Utility difference/CI | -179.6 [-214.7,-144.1] | -179.6 [-214.7025,-144.1000] | CSV:15 | YES to rounding |
| GA scored-candidate FP | 96 | 96 | failure_category_counts.csv and sealed decisions | YES |
| High-name-band GA FP | 66 | 66 | failure_category_counts.csv | YES |
| GA scored-candidate FN | 559 | 559 | failure_category_counts.csv and sealed decisions | YES |
| FN lacking paired bio | 242 | 242 | failure_category_counts.csv | YES |
| FN lacking usable paired URL | 236 | 236 | failure_category_counts.csv | YES |
| FN lacking paired location | 559 | 559 | failure_category_counts.csv | YES |
| Review positives/negatives | 480 / 367 | 480 / 367 | failure_category_counts.csv and sealed decisions | YES |
| GA lowest-cost sensitivity scenarios | 8 of 12 | 8 of 12 rows marked GB-18-GA winner | cost_sensitivity.csv | YES |

The stored CI values agree with the manuscript and raw-metric claim, but the sealed decision file yields different primary confusion counts. Thus the CI is numerically consistent with the stored raw-metric/analysis lineage, not with the persisted sealed per-pair decision table. The uncertainty claim should not be treated as verified until these lineages are reconciled.

7. Leakage and protocol assessment

Evidence supporting LOW rather than MEDIUM/HIGH/CRITICAL:
- labels_for() hard-blocks test access unless allow_test=True (runner lines 166-180).
- The runner trains on model_train, calibrates on model_calibration, and runs GA on ga_validation before the one final test-label read (runner lines 281-310, 376-469, 722-756).
- tests/test_nested_protocol.py verifies entity disjointness, cross-role dropping, train-only scaler behavior for the related training path, and that changing test labels cannot change GA selection.
- All 45 tests pass.

Residual risk is procedural rather than demonstrated test leakage: primary_reproduction/decisions/sealed_test_decisions.parquet contains test labels by design after final evaluation, but it is inconsistent with test_results.csv. A stale/misaligned final artifact can invalidate the numerical audit even when the selection protocol itself is leakage-safe. The missing blocking artifact and stale TOTAL_POS_FULL constant also reduce reproducibility, but neither is evidence that test labels influenced fitting or GA selection.

8. Required corrective actions before PASS

1. Reconcile or regenerate sealed_test_decisions.parquet, test_results.csv, raw_metrics_recomputed.csv, paired_bootstrap_ci.csv, and error-analysis outputs from one exact pair-key-aligned test frame.
2. Verify pair ordering and join keys across cache, feature files, probability files, and sealed decisions; persist a digest for the final test pair key set.
3. Restore or explicitly replace the missing blocking_missed_pairs.csv and explain why 3,316 artifact rows correspond to 3,312 labeled positive misses.
4. Remove or correct exp_lib.py:26 TOTAL_POS_FULL=29247; use the verified 29,243 value or derive it from the ground-truth artifact rather than hard-coding.
5. State the dual eligibility filter (valid profile_row_id and valid profile_id) in research_protocol.md and any corrected manuscript evidence package.
6. Re-run the primary numerical analysis and bootstrap only after the above reconciliation; do not edit the manuscript based on the current conflicting artifacts.
7. Keep R0/R3 comparison metadata explicitly outside the primary ablation lineage.

Verification command

uv run pytest -q

Result: 45 passed in 13.12s.
