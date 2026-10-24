ICSEC 2026 AUTHORITATIVE EXPERIMENT PROTOCOL
Version: authoritative_run_v1
Frozen before execution: 2026-09-03

Purpose

This package is the sole new numerical source for the ICSEC 2026 manuscript. Historical artifacts are comparison evidence only. The primary scientific scope is cross-platform identity resolution.

Dataset and preprocessing

- Dataset: data_for_project/normalized_profiles_with_profile_id.csv.
- Rows are loaded with keep_default_na=False.
- profile_row_id and profile_id are parsed numerically; only rows with both valid identifiers are eligible for candidate generation.
- platform, userName, fullName, bio, external-domain, and cleaned external URL fields are normalized using the current source implementation.
- No profile text, names, usernames, URLs, images, or other PII is exported in this package.

Labels and scope

- Positive label: two profiles have the same non-empty user_folder.
- TOTAL LABELED POSITIVES counts all unordered positive pairs, including same-platform pairs.
- CROSS-PLATFORM LABELED POSITIVES counts only positive pairs whose endpoint platforms differ.
- SAME-PLATFORM POSITIVES are the remainder and are excluded from the paper workflow.
- Candidate generation and all paper retrieval denominators are cross-platform only.

Candidate generation

The current source implementation is src/identity_resolution/workflows/full_candidate.py. It uses:

1. Exact username groups (normalized username length at least 3).
2. Exact cleaned external URL groups.
3. Blocking keys username_prefix3, fullname_prefix3, and external_domain.
4. Generic external domains are removed by the current implementation.
5. Same-platform pairs are excluded and duplicate pair keys are removed.
6. Exact-tier pairs are AUTO_EXACT and are not model scored.
7. All other retained workflow pairs are model-scored candidates.
8. Blocking-missed positives are positive cross-platform pairs absent from the workflow candidate set.

Features and models

- GB-17 uses the current 17-feature set: username_jaro, username_lev_sim, username_token_sort, fullname_jaro, fullname_lev_sim, fullname_token_sort, name_sim, bio_jaccard, bio_len_ratio, both_have_bio, location_jaro, location_exact, both_have_location, same_platform, username_len_diff, fullname_wordcount_diff, username_prefix3_match.
- GB-18 adds only bert_cos from the cached pair_bert_cos feature artifact, using the current frozen feature cache as an input artifact.
- Classifier: sklearn GradientBoostingClassifier.
- n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42.
- Negative undersampling: 3.0 negatives per positive on model-training rows.
- Calibration: sklearn IsotonicRegression(out_of_bounds='clip'), calibration entities only.

Decision policies

- Fixed policy: MATCH for probability >= 0.98; REVIEW for probability >= 0.95 and below MATCH; otherwise NO_MATCH.
- GA genome: [t_match, t_review, c_promote, c_demote].
- GA rule: probability >= t_match => MATCH; in [t_review,t_match), name_sim >= c_promote => MATCH, name_sim < c_demote => NO_MATCH, otherwise REVIEW; probability < t_review => NO_MATCH.
- Constraints: 0.90 <= t_match <= 0.999; 0.50 <= t_review <= t_match; 0.50 <= c_promote <= 1.0; 0 <= c_demote <= c_promote.
- GA population 60, generations 40, elites 12, uniform crossover, Gaussian mutation sigma 0.02 with per-gene probability 0.30.
- GA seeds: 7, 42, 123, 999, 2025.
- Frozen utility: U = 2*FP + FN + 0.1*REVIEW. It is illustrative, not measured economic cost.

Repeated outer evaluation

- Outer seeds: 101, 202, 303.
- For each seed, entities are assigned using the current deterministic outer hash procedure, with 30% sealed test and 70% development.
- Development entities are assigned by entity_nested_v1 to model_train 70%, model_calibration 15%, and GA validation 15%.
- Candidate pairs crossing roles are dropped.
- Zero entity overlap is asserted across training, calibration, GA validation, and sealed test.
- Models are fit on model_train only, calibrators on model_calibration only, and GA policy selection on GA validation only.
- Test labels are not read before final selected-policy evaluation. Each method is evaluated once on sealed test.

Evaluation artifacts and metrics

For each outer seed and method, separate non-identifying row-level artifacts are written for exact-tier decisions, model-scored decisions, blocking-missed positives, and complete workflow decisions. Complete workflow metrics are recomputed independently from these artifacts.

Metrics: TP, FP, FN, REVIEW, precision, recall, F1, and U. Precision is TP/(TP+FP); recall is TP/(TP+FN) over the complete workflow positive denominator; F1 is the harmonic mean of precision and recall; U is the frozen utility above. Mean and sample standard deviation (ddof=1) are reported over the three outer seeds.

No test performance, test labels, or post-hoc sensitivity result may alter these settings.
