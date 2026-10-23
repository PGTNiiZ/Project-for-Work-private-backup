# Gate 9 — Master Protocol v1 (DRAFT; NOT APPROVED)

**Status:** working draft for scientific-owner review. No execution authorization. Prepared against base `1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b` on `research/phase15-protocol`. The requested canonical primary-protocol and Phase 1 docs were not present at that base; see `PROTOCOL_OPEN_DECISIONS.md`. This document does not supersede them.

## Scope and vocabulary

Unit: **profile pair** (unordered pair of distinct profiles, keyed by stable pair ID); label: same `user_folder` = positive, otherwise negative. A **candidate pair** is emitted by blocking; a **blocking miss** is a positive pair never scored. **Entity** means `user_folder`; splits must keep an entity wholly within one role. Roles: **train**, **calibration**, **validation**, **test**. Model outputs are **probabilities**; policy outputs are **MATCH**, **REVIEW**, **NO_MATCH**. A **run seed** identifies stochastic training/policy-search randomness; a **split seed** identifies a partition. These terms are proposed pending Gate 4–7 contracts.

## A–F controlled-protocol stages (draft; not experiment arms)

A–F name protocol stages, consistent with the task; they are not six distinct experiment arms. They do not override the reference plan's A–I implementation sequence; the scientific owner must approve this mapping before freezing.

| Stage | Required work | Current disposition |
|---|---|---|
| A — Data Foundation | Approve normalized snapshot, profile/entity mapping, exclusions, labels, schema and hashes; raw-to-result reproduction remains distinct. | Requires Gates 1–3 evidence records and owner confirmation. |
| B — Candidate Retrieval | C0 historical exact username/URL plus prefix blocking. C1 is the union of C0 and top-k lexical character-ngram TF-IDF candidates; fit vocabulary/IDF on TRAIN only, transform other roles, and use k∈{10,20,50} per query/target-platform (primary workflow k=20). Candidate generation is label-free and unordered pair keys are deduplicated. | Specification only; no retrieval executed. |
| C — Entity Split | Gate 5 proposal: five entity folds, seed 20261010; for outer fold i, TEST=i, CALIBRATION=(i+1)%5, POLICY_VALIDATION=(i+2)%5, TRAIN=remaining two folds. Exclude and count pairs crossing roles. | Awaiting tested Gate 5 contract and population sufficiency. |
| D — Scorer Experiments | E1 Logistic Regression + corrected 17 features; E2 Gradient Boosting + same 17; E3 Gradient Boosting + same 17 plus MiniLM cosine. E2/E3 differ by exactly one column. TRAIN negative:positive sampling 3:1 if feasible, same sampled pair keys for the E2/E3 feature comparison. | No models trained. |
| E — Calibration and Policy Experiments | Compare isotonic and sigmoid; select calibrator by POLICY_VALIDATION Brier per proposal. Compare policies P0 fixed historical thresholds, P1 Chow risk, P2 exact simple two-threshold optimum, P3 random, P4 scrambled Sobol, P5 GA. | Costs, selection hierarchy and all policy contracts require owner decision. |
| F — Freeze and Evaluation | Freeze protocol/config/model/calibrator/policy/prediction hashes; only then controlled evaluator joins TEST labels; independently recompute per-fold metrics and paired comparisons. | Not run; TEST labels not accessed. |

## Proposed common split and population contract

Use five outer entity folds with seed `20261010`, stratified approximately by each entity's observed platform-pattern signature, with deterministic allocation and no label-dependent balancing. For outer fold `i`, the fixed rotating mapping is exactly TEST=`i`, CALIBRATION=`(i+1) mod 5`, POLICY_VALIDATION=`(i+2) mod 5`, TRAIN=the remaining two folds. Roles therefore approximate 40/20/20/20 only if outer folds are adequately balanced. All profiles inherit their entity role. Retain a pair only if both endpoint entities share one role; otherwise exclude it and record the cross-role count by role/source/pair type. Fit learned preprocessing on TRAIN only; fit calibrators on CALIBRATION only; select scorers/policies only using predeclared development rules; freeze before TEST prediction/evaluation. No test outcome data may enter feature generation, candidate generation, training, calibration, or policy selection. This is programmatic isolation on a historically explored corpus, not external validation or security-grade blinding.

The main plan has A–I implementation stages (`docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:166–180`); this document maps requested A–F to protocol stages only, not six newly invented experiment treatments. The research owner must confirm this interpretation and reconcile versioning before freeze.

## Calibration and policies

Fit the scorer on TRAIN only. Compare isotonic and sigmoid calibration fit on CALIBRATION; the proposed calibrator-selection metric is Brier on POLICY_VALIDATION, while acknowledging that subsequent policy selection on the same role adaptively reuses POLICY_VALIDATION. Record both fits, Brier, selection rule, and reuse limitation; no TEST-based selection. Before freeze, the scientific owner must approve minimum support and decide whether calibrator and scorer selection can share POLICY_VALIDATION or require a nested design.

Policy ladder, using the task's labels:

- P0: historical fixed thresholds (candidate .98/.95; confirm the mapping to MATCH/REVIEW/NO_MATCH).
- P1: Chow direct posterior-risk decision under the approved cost matrix.
- P2: exact simple two-threshold optimum at unique calibrated-score breakpoints, including all-MATCH, all-NO_MATCH, and no-REVIEW cases.
- P3: expanded policy searched by random sampling.
- P4: expanded policy searched by scrambled Sobol.
- P5: expanded policy searched by GA.

The expanded P3–P5 policy family, bounds, gate-off behavior, tie order, missing-name behavior, incumbent initialization, duplicate-proposal accounting, and exact-tier override authority must be identical where methods are compared and frozen before search. Proposed costs are FN=1, FP∈{1,2,5}, REVIEW∈{.05,.1,.2} (nine scenarios); select a policy separately on POLICY_VALIDATION for each scenario, and freeze all nine before TEST. Optimizer seeds: 101, 202, 303, 404, 505. Budget: 2,048 actual objective calls per method/seed/fold/cost, checkpoints 128/512/2,048. GA proposal: population 60, elite 12, uniform crossover per gene, Gaussian mutation σ=.02, mutation probability .30 per gene. The stated aggregate 1,382,400 calls is planned work, not completed execution. Require a development-only runtime pilot after authorization; no such pilot is run here. Equalize actual objective-call and elapsed-time budgets and test whether P2's incumbent is feasible and decision-equivalent across random/Sobol/GA.

All these are proposal values and remain subject to owner approval. In particular, exact threshold semantics and whether C1 workflow comparison retrains the scorer under C1 remain explicit open decisions.

## Outcomes and statistical plan (proposal)

Primary workflow outcomes: TP, FP, FN, positive REVIEW, total REVIEW; precision, recall, F1; end-to-end recall `TP/(TP+FN+positive_REVIEW)` and F1 `2TP/(2TP+FP+FN+positive_REVIEW)`; candidate coverage, blocking recall/misses, and cost decomposed by action and label. Include exact-tier and blocking-miss constants in workflow totals and state their provenance. Secondary: PR-AUC/ROC-AUC on scored pairs, Brier/log loss, calibration, review burden, per-platform-pair and evidence-availability slices. No single aggregate may hide a changed denominator.

Primary comparisons are paired per outer fold, with counts/support, paired differences, and cost sensitivity for every fold. Report variation across folds separately from the distribution of the five optimizer seeds within each fold; the 25 fold×optimizer runs are not 25 independent datasets. Report mean/SD and median/range only with the unit named, and make the small-fold/support limitation explicit. Do not infer equivalence from a null result or claim GA superiority from a tiny mean gain. Predeclare one primary contrast, multiplicity handling, uncertainty method and practical margin before TEST access; if no defensible entity/query-level uncertainty method is approved, provide paired fold results and state that inferential precision is limited. Keep conditional pair-model metrics separate from automatic workflow metrics.

## Compute, budget, reproducibility

Draft search budget is **2,048 actual objective calls** per method/optimizer seed/outer fold/cost scenario, with checkpoints 128, 512 and 2,048; include initialization and duplicate proposals in actual call counts. Optimizer seeds are 101, 202, 303, 404, 505. GA proposal: population 60, elite 12, uniform crossover per gene, Gaussian mutation σ=.02, mutation probability .30 per gene. The planned total 1,382,400 objective calls is not completed work. Cost scenarios are FN=1, FP∈{1,2,5}, REVIEW∈{.05,.1,.2}; policies are reselected on POLICY_VALIDATION and frozen across all nine scenarios before TEST. Compare objective-call and elapsed-time budgets fairly. A development-only runtime pilot is required after authorization, not part of this audit. Freeze model seeds and all remaining compute limits before any authorized execution. No training, tuning, calibration, policy optimization, or test evaluation is authorized by this draft.

## Limitations and stop conditions

Blocking places an upper bound on workflow recall; policy optimization cannot recover unscored positive pairs. Entity-disjoint splits can discard cross-role negative pairs and alter the evaluation population. Labels based on `user_folder` may encode dataset-specific identity quality. Historical plans contain differing denominators, split logic, costs, and thresholds; do not combine their results. One corpus does not establish external generalization. The proposed MiniLM and lexical-retrieval components require frozen source, cache, preprocessing and encoder lineage. Data-use, privacy, legal and ethics decisions remain outside technical approval. Stop if Gate 4–7 contracts conflict, test labels are accessible during selection, pair/entity leakage occurs, budget or data provenance is unresolved, or the evaluator cannot reconcile exact-tier + scored + blocking-miss scopes.

**Approval required:** scientific owner must resolve all items in `PROTOCOL_OPEN_DECISIONS.md`, approve the canonical input protocol, and sign a frozen successor before any experiment.