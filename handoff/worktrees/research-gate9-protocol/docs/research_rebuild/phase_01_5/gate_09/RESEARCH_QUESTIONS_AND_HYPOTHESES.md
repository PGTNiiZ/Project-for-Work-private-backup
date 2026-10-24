# Research Questions & Hypotheses — Gate 9 draft

**Not approved; hypotheses are proposals, not established claims.** Shared unit is an eligible profile pair keyed by a canonical unordered `pair_key`; profile-row IDs are distinct from `entity_id` (proposed mapping derives from `user_folder`, awaiting Gate 1–3 evidence). Roles are TRAIN/CALIBRATION/POLICY_VALIDATION/TEST; decisions are MATCH/REVIEW/NO_MATCH. See master draft and open decisions.

## Questions and falsifiable hypotheses

1. **Q1 — Scorer/representation (Stage D: E1–E3):** Does Gradient Boosting with 18 corrected features, including MiniLM cosine, differ from the matched 17-feature Gradient Boosting model on the same entity split, pair population and TRAIN keys? Compare E2 vs E3; E1 Logistic Regression + 17 features is a model-family baseline. H1: E3 improves prespecified discrimination/calibration/workflow outcomes; do not assert direction before evidence.
2. **Q2 — Calibration:** Does a separately fit calibration map improve probability reliability without materially degrading discrimination? H2: calibration reduces validation-selected calibration error and does not use test labels. Test reliability is descriptive after freeze, not a selection target.
3. **Q3 — Decision policy (Stage E: P0–P2 versus P3–P5):** Do expanded policies improve declared workflow utility or review burden relative to fixed, Chow and exact simple-threshold baselines at fixed costs? Select only on POLICY_VALIDATION; compare automatic and conditional outcomes separately. Hypothesis direction and practical margin require owner approval.
4. **Q4 — Optimizer attribution (Stage E: P3 random, P4 scrambled Sobol, P5 GA):** Does GA outperform relevant search baselines when predictor, expanded policy class, bounds, initialization, objective, evaluation budget and role population are identical? Report actual calls/time and optimizer variation; do not treat optimizer repetitions as independent datasets.
5. **Q5 — Retrieval/workflow impact:** What recall–candidate-budget trade-off does C1 provide over C0 on the same role-specific eligible population, and how many blocking misses are recovered? This remains separate from optimizer comparisons and must not use TEST labels for selecting retrieval k.
6. **Q6 — Workflow ceiling:** How much error is due to blocking misses versus scored-pair decisions? Report blocking recall and fixed misses separately; no policy claim may imply recovery of unscored positives.

## Estimands and analysis

Primary estimand must be chosen by the scientific owner: proposed candidate is paired difference in end-to-end F1 or declared workflow loss on entity-held-out test data. Secondary estimands: candidate-pair PR-AUC, calibration scores, action counts, positive-review-inclusive end-to-end recall/F1, coverage, and per-platform-pair outcomes. Contrast methods on identical held-out entity populations; use paired entity-cluster bootstrap, report 95% interval and each outer split. Conditional exact-tier/blocking constants must be disclosed. Resolve multiplicity and practical-equivalence margins before test access.

No hypothesis is confirmed by the historical R0–R6 or other persisted result files. They may differ in source, data, split, policy, or denominator and are context only until lineage reconciliation.