# ICSEC Primary Research Protocol

## Frozen research direction

**Cost-sensitive genetic optimization of a three-way decision policy for cross-platform profile identity resolution.**

This protocol defines the only primary experimental family for the manuscript: `GB-17`, `GB-18`, and `GB-18-GA`. Historical R0–R6 results are not part of the primary ablation table because their data splits, feature construction, model family, or evaluation scope differ. They may be mentioned only as explicitly non-comparable exploratory context.

## Research problem and scope

Given candidate pairs of profiles from Twitter, Google+, and Instagram, determine whether a pair is the same entity while assigning one of three operational decisions: `MATCH`, `REVIEW`, or `NO_MATCH`. The study measures offline decisions against labels derived from the shared `user_folder` entity identifier. It does not evaluate deployment, analyst behavior, CRM conversion, or privacy guarantees.

## Dataset and label construction

- Input profile file: `data_for_project/normalized_profiles_with_profile_id.csv`.
- Eligible profiles: rows with valid `profile_row_id`; the primary run records the input SHA-256 in its configuration.
- Platforms: Twitter, Google+, Instagram.
- Positive pair label: the two profile rows have the same non-empty `user_folder`.
- Candidate pairs are inherited from `experiments/scored_pairs_enriched.parquet`; exact-tier and blocking-missed constants are incorporated by the evaluation harness.
- Dataset provenance, license, collection date, and terms of use are not established by this protocol and remain `[DATASET PROVENANCE REQUIRES VERIFICATION]`.

## Entity-disjoint nested split

The split is implemented by `experiments/code/exp_lib.py:build_nested_entity_split` using `entity_nested_v1` and seed 42.

1. The pre-existing outer split reserves entities whose deterministic hash assigns them to `test`.
2. For non-test entities, a deterministic MD5 bucket allocates entities to:
   - `model_train`: 70%
   - `model_calibration`: 15%
   - `ga_validation`: 15%
3. Candidate pairs with endpoints in different roles are assigned `drop` and excluded.
4. The implementation asserts no entity overlap between model training, calibration, GA validation, and test roles.

Historical primary-run counts:

| Role | Candidate pairs | Entities |
|---|---:|---:|
| model_train | 510,981 | 7,413 |
| model_calibration | 26,246 | 1,606 |
| ga_validation | 22,873 | 1,510 |
| test | 195,440 | 4,554 |
| drop | 1,330,705 | — |

## Features and model variants

### GB-17: handcrafted feature baseline

A `sklearn.ensemble.GradientBoostingClassifier` is fitted using 17 handcrafted pair features:

- username Jaro, normalized Levenshtein similarity, token-sort similarity
- full-name Jaro, normalized Levenshtein similarity, token-sort similarity
- maximum cross-field name similarity
- bio Jaccard, bio-length ratio, both-bios-present indicator
- location Jaro, exact-location indicator, both-locations-present indicator
- same-platform indicator
- username-length difference, full-name word-count difference, username-prefix agreement

### GB-18: semantic representation ablation

GB-18 uses exactly the GB-17 feature set plus one feature: `bert_cos`, the cosine similarity of normalized `all-MiniLM-L6-v2` embeddings of concatenated full name, bio, and location.

The identical sampled training pair hash, labels, model seed, and Gradient Boosting hyperparameters are asserted for GB-17 and GB-18. The intended isolated difference is only `bert_cos`.

### Model and calibration settings

- Classifier: `GradientBoostingClassifier`
- `n_estimators=300`
- `learning_rate=0.05`
- `max_depth=6`
- `random_state=42`
- Negative undersampling on model-training data: ratio 3.0 negatives per positive.
- Probability calibration: `IsotonicRegression(out_of_bounds="clip")`, fitted only on `model_calibration` entities.
- Manual operational baseline thresholds: `MATCH >= 0.98`, `REVIEW >= 0.95`, otherwise `NO_MATCH`.

## GA decision policy: GB-18-GA

GB-18-GA uses the calibrated GB-18 probability artifact unchanged. It does not fit, update, or otherwise modify the Gradient Boosting classifier or its calibrator.

Genome: `[t_match, t_review, c_promote, c_demote]` with constraints:

- `0.90 <= t_match <= 0.999`
- `0.50 <= t_review <= t_match`
- `0.50 <= c_promote <= 1.0`
- `0 <= c_demote <= c_promote`

Decision rule for candidate pair `i`, probability `p_i`, and name evidence `n_i`:

- `MATCH` if `p_i >= t_match`.
- In the band `t_review <= p_i < t_match`, return `MATCH` if `n_i >= c_promote`.
- In the same band, return `NO_MATCH` if `n_i < c_demote`.
- Otherwise return `REVIEW`.
- Return `NO_MATCH` if `p_i < t_review`.

GA configuration:

- Seeds: 7, 42, 123, 999, 2025
- Population: 60
- Generations: 40
- Elites: 12
- Uniform crossover
- Gaussian mutation with probability 0.30 and standard deviation 0.02
- Selection: lowest validation weighted decision cost; ties: smallest seed.

## Cost objective and its status

The reproduced ICSEC run uses the shared code's `crm_derived_v1` objective:

`cost = 2.0 * FP + 1.0 * FN + 0.1 * REVIEW`.

A pre-existing historical GB-primary artifact records a different GA weight vector (`5.0, 1.0, 0.02`), so that historical artifact is not used as the primary result source. The ICSEC reproduction is the frozen source of primary results.

Repository documentation describes the weights as CRM-derived normalization but no measured timing study, expert elicitation protocol, or external citation was found. Therefore the reproduced cost configuration is an engineering assumption, not a validated business cost. The ICSEC paper must report it as such and include sensitivity analysis rather than claim measured business impact.

## Test-label isolation

`run_gb_transformer_experiments.py` constructs features, fits models, calibrates probabilities, runs all GA seeds, and selects a genome without requesting test labels. Test labels are requested only at the final evaluation statement (`labels_for(..., "test", allow_test=True)`). Automated tests verify that changing GA-validation/test labels does not alter the fitted model or GA genome. The historical artifact also records `test_labels_accessed_before_final_evaluation: false` and `selected_ga_test_evaluations: 1`.

## Primary outcomes

For each method, report the same held-out-test quantities:

- TP, FP, FN, REVIEW
- precision, recall, F1
- weighted decision cost under declared cost scenarios

The evaluation harness includes exact-tier results and blocking-missed false negatives as fixed split-specific constants. These are workflow-level operational metrics, not ordinary binary classifier metrics.

## Reproduction outputs

The final reproducibility package is placed in `experiments/icsec_final/` without overwriting historical artifacts. It must include source/input hashes, configuration, split manifest, model artifacts, calibrated probabilities, per-pair decisions, raw metrics, bootstrap analysis, sensitivity analysis, error decomposition, and logs.
