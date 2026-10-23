MAJOR-REVISION ROOT-CAUSE AUDIT
ICSEC 2026
Audit date: 2026-09-03

1. Executive diagnosis

The current numerical package is internally reproducible within its declared v1 scope, but the central scientific interpretation is not ready for a new paper. Four independent blockers remain:

1. The authoritative GB-17/GB-18 feature cache inherits a predecessor-score gate. The manuscript describes name_sim as an unconditional max of four name-field Jaro-Winkler similarities, but the historical cache computes it only when the predecessor score is at least 0.5 and writes zero otherwise.
2. Test labels are resident in the authoritative candidate table and are read by the pre-evaluation constants calculation. The narrow accessor audit records zero guarded test-label requests, but it does not establish physical label isolation.
3. GB-18-GA changes both the policy family and validation selection relative to the fixed GB-18 policy. The observed F1 change 0.8280 to 0.8604 is therefore not identifiable as a GA-optimizer effect.
4. Provenance closes many files inside authoritative_run, but not the complete upstream chain, especially feature-cache generation, the predecessor model/source, raw-to-transformed derivation, and exact historical execution environment.

Dataset licensing and ethics are also unresolved. Public hosting is verified; permission to reuse or redistribute personal profile data is not.

Disposition: the research design is correctable, but current GA and primary performance claims must be suspended pending a clean v2 protocol and rerun. Do not patch the manuscript or alter authoritative artifacts before that rerun.

2. name_sim dependency trace

Relevant implementations coexist:

- Current reusable primitives: src/identity_resolution/core/name_similarity.py:14-40 define Unicode NFKC normalization, case-folding, whitespace normalization, empty-value handling, Damerau similarity, and token-set similarity. These primitives are not the implementation used to create the authoritative pair_features17 cache.
- Historical candidate/experiment cache: experiments/code/exp_lib.py:48-64 defines _name_sim_arrays. For each pair it lowercases and strips userName/fullName at lines 67-69, then computes jellyfish.jaro_winkler_similarity for every non-empty member of the four cross-field combinations (userName_a,userName_b), (userName_a,fullName_b), (fullName_a,userName_b), and (fullName_a,fullName_b), retaining the maximum.
- Cache gate: exp_lib.py:93-101 sets need = decision_source != AUTO_EXACT AND score >= NSIM_MIN_SCORE, with NSIM_MIN_SCORE = 0.5 at line 28. It initializes all name_sim values to 0.0 at line 100 and fills only the gated rows at line 101.
- Feature cache: experiments/code/exp_r2_bert_feature.py:151-167 reads the profile fields; lines 175-201 compute the separate username/fullname Jaro, Levenshtein, and token-sort columns; line 257 copies scored["name_sim"] into the 17-feature output. Thus the feature cache carries the already gated value; it does not independently recompute the advertised unconditional name_sim.
- Authoritative v1: experiments/icsec_final/authoritative_run/run_authoritative_outer.py:50-57 reads pair_features17.parquet, joins its name_sim by pair key, and assigns AUTO_EXACT rows zero. run_authoritative_outer.py:116-122 passes that cache to GB-17 and GB-18, and run_authoritative_outer.py:130-131 passes the same name_sim to the GA policy.
- GB feature registry: experiments/code/exp_r2_bert_feature.py:58-66 lists name_sim as feature 7 of GB-17; GB-18 adds only bert_cos. The protocol repeats this list at PROTOCOL.md:40-45.

Dependency chain:

raw userName/fullName fields
-> exp_lib._clean_names: lowercase, strip, empty/nan to empty
-> historical predecessor score from train_data/stage15_crm_entity_pipeline/artifacts/match_decisions.parquet (the path is referenced by exp_lib.py:19; the file is currently absent)
-> gate score >= 0.5 and decision_source != AUTO_EXACT
-> max of four jellyfish Jaro-Winkler cross-field similarities
-> zero for ungated scored rows; zero for AUTO_EXACT rows in authoritative_run
-> pair_features17.parquet name_sim column
-> GB-17/GB-18 classifier input and GA promote/demote evidence

2.1 Exact answers

1. Mathematical definition actually used:
For an eligible, non-AUTO_EXACT row with predecessor score s >= 0.5,
name_sim = max{JW(u_a,u_b), JW(u_a,f_b), JW(f_a,u_b), JW(f_a,f_b)}
where empty fields contribute no candidate. For s < 0.5, name_sim is forced to 0. For AUTO_EXACT rows in the v1 authoritative join it is also forced to 0. JW is jellyfish.jaro_winkler_similarity on lowercase, stripped strings; this is not the same as the richer current core/name_similarity API.

2. Raw fields: userName_a, fullName_a, userName_b, fullName_b. No bio, location, URL, entity label, or test label enters the numerical similarity itself.

3. Pure similarity metric: no. The inner max is a pure pairwise similarity, but the final feature is a gated/censored learned-feature-dependent value.

4. Modification: yes. It is censored/replaced by zero according to predecessor score and exact-row status.

5. Predecessor: the score column from the historical Stage 15 match_decisions artifact referenced at exp_lib.py:19. Its producing model is not reconstructible from the present authoritative package: the artifact is absent, and no closed source/model/config lineage for that score is recorded. The repository contains a production multimodal model run at train_data/stage7_13_multimodal_suite/runs/image_context_r075_h20_s42, selected as a GB predecessor/production run in settings.py:33-34 and loaded by full_candidate.py:174-185, but the exact artifact that generated the exp_lib cache is not available to prove an identity between those systems.

6. Label/split visibility of predecessor: its output is persisted before R1/R2/GB-18 policy experiments. The available source does not prove that the predecessor was retrained inside each current nested outer split. Therefore the safe finding is a hidden historical model dependency with incomplete split/label provenance, not a proven same-split leak. The predecessor score itself is used as a gate and may also have been trained using labels; that cannot be cleared from the present evidence.

7. Consequences: hidden learned-feature dependency and experimental confounding are established. Data leakage is not proven from the available files, but it cannot be ruled out because predecessor training lineage and split exposure are unavailable. The implementation is invalid for the manuscript's stated pure-feature definition until regenerated. This is more than a wording bug.

8. GB-17/GB-18 description: the feature count and GB-18's one-column bert_cos addition are correct, but the name_sim semantics are incorrect/incomplete. GB-17 and GB-18 are not currently described correctly.

9. Existing validity: the historical GB-17/GB-18 numerical results may be retained only as historical exploratory evidence, not as clean evidence for the stated feature ablation or causal interpretation. Regenerate the feature caches with an explicit unconditional definition and retrain/recalibrate both models. Because the input changes, rerun the complete controlled outer experiment. Do not reuse old GB-17/GB-18 numbers as v2 numerical evidence.

Classification: DESCRIPTION BUG ONLY; HIDDEN MODEL DEPENDENCY; EXPERIMENTAL CONFOUND; INVALID FEATURE CONSTRUCTION. DATA LEAKAGE is not established, but remains an unresolved risk requiring isolation.

3. Test-label access trace and leakage determination

A. Labels exist on disk: yes. candidate_workflow.parquet contains actual; the historical cache also contains actual; blocking-missed-positive artifacts contain positive labels.
B. Loaded into memory: yes. run_authoritative_outer.py:44 reads candidate_workflow.parquet; line 48 converts cache["actual"] to int8. The candidate row table therefore loads test labels before training, calibration, GA, and final evaluation.
C. Programmatically accessible: yes. assigned retains actual through build_nested_entity_split; labels_for can join it by pair key.
D. Actually read before final evaluation: yes. run_authoritative_outer.py:62-81 constants() iterates assigned and computes actual == 1 for exact and scored rows for every role, including test, before line 118 model fitting and line 122 GA selection. The same function uses test blocking counts and test total_pos constants. This is a direct pre-final read even though it is intended for metric constants.
E. Training influence: the guarded training functions use only model_train labels at run_gb_transformer_experiments.py:285-304. No evidence that test labels affect model fitting.
F. Calibration influence: calibration uses model_calibration only at lines 287-305. No evidence that test labels affect calibration.
G. GA fitness/policy selection: run_ga_trials uses ga_validation labels at lines 380-406. The test constants computed earlier are not passed into the GA objective; no evidence that test labels affect selected genome. However, physical isolation is absent and the implementation does not make that guarantee structurally.
H. Final evaluation: test labels are fetched through the guarded accessor at run_authoritative_outer.py:125-126, and the reported audit counts three after-final requests (one per outer split).

The label_access_audit.json result (0 before, 3 after) proves only that no guarded labels_for(test) call occurred before final evaluation. It does not prove that actual was unavailable. The cache load and constants() read bypass that accessor.

For test entities, first load is run_authoritative_outer.py:44-48. First direct label read is constants() at lines 62-80, called at line 117. The nominal first guarded accessor read is lines 125-126, but that is not the first actual label read.

Determination: REAL PRE-EVALUATION LABEL ACCESS. It is not demonstrated that the access changed model, calibration, seed, or GA selection; therefore call it pre-evaluation access rather than proven actual test leakage in the causal-selection sense. The manuscript's stronger claim that test labels were unavailable is false.

Required protocol correction, not yet implemented:
- Build candidate, feature, probability, and split-role tables without any actual/label column for sealed-test rows.
- Store test labels in a separate access-controlled artifact or separate input argument unavailable to all training/calibration/policy-selection code.
- Make constants for model_train, model_calibration, and policy-validation from their role labels only. Do not compute test exact-tier, blocking-miss, or total-positive constants until final evaluation.
- Final evaluator alone joins sealed-test labels to pair-keyed decisions and computes all test metrics. Instrument file reads and label-join calls, not merely one function.
- Use a fresh v2 outer partition and do not use test labels for threshold, hyperparameter, optimizer, seed, or report selection.

4. GA claim identifiability

Classifier: both GB-17 and GB-18 use sklearn GradientBoostingClassifier with n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42. GB-18 adds bert_cos to the 17-feature set. The GA does not retrain either classifier.

Calibrated probabilities: each model is calibrated by a separate IsotonicRegression(out_of_bounds='clip') fit on model_calibration only (run_gb_transformer_experiments.py:302-305).

B0/current fixed policy: p >= 0.98 MATCH; 0.95 <= p < 0.98 REVIEW; p < 0.95 NO_MATCH (manual_decision, lines 260-264).

B3/current GA policy: genome [t_match,t_review,c_promote,c_demote]. p >= t_match -> MATCH; p < t_review -> NO_MATCH; in the band, name_sim >= c_promote -> MATCH, name_sim < c_demote -> NO_MATCH, otherwise REVIEW (exp_r1_ga_redecision.py:69-78). Bounds are t_match [0.90,0.999], t_review [0.50,t_match], c_promote [0.50,1], c_demote [0,c_promote].

Current optimization: five GA seeds, population 60, 40 generations, elite 12, uniform crossover, Gaussian mutation sigma .02 with per-gene probability .30. Selection is minimum validation cost with seed tie-break (run_gb_transformer_experiments.py:376-469). The effective evaluation budget is 5 x 60 x 40 = 12,000 population fitness evaluations per outer split, subject to the implementation's initial-population/generation accounting being declared consistently.

Why F1 0.8280 -> 0.8604 is confounded:
- B0 uses inherited thresholds and no validation tuning.
- B3 uses a four-parameter policy family unavailable to B0.
- B3 selects those parameters on GA-validation labels.
- B3 also uses an optimizer whose stochastic search may or may not be better than another search at the same budget.
- The reported improvement therefore combines policy tuning, expanded policy expressivity, and optimizer choice. It does not identify a GA-specific effect.

5. Controlled B0/B1/B2/B3 design

All four methods must use the same outer split, candidate rows, feature rows, GB-18 classifier, calibrated probabilities, validation role, objective U = 2FP + FN + 0.1REVIEW, constraints, and sealed test. Only policy family/search method may differ.

B0 — fixed policy
Policy [0.98, 0.95] with no validation tuning. Evaluate once on sealed test.

B1 — tuned simple policy
Same two-threshold family as B0: MATCH if p >= t_match, REVIEW if t_review <= p < t_match, else NO_MATCH. Search only [t_match,t_review] on policy-validation entities. This isolates the value of validation tuning within the simple policy class. Use the same feasible probability bounds and objective; declare the search method and budget.

B2 — expanded policy plus non-GA search
Use exactly [t_match,t_review,c_promote,c_demote] and exactly the same decision rule and bounds as B3. Use deterministic Sobol quasi-random search as the primary non-GA baseline. Sobol is preferable to an arbitrary grid because the four-dimensional bounded space includes continuous thresholds, a grid suffers from resolution/curse-of-dimensionality trade-offs, and Sobol gives reproducible space-filling coverage without Bayesian model assumptions or a tuned acquisition function.

B3 — expanded policy plus GA
Use the existing GA rule, bounds, and implementation, but freeze its budget and random-seed protocol before execution.

Interpretation:
B0 -> B1 = tuning effect;
B1 -> B2 = additional policy-class effect plus any search-method difference, so the B1/B2 comparison must be described as expansion under controlled search budget, not a pure mathematical class effect unless B1 is also searched with the same non-GA engine;
B2 -> B3 = optimizer effect, because policy class, objective, data, and budget are held constant.

For the cleanest decomposition, run B1 with the same Sobol engine and budget as B2 restricted to two dimensions, while retaining B0 as the untuned reference. Then B0->B1 is tuning, B1->B2 is policy-class expansion, and B2->B3 is optimizer choice.

6. Recommended optimizer and fair budget

Primary non-GA optimizer: deterministic Sobol quasi-random search, with a fixed predeclared point sequence and explicit feasibility filtering. It is transparent, reproducible, derivative-free, and appropriate for a four-dimensional bounded policy space with piecewise-constant objective values.

Budget: count one policy objective evaluation for every candidate parameter vector evaluated on all policy-validation rows. Set B2 to exactly 12,000 feasible Sobol points per outer split, matching the GA's declared 60 x 40 = 12,000 population evaluations. If the GA implementation evaluates an initial population plus 40 subsequent populations, use the measured count from instrumented code and allocate exactly that same count to Sobol; publish both requested and realized counts. Do not count model fitting or probability generation in this policy-search budget because those are shared and frozen. Use one fixed Sobol seed/direction-number specification, and report whether infeasible draws are discarded or projected; preferably generate directly in the feasible transformed domain.

B3 may retain the five independent GA seeds for optimizer variability, but each GA seed must receive the same realized evaluation budget as B2. Report per-seed results and predeclare selection across seeds. Do not choose the Sobol budget after seeing which budget makes GA win.

7. Claims under possible outcomes

Scenario A: B3 clearly outperforms B2 across repeated outer splits.
Allowed: the GA policy optimizer provides incremental value over a same-class, same-budget Sobol search under this declared utility and corpus. Still do not claim universal GA superiority, business benefit, or algorithmic novelty without broader evidence.

Scenario B: B2 and B3 are effectively similar.
Allowed: validation-selected expanded three-way policy class improves the operating trade-off; GA is one implementation mechanism. Remove any claim that GA itself caused the improvement or is necessary.

Scenario C: B2 outperforms B3.
Required: remove GA as the main contribution and reframe around three-way decision-policy optimization and controlled entity-disjoint evaluation. GA can be reported as a weaker optimizer in this setting.

8. Provenance root cause

The current chain and status are:

raw/public source -> local transformed profiles -> candidate generation -> pair table -> name/hand-feature cache -> MiniLM cache -> GB training -> isotonic calibration -> policy selection -> sealed evaluation -> metrics.

Known hashes from the current audit:
- normalized_profiles_with_profile_id.csv SHA-256 17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1.
- experiments/scored_pairs_enriched.parquet SHA-256 396884be39c3aca894df8db56115dbe78b45694737dcb04fb3190974a5f53801.
- experiments/pair_features17.parquet SHA-256 215d2a1ee5464f4c11774052ef5510451a2f49d7bda4ec40435dae10f870d591.
- experiments/pair_bert_cos.parquet SHA-256 687e93cb46b12df3ae47b26f2eeaafafcf16f6a566146e3d5198d4cefeef97b7.
- exp_lib.py SHA-256 984adb9cf584210f5c2cbbae15062346388211df4812f0f32f91dcfd0f661db4.
- exp_r2_bert_feature.py SHA-256 98da5cb8b2d976bb021f03a593b64f9ca0b36451656fc3c6b2c262ebfef9d698.
- run_gb_transformer_experiments.py SHA-256 52b1aedaf9096e754a4e5dd12290cb91c228659aede48a3cf41ec6ceaef6b3a5.
- exp_r1_ga_redecision.py SHA-256 b6dc3eede40e33e8fea65ef4ea49d5ac3f05c0ab7a6d6ad1fae8ef36c14b8c23.
- authoritative run driver SHA-256 5d3138c92019ab667c7e7ef580b4adf5cf6c6e57285262b0e4f51294e8386ceb.

The v1 internal package has a 93-file SHA256SUMS.txt and records commit 1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b. That closes package-internal outputs, not the full input chain.

Missing links:
- raw public source file-level hash and exact acquisition snapshot;
- transformation script/config from raw repository to normalized_profiles_with_profile_id.csv;
- full source hash and model/config/labels/splits for the predecessor score at exp_lib.py:19; the referenced match_decisions.parquet is absent;
- exact feature-cache generation run metadata, environment, and upstream source hashes;
- MiniLM model revision/download hash and embedding-generation configuration;
- complete external input hashes in the v1 package (the package hashes outputs and internal scripts but does not close every upstream cache dependency);
- exact command line and environment for historical sealed decisions and some analysis exports;
- v1 repeated-outer package does not independently close all source/input/environment hashes for the historical family;
- license/ethics/collection evidence.

Cache disposition:
- experiments/scored_pairs_enriched.parquet: REGENERATE + HASH; it contains gated name_sim and labels.
- experiments/pair_features17.parquet: REGENERATE + HASH; required after uncensored name_sim correction.
- experiments/pair_bert_cos.parquet: KEEP only if regenerated or independently tied to the exact v2 candidate keys, MiniLM revision, and profile input hash; otherwise REGENERATE + HASH.
- stage15 match_decisions predecessor output: REMOVE from v2 numerical dependency unless its model, labels, splits, and source are fully recovered; currently UNVERIFIABLE HISTORICAL.
- v1 GB models, probabilities, decisions, summaries, and GA trials: KEEP as historical audit evidence, but exclude from v2 numerical evidence.
- v1 blocking/candidate artifacts: candidate counts can remain descriptive/frozen only if rebuilt input identity is verified; do not reuse them as v2 evidence after feature/policy correction without key/hash checks.

9. Dataset licensing and ethics

KNOWN / VERIFIED:
- Source repository: https://github.com/vishalshar/Dataset-LinkSocial.
- README identifies Sharma and Dyreson, “LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms,” IEEE ICBK 2018, IEEE record 8588801.
- Repository contains the three corresponding raw-profile directory names.
- Public README counts are 10,958 Instagram, 13,961 Twitter, and 11,892 Google+; local derivative counts are 10,957, 13,960, and 11,890 after filtering.
- Fields include usernames, biographies, full names, external URLs, bi-grams, and profile-picture URLs for some platforms.
- Local labels use shared entity folders/identifiers consistent with the repository layout.

UNKNOWN / NOT DOCUMENTED:
- original author-to-project permission beyond the repository's citation request;
- formal license, SPDX identifier, or machine-readable reuse terms;
- redistribution permission;
- complete collection methodology, crawler code, and collection date;
- platform Terms-of-Service compliance;
- informed consent, notification, opt-out, or data-subject process;
- ethics review/IRB approval;
- whether all personal fields were lawfully collected and may be redistributed.

NOT FOUND in the verified audit: LICENSE file, GitHub license metadata, explicit redistribution permission, formal consent statement, IRB statement, collection-period statement, or platform-ToS compliance statement.

Safe paper statement: use a locally transformed derivative of the public LinkSocial corpus, cite the original authors, state that no machine-readable reuse license or formal ethics documentation was found, do not imply public availability grants redistribution rights, and limit released materials to code where permitted, configuration, hashes, aggregate results, and non-identifying error categories.

Safe data-release boundary: do not release raw names, usernames, biographies, locations, URLs, image URLs/images, user_folder/entity identifiers, pair identifiers, raw profile records, or raw decision files. Obtain written maintainer permission and check ICSEC artifact/data policy before releasing any data-derived rows or caches.

10. Impact on current authoritative results

- name_sim correction: FULL AUTHORITATIVE RERUN for GB-17, GB-18, calibration, policies, and metrics. Candidate-generation counts can remain frozen only as a separately scoped retrieval result if the exact candidate input and hashes remain unchanged; the corrected feature/model evidence must use regenerated pair-key-aligned caches.
- physical test-label isolation: FULL AUTHORITATIVE RERUN of evaluation evidence. A post-hoc code audit cannot make already-resident labels physically sealed, and current test constants were read pre-final.
- B0/B1/B2/B3: new complete repeated-outer run for all three required seeds 101, 202, 303. Retrain/recalibrate only if the corrected feature cache changes model input; in practice it does.
- dataset profile counts and candidate counts: potentially KEEP as frozen descriptive retrieval evidence, but verify valid-ID eligibility and source hashes in v2. Do not silently combine them with new model metrics.
- existing references: bibliography entries can remain provisionally; claims relying on related work or dataset provenance must be rechecked against the corrected story. References do not require experimental rerun.
- existing figures: may be reused only conceptually as design sketches after visual/claim review; numerical figures and any feature-dependent plot must be regenerated. No existing numerical figure is cleared as v2 evidence.
- current v1 repeated-outer metrics: suspend for the main claim because feature construction and label-sealing evidence fail, even though row-level arithmetic is internally consistent.
- retrieval aggregates 36,807 input rows versus 36,804 eligible rows, 449,149,239 possible cross-platform pairs, 2,086,245 workflow candidates, 29,243 cross-platform positives, 25,931 covered positives, 3,312 misses, 88.6742% retrieval recall, and 99.5355% reduction can remain audit facts with explicit scope and eligibility wording, subject to v2 hash confirmation.

11. Authoritative_run_v2 design (design only; do not execute yet)

Directory: experiments/icsec_final/authoritative_run_v2/

Pre-execution files:
- PROTOCOL.md frozen and hash-recorded before data/model execution;
- environment/package lock and source manifest;
- raw-source manifest and transformed-profile manifest;
- candidate-generation config and candidate/exact/blocking-miss key manifests;
- split manifest for outer seeds 101, 202, 303 with hashed entity keys and zero-overlap assertions;
- explicit label-access policy and read instrumentation;
- predeclared B0/B1/B2/B3 search configuration and budgets.

Workflow for each outer seed:
1. Load eligible profile rows and public-source derivative metadata. Keep raw labels in a physically separate sealed-label input.
2. Rebuild cross-platform exact, candidate, and blocking-missed sets from the authoritative transformed input. Persist pair-key manifests and SHA-256 hashes.
3. Recompute all name features unconditionally from the documented raw fields. Persist an uncensored name_sim column and all 17-feature rows keyed by pair. Do not use predecessor scores.
4. Recompute MiniLM embeddings/cosines with pinned model revision and hash. Persist only non-identifying pair keys/features in the numerical package.
5. Assign entities to TRAIN, CALIBRATION, POLICY_VALIDATION, SEALED_TEST using outer seed 101/202/303 and entity_nested_v2. Assert zero entity overlap. Drop cross-role pairs.
6. Fit the same GB configuration on TRAIN only; deterministic 3:1 negative sampling remains unless the corrected feature protocol explicitly requires a predeclared change.
7. Fit isotonic calibration on CALIBRATION only.
8. Produce probabilities for all role rows without loading sealed labels.
9. Select B1 and B2/B3 policies using POLICY_VALIDATION labels only. B0 is fixed. Use Sobol B1/B2 and GA B3 with equal realized policy-evaluation budgets.
10. Before final evaluation, assert no test-label file handle/read, no test-label column in working frames, and no test-derived constants. Log every label access with role and function.
11. Final evaluator alone opens the sealed-test label artifact, joins labels by pair key, and evaluates B0/B1/B2/B3 exactly once per method. Add exact-tier and blocking-missed rows only in this final evaluator.
12. Persist separate exact-tier, model-scored, blocking-missed, and complete-workflow decisions for each method. Include TP, FP, FN, positive REVIEW, REVIEW total, precision, recall, F1, and U. Assert exact + scored + misses equals workflow and confusion identities.
13. Recompute metrics independently from row artifacts in a separate evaluator process/module. Compare outputs byte/row-key-wise to runner results.
14. Capture source, input, model, cache, split, environment, configuration, and output SHA-256 manifests after all files exist; verify the final manifest after any report generation.
15. Write AUTHORITATIVE_RESULTS.md only after all checks pass. Mark all v1 artifacts historical and excluded from v2 evidence.

Required roles exactly: TRAIN, CALIBRATION, POLICY_VALIDATION, SEALED_TEST. Required seeds exactly: 101, 202, 303. Test labels must not be loaded before final evaluation. Same classifier configuration and calibration approach are retained unless uncensored features force a declared model-input update.

12. Scientifically defensible paper story

Current ranking:
1. Story 2 — Validation-selected three-way policy optimization improves the operating trade-off; GA is one optimization mechanism, not yet shown to be the source of improvement. This is the strongest likely story after B0-B3.
2. Story 3 — Entity-disjoint evaluation of three-way operational decision policies, with no GA-specific performance claim. This is the safest fallback if B2 matches or beats B3, or if optimizer evidence remains weak.
3. Story 1 — GA provides additional value beyond tuning and policy-class expansion. Currently unsupported. It becomes defensible only if B3 consistently beats B2 across repeated outer splits under equal, predeclared budgets and corrected features/labels.

The paper should describe the problem first as cross-platform pair-level profile identity resolution and a three-way operational decision layer. It should not present an agentic CRM deployment, lead scoring, human review study, or business-cost result that was not evaluated.

13. Title decision

REVISE.

Provisional titles:
1. Three-Way Decision Policy Optimization for Cross-Platform Profile Identity Resolution
2. Entity-Disjoint Evaluation of Three-Way Policies for Cross-Platform Profile Matching
3. From Candidate Retrieval to Three-Way Decisions in Cross-Platform Profile Identity Resolution

The current title foregrounds Genetic Optimization without an identified GA effect and foregrounds an Agentic CRM platform that was not evaluated as a deployed system.

14. Paper V2 recommendation

WRITE PAPER V2 FROM BLANK IEEE STRUCTURE rather than patching the historical manuscript. The current manuscript contains historical framing and was written around claims now blocked by name_sim semantics, label availability, and GA identifiability. A clean structure is recommended:

1. Introduction
2. Related Work
3. System / Decision Pipeline Overview
4. Methodology
5. Leakage-Safe Experimental Design
6. Results and Discussion
7. Limitations / Threats to Validity
8. Conclusion

Use internal model names only after explaining the problem and pipeline. Do not write V2 until the v2 experiment is complete, independently reconciled, and provenance-closed.

15. Current status and action gate

No authoritative v2 run should start until this report's protocol decisions are frozen and the label-access design is implemented in a new directory. No manuscript file or existing authoritative artifact was modified by this audit.

RESEARCH DESIGN STATUS:
CORRECTABLE

NAME_SIM ISSUE:
CONFOUND

TEST LABEL STATUS:
PRE-EVALUATION ACCESS

RERUN REQUIRED:
FULL

GA-SPECIFIC CLAIM CURRENTLY SUPPORTED:
NO

CURRENT TITLE STATUS:
REVISE

SAFE TO RUN AUTHORITATIVE_V2:
NO

SAFE TO WRITE PAPER V2:
NO

NEXT ACTION:
Freeze and implement the leakage-safe authoritative_run_v2 protocol with uncensored name_sim and equal-budget B0/B1/B2/B3 definitions before any rerun or manuscript rewrite.
