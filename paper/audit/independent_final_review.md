# Independent Final IEEE/ICSEC 2026 Review

## Review scope and evidentiary basis

This is a read-only independent review of `paper/overleaf/main.tex` and `paper/overleaf/main.pdf`. The only experimental results treated as authoritative are those under `experiments/icsec_final/authoritative_run/`; historical experiment families were used only to trace implementation and provenance, not as evidence for manuscript results.

Checks completed:

- all 93 entries in the authoritative SHA-256 manifest verified;
- all nine method/outer-run metric rows were recomputed from workflow-level decision artifacts;
- the aggregate means and sample standard deviations were independently recomputed;
- the complete test suite passed: 45 tests;
- all five PDF pages and both figures were rendered and inspected;
- all 16 bibliography records and 28 citation occurrences were audited;
- protected manuscript, bibliography, figure, code, and experiment files were not modified.

## Independent reconstruction of the research

### Problem actually solved

The implemented system makes pair-level cross-platform profile-linkage decisions: given profiles from Twitter, Google+, and Instagram, it predicts whether two accounts correspond to the same source entity. It does not evaluate final customer entities, connected-component clustering, CRM agents, lead scoring, conversion, or business outcomes.

### Actual pipeline

1. Keep profiles with valid row and profile identifiers.
2. Restrict the universe to cross-platform pairs.
3. Automatically mark exact normalized-username or exact cleaned-external-URL pairs as MATCH.
4. Generate remaining candidates through username-prefix-3, full-name-prefix-3, or non-generic external-domain blocks.
5. Compute pair features and score model candidates with Gradient Boosting.
6. Fit an isotonic mapping on a separate calibration entity role.
7. Apply either fixed probability thresholds or a GA-selected four-parameter three-way policy.
8. Evaluate the complete workflow by combining exact-tier rows, model-scored rows, and blocking-missed positives, the last of which are entered as positive NO_MATCH decisions.

### GB-17 and GB-18

GB-17 contains 17 columns: three username similarities, three full-name similarities, `name_sim`, three biography/missingness features, three location/missingness features, `same_platform`, normalized username-length difference, normalized full-name word-count difference, and username-prefix-3 agreement. `same_platform` is constant zero in this cross-platform experiment.

The manuscript says `name_sim` is the maximum Jaro--Winkler similarity across username/full-name cross-field combinations. The current authoritative cache does not implement that feature for every scored pair: the historical cache builder computes it only when a predecessor score is at least 0.5 and leaves it at zero otherwise (`experiments/code/exp_lib.py:93-101`). This undocumented censoring affects both classifier input and GA promotion/demotion.

GB-18 adds one feature, `bert_cos`: cosine similarity between normalized `all-MiniLM-L6-v2` embeddings of concatenated full name, biography, and location. Empty concatenations map to the same `[empty]` text. The comparison is therefore a one-feature ablation, not a broad test of semantic entity matching.

### Classifier, calibration, and decisions

Both models use `GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42)`. Training negatives are deterministically undersampled at 3:1 relative to positives. Separate isotonic regressors with `out_of_bounds="clip"` are fitted on calibration entities. Calibration supplies a monotone probability-like decision scale; the paper does not establish calibrated probability quality because it reports no held-out Brier score, log loss, ECE, or reliability analysis.

The fixed policy is MATCH for `p >= 0.98`, REVIEW for `0.95 <= p < 0.98`, and NO_MATCH otherwise. REVIEW means unresolved offline deferral, not a completed human adjudication. Positive REVIEW rows remain in the recall denominator but are neither TP nor FN; FN means a positive row assigned NO_MATCH.

The GA genome is `[t_match, t_review, c_promote, c_demote]`. Above `t_match` a pair is MATCH. In the intermediate probability region, sufficiently high `name_sim` promotes it to MATCH, sufficiently low `name_sim` demotes it to NO_MATCH, and the remainder becomes REVIEW. Below `t_review` it is NO_MATCH. The GA optimizes only this downstream policy; it does not retrain or alter the classifier or calibrator.

The minimized objective is:

`U = 2 * FP + FN + 0.1 * REVIEW`.

This is an illustrative engineering scalarization, not measured economic, CRM, business, or operational cost.

### Evaluation protocol

For outer seeds 101, 202, and 303, entities are hashed into approximately 30% test and 70% development. Development entities are split 70/15/15 among model training, calibration, and GA validation. A pair is retained only if both endpoints have the same role; cross-role pairs are dropped. Entity overlap within each outer run is zero. Each run refits both classifiers and calibrators and reselects the GA.

The role structure is sound, but the stronger claim that test labels are “unavailable” before final evaluation is false. The candidate cache contains `actual` for all roles when loaded, and `constants()` directly reads test `actual` values before model fitting and GA selection (`run_authoritative_outer.py:44-48,62-80,117`). The audit wraps only one `labels_for` accessor, so its zero count proves no guarded accessor request, not genuine test-label isolation. No direct evidence shows that these labels changed the selected policy, but the manuscript overstates the protection. In addition, the same nominal outer-seed family existed in earlier experiments, so these partitions were not demonstrably epistemically unseen.

### Main limitations reconstructed independently

- one transformed historical corpus and three historical platforms;
- only three correlated repeated holdouts, with substantial test-entity reuse;
- no genuinely fresh confirmatory test partition;
- an undocumented predecessor-score gate in `name_sim`;
- incomplete source/input/cache/environment provenance and a heavily dirty/untracked repository state;
- candidate retrieval misses 3,312 cross-platform positives;
- cross-role dropping disproportionately removes negative pairs and changes the evaluation population;
- no fair validation-tuned non-GA policy baseline;
- no calibration-quality evaluation;
- no human-review outcome, review-capacity, or analyst study;
- no final entity-cluster or transitivity evaluation;
- no external, temporal, language, or platform transfer;
- unresolved dataset license, consent, and ethics documentation.

# A. Executive Summary

The manuscript is unusually transparent about the retrieval ceiling, the mixed MiniLM result, the GA trade-off, and the absence of downstream CRM evidence. Its authoritative row-level result artifacts are internally consistent, and the IEEE PDF is broadly compliant and anonymous. Those strengths do not overcome three blocking scientific problems. First, the central `name_sim` feature is materially different from its manuscript definition because it is censored by a predecessor score. Second, “sealed” test-label unavailability is not implemented or established, and the nominal test seeds had historical exposure. Third, the main comparison shows that a validation-selected richer policy outperforms inherited fixed thresholds under its own utility; it does not isolate the necessity or advantage of genetic optimization. A clean rerun with uncensored features, genuine label isolation, closed provenance, fresh partitions, and equally tuned non-GA baselines is required.

# B. Paper Story in One Paragraph

The paper studies a cross-platform profile-linkage workflow in which lexical/domain blocking retrieves candidate pairs, Gradient Boosting scores them using 17 handcrafted features with or without one MiniLM cosine, isotonic regression supplies a probability-like scale, and a downstream policy maps each pair to MATCH, REVIEW, or NO_MATCH. Under three entity-disjoint repeated holdouts, a GA-selected four-parameter policy applied to frozen GB-18 scores increases mean recall and F1 and reduces FN relative to fixed thresholds, while decreasing precision and increasing FP and REVIEW. The study also shows that candidate generation imposes an 88.6742% recall ceiling. This is an integration and operating-policy study, not an evaluation of Agentic CRM or a novel GA.

# C. Strongest Contribution

The strongest contribution is the retrieval-to-decision decomposition backed by complete row-level workflow artifacts. Exact-tier, model-scored, and blocking-missed scopes reconcile exactly; every reported workflow metric is reproducible from pair-keyed decisions. The manuscript also reports the GA’s adverse effects instead of implying universal improvement.

# D. Weakest Aspect

The weakest aspect is causal attribution to the GA. It is compared with inherited 0.98/0.95 thresholds, not a policy tuned on the same validation entities and objective. The GA also receives a richer four-parameter policy family. The evidence supports “this validation-selected policy beats these untuned fixed thresholds,” not “genetic optimization is necessary or superior.” The censored `name_sim` feature further compromises the central policy experiment.

# E. Title Assessment

TITLE: REVISE

“Cross-Platform Profile Identity Resolution” is supported. “Three-Way Decisions” accurately describes MATCH/REVIEW/NO_MATCH. “Genetic Optimization” describes the mechanism but foregrounds a conventional optimizer whose comparative necessity is not established. “for an Agentic CRM Platform” can lead readers to expect a deployed platform, agents, lead scoring, or business outcomes despite later disclaimers; it is application context only.

Preferred alternatives, in order:

1. “Three-Way Decision Policy Optimization for Cross-Platform Profile Identity Resolution”
2. “Entity-Disjoint Evaluation of Genetic Policy Selection for Cross-Platform Profile Matching”
3. “From Candidate Retrieval to Three-Way Decisions in Cross-Platform Profile Identity Resolution”

The title currently risks overstating both application scope and GA centrality, though it does not explicitly claim a novel GA.

# F. Abstract Assessment

ABSTRACT CLARITY: 4/5

ABSTRACT TECHNICAL ACCURACY: FAIL

ABSTRACT OVERCLAIM RISK: MEDIUM

The abstract clearly defines identity resolution, the score-to-action gap, the GA’s limited role, the experimental comparisons, all principal trade-offs, the retrieval ceiling, and the absence of downstream evaluation. Every numerical value and rounding in the abstract matches the authoritative artifacts. “Isotonic-calibrated” is somewhat technical before calibration is motivated, but it is not the main clarity problem.

The failure is the statement that the experiment uses “sealed testing” under disjoint roles. Entity disjointness is verified, but test labels are present and test-label-derived constants are read before final evaluation. The first Agentic CRM sentence is contextual rather than experimentally supported; the final limitation sentence appropriately prevents a direct outcome overclaim.

# G. Research Gap Assessment

The defensible gap is not a new GA, new ER model, new three-way decision theory, new calibration method, new blocker, new Gradient Boosting method, or new MiniLM method. The actual contribution is a controlled integration and evaluation of:

- a frozen calibrated profile matcher;
- validation-selected downstream three-way policy parameters;
- entity-role separation across training, calibration, policy selection, and test;
- workflow-level accounting that includes exact matches and retrieval misses;
- explicit reporting of FP/FN/REVIEW trade-offs.

Primary contribution classification:

- METHODOLOGICAL NOVELTY: limited/moderate;
- EXPERIMENTAL NOVELTY: limited/moderate;
- SYSTEMS / APPLICATION CONTRIBUTION: moderate, at pair-decision level only;
- INTEGRATION CONTRIBUTION: primary category;
- ALGORITHMIC NOVELTY: no.

Would a reviewer reasonably say “This is only standard techniques combined together”? Yes. This is a HIGH acceptance risk. The response cannot be rhetorical; the paper must demonstrate why the combination yields generalizable scientific knowledge. At present the GA is four-dimensional, its empirical objective is piecewise constant, selected genes repeatedly hit bounds, several distinct genomes produce identical decisions, and no equal-budget random, grid/breakpoint, coordinate, or deterministic search is evaluated. The evaluation protocol and error decomposition add value, but they do not establish an evolutionary-computing contribution.

# H. Novelty Assessment

Novelty is 2/5. The paper appropriately disclaims novelty for three-way ER and GA-based ER, which should not be weakened. Its narrow novelty lies in applying a GA to a frozen calibrated decision layer under four-role entity-disjoint evaluation and exposing the resulting operating trade-off. That is an integration contribution. A stronger claim would require fair optimizer baselines, policy-class ablations, analysis of decision-equivalent genomes, and preferably multiobjective/Pareto or constrained policy analysis.

# I. Methodology Assessment

## Source-code consistency

| Item | Manuscript | Repository | Match? |
|---|---|---|---|
| Candidate scope | Cross-platform only; valid identifiers | Valid IDs retained; same-platform pairs excluded | YES |
| Exact tier | Normalized username or cleaned external URL | Same; username length at least 3 | YES, manuscript should state length condition |
| Username-prefix block | First 3 normalized username characters | First 3 alphanumeric normalized characters | YES |
| Full-name-prefix block | First 3 normalized full-name characters | First 3 alphanumeric normalized characters | YES |
| External-domain block | Non-generic external domain | Generic domains removed | YES |
| Duplicate/exact handling | Exact rows excluded from scoring | Exact and blocked sets deduplicated/disjoint | YES |
| GB-17 columns | 17 listed features | Same 17 columns | PARTIAL |
| `name_sim` semantics | Max four-way cross-field Jaro--Winkler for each pair | Computed only for predecessor-score >= 0.5; otherwise forced to 0 | NO — BLOCKING |
| Constant `same_platform` | Retained but zero | Zero for all cross-platform rows | YES |
| GB-18 addition | Adds only `bert_cos` | Adds cached `bert_cos` only | YES, lineage incomplete |
| Semantic text | Concatenated full name, bio, location; MiniLM cosine | Same; empty text becomes `[empty]` | PARTIAL — empty behavior omitted |
| Gradient Boosting | 300 estimators, lr 0.05, depth 6, seed 42 | Same | YES |
| Negative sampling | Deterministic 3:1 negatives:positives | Same on training role | YES |
| Calibration | Separate isotonic regressor, clip, calibration entities only | Same | YES |
| Fixed thresholds | 0.98 MATCH; 0.95 REVIEW | Same | YES |
| GA genome | Four stated genes | Same | YES |
| GA decision rule | Probability regions plus promotion/demotion gates | Same | YES |
| GA constraints | Stated four bounds | Same repair/clipping constraints | YES |
| Population/generations/elites | 60/40/12 | Same | YES |
| Crossover | Uniform | Same; every child is crossed from elites | YES, selection mechanics underspecified |
| Mutation | Per gene 0.30, Gaussian sigma 0.02 | Same | YES |
| GA seeds | 7, 42, 123, 999, 2025 | Same | YES |
| Utility | 2 FP + FN + 0.1 REVIEW | Same | YES |
| Outer seeds | 101, 202, 303 | Same | YES |
| Split logic | 30% test; development 70/15/15; entity roles | Same | YES |
| Cross-role pairs | Dropped | Same | YES |
| Zero entity overlap | Asserted | Verified in all manifests | YES |
| Test labels unavailable | Claimed unavailable before final evaluation | Labels resident; test constants read pre-final; narrow accessor guard only | NO — BLOCKING |
| Source/input hash closure | Package records source/input hashes | Manifest closes internal run files, not all external code/data/cache dependencies | NO |
| Recall definition | Implicitly workflow TP / all positives | Evaluator uses TP / all positives including positive REVIEW | PARTIAL; protocol incorrectly says TP/(TP+FN) |

Methodological consistency therefore FAILS despite most parameter-level agreement. The `name_sim`, test-isolation, metric-documentation, and provenance discrepancies are material.

# J. Experimental Rigor

EXPERIMENTAL RIGOR: 3/5

Strengths:

- entity assignment rather than pair-random splitting;
- zero overlap among model-training, calibration, GA-validation, and test roles within each outer run;
- separate classifier, calibration, and policy-selection roles;
- explicit cross-role pair dropping;
- every outer run retrains, recalibrates, and reselects;
- exact, scored, missed, and workflow scopes are pair-key reconciled;
- zero duplicate workflow pair keys;
- all nine result rows recompute exactly;
- test metrics are not visibly used by the GA selection function.

Material weaknesses:

1. Test labels are not actually unavailable; the audit does not intercept direct reads.
2. Earlier experiments used the same nominal outer seeds, so confirmatory “sealed” status is not established.
3. `name_sim` is inherited from a predecessor-score-censored cache; the upstream model’s training scope and possible leakage are not closed.
4. Between 1.318 and 1.336 million cross-role pairs are dropped per outer seed. Because same-entity positives share a role while many negative pairs cross roles, this changes prevalence and FP opportunity. The resulting estimand is performance on the held-out-entity induced candidate subgraph, not the whole 2,086,245-pair corpus.
5. Three holdouts are correlated: 1,351–1,405 test entities overlap pairwise and 408 occur in all three test sets. Mean ± sample SD is descriptive, not population uncertainty.
6. The fixed policy is not tuned under the same objective and validation role; this is an unfair baseline for attributing benefit to GA.
7. There is no calibration-quality, review-outcome, cluster-level, external, temporal, or computational evaluation.

There is no direct proof that test labels changed the fitted models or selected policies. The correct finding is an unclosed leakage/post-hoc risk and an overstated isolation claim, not demonstrated test-driven selection.

# K. Numerical Accuracy

NUMERICAL ACCURACY: PASS

No manuscript numerical mismatch was found. Independent recomputation confirmed:

| Method | Precision | Recall | F1 | FP | FN | REVIEW | U |
|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 0.9910 ± 0.0051 | 0.7138 ± 0.0431 | 0.8293 ± 0.0278 | 59.0 ± 35.8 | 2265.3 ± 111.7 | 264.7 ± 395.9 | 2409.8 ± 97.2 |
| GB-18 | 0.9940 ± 0.0011 | 0.7100 ± 0.0323 | 0.8280 ± 0.0223 | 38.0 ± 7.0 | 2151.0 ± 234.2 | 438.0 ± 406.1 | 2270.8 ± 200.2 |
| GB-18-GA | 0.9889 ± 0.0055 | 0.7615 ± 0.0029 | 0.8604 ± 0.0012 | 75.7 ± 38.4 | 1558.0 ± 39.0 | 923.3 ± 151.1 | 1801.7 ± 69.3 |

The central GB-18-GA minus GB-18 mean differences are F1 +0.0324, recall +0.0515, precision -0.0051, FP +37.7, FN -593.0, REVIEW +485.3, and U -469.1. Per-partition F1 gains are 0.0208, 0.0192, and 0.0571 after manuscript rounding.

All requested scope values also match and reconcile:

- eligible profiles: 36,804 = 13,959 + 11,889 + 10,956;
- all-platform positives: 29,247;
- cross-platform positives: 29,243;
- same-platform positives: 4;
- possible cross-platform pairs: 449,149,239, independently reproduced from platform cross-products;
- exact-tier pairs: 12,403;
- model-scored pairs: 2,073,842;
- workflow pairs: 2,086,245 = 12,403 + 2,073,842;
- covered positives: 25,931;
- blocking misses: 3,312;
- retrieval recall: 25,931 / 29,243 = 88.6742%;
- candidate-space reduction: 1 - 2,086,245 / 449,149,239 = 99.5355%.

Important non-numerical metric defect: `PROTOCOL.md:71` says recall is TP/(TP+FN), but the evaluator and reported values use TP/all positives, where positive REVIEW remains in the denominator. The reported numbers are internally correct under the evaluator’s definition; the documentation is not.

## Result interpretation

The manuscript correctly presents the central result as an operating trade-off, not “GA improves everything.” It states that F1 and recall increase and FN decreases, while precision decreases and FP and REVIEW increase. It also reports the mixed semantic result honestly: mean F1 is approximately 0.8293 for GB-17 and 0.8280 for GB-18. The discussion draws the useful but limited insight that one global cosine over concatenated incomplete fields is unstable. It should go further by examining field-aware semantics, missingness, platform-pair strata, and calibration, but it does not misstate the current result.

## Utility audit

The formula is consistently `U = 2 * FP + FN + 0.1 * REVIEW`. The manuscript repeatedly calls it illustrative, scenario-specific, and based on engineering assumptions, and explicitly denies that it is economic, CRM, business, or measured operational cost. This wording is appropriate.

The explanation is nevertheless insufficient to validate policy usefulness. The coefficients have no empirical source, REVIEW is cheap and unresolved, no review-capacity constraint is imposed, and no authoritative sensitivity or Pareto analysis is available. Moving a positive from NO_MATCH to REVIEW lowers U without demonstrating eventual correct resolution. Report positive and negative REVIEW separately and evaluate development-only sensitivity or constrained/Pareto policies.

# L. Related Work

RELATED WORK COVERAGE: ADEQUATE

Bibliographic integrity is good: 16 entries, 16 cited keys, 28 citation occurrences, no undefined citation, and no uncited entry. Twelve records are fully verified and four are partially verified; none is fabricated, incorrect, or irrelevant.

| Key | Disposition | Finding |
|---|---|---|
| `linkSocial2018` | VERIFIED | Correct corpus and three-platform use |
| `shu2017uilreview` | VERIFIED | Supports cross-network linkage evidence and evaluation |
| `yao2023profile` | VERIFIED | Supports incomplete profile/string/short-text attributes |
| `papadakis2021blocking` | VERIFIED | Supports blocking/scalability claim |
| `li2020blocking` | PARTIALLY VERIFIED | Relevant; bibliography omits issue 4 |
| `barlaug2021survey` | VERIFIED | Supports neural entity-matching stages |
| `li2020ditto` | VERIFIED | Supports transformer heterogeneous-record matching |
| `ouyang2019threeway` | VERIFIED | Supports prior three-way linkage and uncertain region |
| `hendrickx2024reject` | PARTIALLY VERIFIED | Relevant; bibliography omits issue 5 |
| `sun2017gaer` | VERIFIED | Supports GA-based ER as prior art |
| `niculescu2005calibration` | VERIFIED | Supports isotonic calibration |
| `fellegi1969theory` | VERIFIED | Correct classical linkage foundation |
| `christen2026consistent` | PARTIALLY VERIFIED | Relevant to metric/error-regime rankings; pages 1–23 omitted; does not support entity-disjoint leakage claim |
| `thirumuruganathan2021deepblocker` | VERIFIED | Supports learned semantic blocking |
| `qian2019systemer` | PARTIALLY VERIFIED | Supports HITL ER, not measured coverage/review burden |
| `chow1970reject` | VERIFIED | Supports classical error–reject trade-off |

Missing or weakly supported areas:

- no direct source for the precise entity-disjoint pair-leakage assertion;
- no citation for Sentence-BERT, MiniLM, or the exact `all-MiniLM-L6-v2` model card;
- dataset-field/license-absence claims should cite the dataset repository with audit date;
- SystemER does not support measured reviewer burden;
- direct cross-platform UIL literature is thin: HYDRA and FRUI-type work should be discussed;
- evolutionary deduplication/record-linkage history is underdeveloped;
- pairwise versus cluster-level ER evaluation lacks Menestrina et al.;
- human-workflow evidence should include CrowdER or a comparable empirical study;
- GA threshold/reject-policy optimization and non-evolutionary search alternatives are missing.

The generated bibliography visibly lowercases “IEEE” as “iEEE” in reference [11], and the metadata for [5], [9], and [16] should be completed.

# M. Figure Assessment

## Figure 1 — Cross-Platform Identity Resolution Pipeline

Rating: 3/5.

A reader can understand the broad candidate → representation → score/calibrate → three-way-decision path within about 10 seconds. The three outputs are clear, and the figure correctly signals that only candidate pairs are scored. However, auxiliary labels render near 6 pt, “probability-like evidence” and bottom notes float without clear leaders, and exact-tier automatic decisions versus model-scored decisions are not as structurally explicit as the workflow accounting requires. The figure is accurate but too small in print for a 5/5 rating.

## Figure 2 — Entity-Disjoint Evaluation Protocol

Rating: 4/5.

The four roles and left-to-right order are immediately legible; large red warnings clearly communicate intended entity separation and test-only evaluation. Labels are approximately 8–9 pt and unclipped. The horizontal arrows should identify what flows between stages, and the dashed “NO ENTITY OVERLAP” line asserts rather than depicts pairwise disjoint sets. More importantly, “test labels unavailable” is not true of the implementation. The figure currently communicates a stronger guarantee than the code provides and must be revised or backed by a genuinely isolated rerun.

# N. Table Assessment

| Table | Decision | Assessment |
|---|---|---|
| Table I: candidate decomposition | REVISE | Numbers and scope are correct and highly useful. Expand T/G+/I, mention username length >=3 in nearby text, and distinguish exact-tier auto-MATCH from model-scored scope. |
| Table II: mean workflow performance | REVISE | Correct and central. Add leading zeros, define method abbreviations and FP/FN/REVIEW, state recall/REVIEW semantics, and provide test denominator or review rate context. Decimal alignment would improve readability. |
| Table III: per-partition F1 | REVISE | Correct and compact. Rename “Seed” to “Outer-partition seed.” Consider retaining it only if space permits after adding fair-baseline or review-composition evidence. |

No table should be removed solely for numerical reasons. Tables II and III appear after their first discussion, which mildly disrupts reading but is legal IEEE float placement. The paper does not confuse candidate-workflow counts with model-scored counts; it explicitly separates them.

# O. Agentic CRM Framing

The search found 14 source lines containing Agentic/CRM/customer/business/deployment/operational language. Sentence-level classification follows.

| Location/statement | Classification | Assessment |
|---|---|---|
| Title and PDF title metadata: “for an Agentic CRM Platform” | OVERCLAIM | Implies an evaluated platform more strongly than the evidence supports |
| Abstract: Agentic CRM systems require consolidated identities | CONTEXT ONLY | Plausible motivation, not tested here |
| Abstract: merge/defer/reject workflow | SUPPORTED | Directly evaluated at pair-decision level |
| Abstract: downstream CRM agents, lead scoring, human review, business outcomes not evaluated | SUPPORTED | Accurate boundary |
| Introduction: Agentic CRM may coordinate automated activities around customer records | CONTEXT ONLY | Hypothetical application context |
| Introduction: identity errors can corrupt or fragment records | CONTEXT ONLY | Motivation, not measured outcome |
| Introduction: paper treats Agentic CRM only as context | SUPPORTED | Accurate disclaimer |
| Introduction: score is not an operational action; REVIEW consumes attention | SUPPORTED / CONTEXT ONLY | Three-way action is implemented; actual attention cost is not measured |
| Research question: operational trade-off of fixed probabilities | SUPPORTED | Component outcomes are reported |
| System overview: downstream CRM behavior is not tested | SUPPORTED | Accurate boundary |
| Figure 1 caption: policy yields operational outcome | SUPPORTED WITH QUALIFIER | Only offline pair-level outcome |
| Utility paragraph: illustrative operational utility, not economic/CRM/business/measured cost | SUPPORTED | Correct limitation |
| Discussion: trade-off may or may not suit deployment | CONTEXT ONLY | Properly conditional |
| Discussion: identity decisions could supply upstream records; no agent/lead/customer evidence | CONTEXT ONLY / SUPPORTED DISCLAIMER | Does not claim measured downstream benefit |
| External validity: no live Agentic CRM task | SUPPORTED | Correct limitation |
| Construct validity: no CRM outcomes or lead scoring | SUPPORTED | Correct limitation |
| Conclusion: operational pair decisions; future downstream CRM assessment | SUPPORTED / CONTEXT ONLY | Properly bounded future work |

No body sentence claims measured conversion, business value, agent quality, lead-scoring performance, or downstream CRM performance. The title is the main boundary violation. The opening paragraph restores the boundary quickly, but a first-time reviewer may already have formed the wrong expectation.

# P. Dataset / Ethics

DATASET / ETHICS RISK: HIGH

Positive points:

- LinkSocial is cited as the public source;
- the paper clearly calls the local data a transformed derivative;
- no raw names, usernames, URLs, images, or personal records appear in the manuscript or authoritative package;
- the manuscript does not claim redistribution rights;
- release is explicitly constrained to code/configuration/hashes/aggregates absent permission.

Reviewer concerns:

- public hosting is not a reuse or redistribution license;
- no machine-readable license was found;
- consent, original collection terms, platform terms, retention, and formal ethics review are unknown;
- the platforms and profiles are historical but still involve identity linkage, which has privacy and misuse implications;
- transformations and de-identification risk are underspecified;
- the exact legal/ethical basis for research use is not documented.

This is not CRITICAL because the paper exposes no raw PII and acknowledges the uncertainty, but publication or artifact release should not proceed without a documented provenance/permission assessment and an explicit ethics statement addressing re-identification and linkage harms.

# Q. Reproducibility

REPRODUCIBILITY: MODERATE

A knowledgeable researcher can understand and independently recompute candidate scope, decision rules, workflow metrics, and aggregate summaries from the package. Seeds, GA settings, fitted artifacts, selected policies, row-level decisions, split manifests, environment information, and checksums are present. The package is internally intact.

Full rerun reproducibility is not high because:

- imported source and key data/cache inputs are outside the authoritative manifest;
- the source tree and run package are untracked in a heavily dirty repository state;
- upstream production of the 17-feature and MiniLM caches is not fully frozen;
- the MiniLM model revision/tokenizer and feature-generation environment are not closed;
- `name_sim` contains undocumented historical gating;
- the baseline-threshold and utility-weight provenance is unclear;
- test-label isolation depends on convention rather than a physically sealed interface.

The selected per-partition policies are saved in artifacts but not reported in the paper. A clean commit or source snapshot, lockfile, commands, raw-input hashes, feature-cache lineage, and clean-room rerun are needed for HIGH reproducibility.

# R. IEEE / ICSEC Compliance

Official ICSEC 2026 requirements checked at `https://cpe.eng.kps.ku.ac.th/ICSEC2026/submission.php` include the IEEE conference template, English, 4–6 pages inclusive, standard two-column layout, and double anonymity.

| Requirement | Status | Explanation |
|---|---|---|
| IEEEtran conference class | PASS | `\documentclass[conference]{IEEEtran}`; no margin/spacing hacks found |
| Length | PASS | 5 pages, within 4–6 inclusive |
| Two columns / paper size | PASS | Standard two-column US Letter layout |
| Fonts | PASS | 13 font resource variants; all embedded/subset; no Type 3/unembedded fonts |
| Margins and spacing | PASS | No visible intrusion; no geometry or line-spacing override |
| Figure captions | PASS | Captions below figures and numbered correctly |
| Table captions | PASS | Captions above tables and numbered correctly |
| Equations | PASS | Numbered and within columns |
| Algorithm formatting | WARNING | Valid, but `Require` wraps and isolates genome symbol `g` |
| Bibliography closure | PASS | 16 keys/entries; no missing or uncited entry |
| Bibliography quality | WARNING | “iEEE” rendering typo and incomplete metadata in three records |
| Overflow/clipping | PASS | 0 overfull boxes; all pages rendered without collision or clipping |
| Build warnings | WARNING | Two underfull hboxes and one underfull vbox, cosmetic only |
| Figure readability | WARNING | Figure 1 auxiliary text is about 6 pt at final size |
| Table readability | WARNING | Table II is dense and omits metric definitions |
| Page flow | WARNING | Tables II/III float after first discussion; awkward column break leaves “The” alone |
| PDF metadata anonymity | PASS | Author=Anonymous; non-identifying subject/title/keywords |
| Double-anonymous visible content | PASS | No author, affiliation, email, institution, company, acknowledgment, or identifying URL |
| Figure metadata | PASS | No identifying author metadata |
| ICSEC PDF eXpress | WARNING | Not formally validated; conference ID 71596 |
| Copyright notice | WARNING | Absent; confirm whether required for initial anonymous review or only camera-ready |
| Current upload ZIP | FAIL | Adjacent Overleaf ZIP/README are stale and do not represent the audited source/PDF; do not submit that archive |

ANONYMITY: PASS

No identity leak was found in visible PDF content, source comments, bibliography beyond normal author citations, figure metadata, or PDF metadata. Exact-title search found no indexed duplicate, but authors must separately ensure that no preprint publicly uses the submission title, as ICSEC requires a different preprint title.

DESK-REJECTION RISK: LOW

The audited `main.pdf` itself satisfies the main format, length, language, and anonymity rules. Risk rises if the stale ZIP is uploaded, if PDF eXpress rejects the file, if the missing copyright notice is required at initial submission, or if the same title has been publicly used. These checks are administrative and separate from the high scientific-rejection risk.

# S. Reviewer A — Evolutionary Computing

## Scores

| Criterion | Score |
|---|---:|
| Novelty | 2/5 |
| Technical Quality | 3/5 |
| Experimental Rigor | 3/5 |
| Reproducibility | 3/5 |
| Clarity | 4/5 |
| Related Work | 2/5 |
| Significance | 2/5 |

Recommendation: WEAK REJECT

Major Concerns:

- The experiment does not isolate GA value from policy-class value and validation tuning.
- Four continuous genes over a piecewise-constant empirical objective may be solved more simply and deterministically.
- Boundary-hitting, long plateaus, and decision-equivalent genomes indicate weak parameter identifiability.
- The fixed baseline is not tuned under the same U.
- One arbitrary scalarization and no Pareto/sensitivity analysis make the headline utility contingent.
- The recall formula in the protocol conflicts with the evaluator.

Minor Concerns:

- Bounds and hyperparameters lack rationale.
- Initialization ranges do not cover the whole repaired feasible region uniformly.
- Parent selection/crossover pressure is underspecified.
- Calibration stability is not evaluated.
- No known-optimum test or authoritative-run-specific GA test is supplied.

Questions for Authors:

1. Why use GA rather than breakpoint enumeration, coordinate search, or equal-budget random search?
2. What does a validation-tuned two-threshold baseline achieve?
3. How many unique decision vectors, rather than genomes, were visited?
4. Why do distinct outer-202 genomes yield identical decisions?
5. How were bounds, budget, and U coefficients fixed before outcome inspection?
6. How do results change under review budgets or a Pareto frontier?

Likely Rejection Reasons:

- minimal EC novelty;
- no demonstration that GA is necessary or competitive;
- confounded and unfair comparator;
- unvalidated scalar objective;
- only three outer partitions.

Required Revisions:

- compare identical policy families under grid/breakpoint, random, coordinate, and GA search;
- add threshold-only, promotion-only, demotion-only, and full-policy ablations;
- report budget, runtime, convergence, boundary hits, and unique decision vectors;
- justify bounds/hyperparameters;
- add development-only utility sensitivity or multiobjective analysis;
- correct three-way metric definitions.

# T. Reviewer B — Entity Resolution / ML

## Scores

| Criterion | Score |
|---|---:|
| Novelty | 2/5 |
| Technical Quality | 2/5 |
| Experimental Rigor | 3/5 |
| Reproducibility | 2/5 |
| Clarity | 4/5 |
| Related Work | 3/5 |
| Significance | 2/5 |

Recommendation: REJECT

Major Concerns:

- `name_sim` is censored by a predecessor score and is not the feature described.
- The sealed-label claim is unsupported by the implementation.
- The GA comparison lacks a fair validation-tuned non-GA baseline.
- Isotonic calibration is never evaluated as calibration.
- REVIEW is treated as a cheap unresolved escape with no observed reviewer outcome.
- “End-to-end” stops at pair decisions and does not test clustering/transitivity.
- Candidate retrieval has no stronger baseline and caps recall at 88.6742%.

Minor Concerns:

- `same_platform` is a constant feature.
- `[empty]` can make two empty semantic records maximally similar.
- One global concatenated cosine provides no field attribution.
- Exact-tier errors are not reported separately.
- Semantic and feature-cache lineage is incomplete.

Questions for Authors:

1. Why was uncensored `name_sim` not recomputed for all authoritative pairs?
2. Was the predecessor model trained without test-entity exposure?
3. What are held-out calibration metrics before and after isotonic mapping?
4. What fraction of REVIEW is positive versus negative, and what happens after review?
5. How are pair decisions converted into consistent entities?
6. What are retrieval and decision results by platform pair and missingness?
7. What legal/ethical basis permits use of the LinkSocial derivative?

Likely Rejection Reasons:

- a central feature is materially misdescribed;
- no fair decision-policy comparator;
- no genuine test-label isolation;
- no external, cluster-level, or human-review evidence;
- narrow and unstable semantic ablation;
- unresolved licensing/ethics.

Required Revisions:

- rebuild all features from source fields and rerun;
- physically isolate test labels;
- add fair tuned decision baselines;
- evaluate calibration, review outcomes, final clusters, and retrieval slices;
- add external/temporal evidence or narrow the framing;
- close data/model/cache provenance and ethics documentation.

# U. Reviewer C — Experimental Methodology

## Scores

| Criterion | Score |
|---|---:|
| Novelty | 2/5 |
| Technical Quality | 3/5 |
| Experimental Rigor | 3/5 |
| Reproducibility | 2/5 |
| Clarity | 4/5 |
| Related Work | 3/5 |
| Significance | 2/5 |

Recommendation: WEAK REJECT

Major Concerns:

- “Test labels unavailable” is contradicted by resident labels and pre-final test constants.
- Previous use of the same outer-seed family defeats a strong confirmatory/sealed interpretation.
- Cross-role dropping removes most cross-entity negatives and changes the estimand.
- the manifest is not closed over critical code, data, or cached-feature dependencies;
- only three correlated holdouts support descriptive, not inferential, conclusions.

Minor Concerns:

- three-way FN/REVIEW-positive semantics are not clearly defined;
- fixed-threshold provenance is unclear;
- U is transparent but weakly grounded;
- error analysis is aggregate;
- exact-tier errors and calibration quality are not separated;
- the authoritative Markdown summary contains malformed Pandas text, though CSV results are correct.

Questions for Authors:

1. Were these partitions or outcomes inspected before freezing models, utility, bounds, and seeds?
2. Why is “sealed” used despite historical seed reuse?
3. Can evaluation labels be joined only in a separate final process?
4. What deployment population does the held-out induced-subgraph estimand represent?
5. How do prevalence and candidate composition differ across roles and dropped pairs?
6. Was feature-cache creation entity- and label-blind?

Likely Rejection Reasons:

- overclaimed test isolation;
- post-hoc exposure risk;
- unclear deployment estimand after dropping cross-role negatives;
- weak statistical evidence;
- incomplete provenance closure.

Required Revisions:

- use genuinely fresh partitions/corpus under an immutable preregistered protocol;
- remove labels from every development process;
- hash/snapshot every source and input dependency;
- define and report role-specific populations and prevalence;
- use more disjoint folds or repeated partitions with entity-aware uncertainty;
- define all three-way metrics and REVIEW composition.

# V. Top 10 Rejection Risks

| Rank | Risk | Severity | Evidence | Required mitigation |
|---:|---|---|---|---|
| 1 | Central `name_sim` feature is misdescribed and predecessor-score-censored | CRITICAL | Cache computes it only for score >=0.5; GA and GB consume it | Recompute uncensored features from raw fields and rerun all authoritative experiments |
| 2 | GA benefit is not isolated | CRITICAL | Rich validation-tuned policy vs inherited fixed thresholds; no equal-policy search baseline | Add tuned threshold and identical-genome non-GA/equal-budget baselines |
| 3 | “Sealed/unavailable test labels” claim is false | HIGH | Labels are resident and test constants read pre-final; audit wraps one accessor | Physically separate development and evaluation processes and use fresh labels/partitions |
| 4 | Historical exposure/post-hoc risk | HIGH | Same nominal outer seeds existed in earlier experiment family | Freeze settings in immutable timestamped protocol and evaluate fresh seeds/corpus |
| 5 | Algorithmic novelty/significance is weak | HIGH | Standard GB, isotonic, four-gene GA, standard three-way policy | Reframe as integration/methodology and establish optimizer/policy insight experimentally |
| 6 | Evidence is statistically and externally narrow | HIGH | One historical corpus; three correlated holdouts; no interval or external test | Add more/disjoint partitions, entity-aware uncertainty, and external/temporal validation |
| 7 | Reproducibility chain is not closed | HIGH | External code/data/caches outside manifest; dirty/untracked tree | Clean commit/source snapshot, input hashes, lockfile, model revision, full rerun commands |
| 8 | REVIEW/utility lacks empirical validity | HIGH | REVIEW cost 0.1; volume nearly doubles; no reviewer outcomes or sensitivity | Report class composition/rates, capacity constraints, sensitivity/Pareto analysis, human study |
| 9 | Dataset license and ethics are unresolved | HIGH | Public derivative has no confirmed license, consent, or formal ethics record | Obtain permission/legal basis; add ethics/privacy statement; restrict redistribution |
| 10 | Pair-level results do not establish identity consolidation or CRM value | MEDIUM | No clustering, transitivity, downstream agents, lead scoring, or business outcomes | Evaluate entity-level outputs or strictly narrow title, abstract, and significance claims |

# W. Required Revisions

## BLOCKING — must fix before submission

1. Recompute uncensored `name_sim` for every scored pair directly from frozen source profile fields and rerun every outer experiment.
2. Implement genuine test-label isolation: development inputs must not contain test labels or test-label-derived constants; evaluation should join labels only after models, calibrators, policies, configs, and hashes are frozen.
3. Use fresh confirmatory partitions or a fresh corpus not previously inspected under an immutable, externally timestamped protocol.
4. Add validation-tuned non-GA comparators on the same objective and policy class, including at minimum tuned two-threshold and equal-budget search over all four genes.
5. Correct the manuscript’s “sealed,” “unavailable,” source/input-hash, and feature-definition claims; correct the protocol recall definition and explicitly define positive REVIEW handling.
6. Close provenance over all imported source, raw/normalized input, feature caches, MiniLM revision, environment, and commands using a clean commit or complete source snapshot.
7. Resolve or document the legal/ethical basis for use of the LinkSocial derivative before release or submission.

## MAJOR — strongly recommended

1. Add policy-class ablations and separate optimizer gain from policy-family gain.
2. Report positive/negative REVIEW counts, review rate, automatic coverage, and selective metrics.
3. Add development-only utility sensitivity, review-budget/precision constraints, or a Pareto analysis.
4. Evaluate calibration with held-out Brier score, log loss, ECE, and reliability curves.
5. Define the held-out induced-subgraph estimand and report role-specific candidates, negatives, prevalence, exact/scored composition, and dropped pairs.
6. Increase outer evaluations or use disjoint entity folds and entity-aware paired uncertainty.
7. Report exact-tier TP/FP, retrieval performance by blocking key/platform pair, and runtime/memory.
8. Evaluate final clusters/transitivity and false-merge propagation, or avoid “end-to-end identity resolution” language.
9. Expand direct UIL, evolutionary ER, HITL ER, semantic model, and pair-versus-cluster evaluation literature.
10. Remove Agentic CRM from the title unless downstream application evidence is added.

## MINOR — polish

1. Add leading zeros in Tables II and III and clarify captions/abbreviations.
2. Rename Table III’s “Seed” to “Outer-partition seed.”
3. Increase Figure 1 auxiliary text size and label Figure 2 artifact flows.
4. Fix the awkward final-page column break and the generated “iEEE” typo.
5. Complete issue/page metadata for the partially verified citations.
6. Explain exact username length >=3, empty semantic-text handling, and constant `same_platform`.
7. Clarify GA parent selection, initialization, bounds, and tie-breaking rationale.
8. Report selected policies or provide a concise artifact pointer that preserves anonymity.

## OPTIONAL — preference only

1. Replace the scalar GA with a multiobjective evolutionary analysis if the venue/topic fit benefits from a stronger EC contribution.
2. Retain Table III only if it does not displace more important fair-baseline or review-composition evidence.
3. Reorder floats to keep the central results nearer their first discussion.

# X. What Should NOT Be Changed

- Do not soften the honest statement that MiniLM’s fixed-policy effect is mixed.
- Do not remove the precision, FP, and REVIEW penalties of the GA trade-off.
- Do not present GA as retraining or improving the predictor.
- Do not replace the cross-platform positive denominator with the all-platform denominator.
- Do not omit the 3,312 retrieval misses or the 88.6742% retrieval ceiling.
- Do not call U economic/business cost.
- Do not claim human-in-the-loop benefit without a study.
- Do not expand Agentic CRM claims to lead scoring, conversion, autonomous-agent quality, or downstream business value.
- Preserve the four-role entity-level design as the intended protocol; fix its label-isolation implementation rather than reverting to pair-random splitting.
- Preserve the row-level exact/scored/missed decomposition and the authoritative aggregate values unless a required rerun changes them.
- Preserve the explicit limitations on external validity, clustering, review, and statistical significance.
- Preserve the current IEEEtran structure, 5-page length, anonymous metadata, and embedded-font setup; only targeted visual cleanup is needed.

# First-Time Reader Comprehension

| Section | Readability | Main first-reader issue |
|---|---:|---|
| Abstract | 4/5 | “Isotonic-calibrated” arrives early; Agentic CRM opening broadens expectations |
| Introduction | 4/5 | Clear RQs, but GA attribution sounds stronger than the available baseline supports |
| Related Work | 3/5 | Thin direct UIL/EC coverage; entity-disjoint leakage assertion lacks a supporting source |
| System Overview | 4/5 | Clear pipeline; exact-tier bypass and full workflow accounting could be more explicit |
| Methodology | 3/5 | Dense internal names GB-17/GB-18/`bert_cos`; `name_sim` description is inaccurate |
| Experimental Setup | 4/5 | Four roles are understandable; “sealed/unavailable” guarantee is overstated; dropped-pair estimand unexplained |
| Results | 4/5 | Honest trade-off; absolute counts lack denominators/review rates; tables float later |
| Discussion | 4/5 | Good separation of retrieval and policy failures; no detailed platform/missingness analysis |
| Limitations | 5/5 | Clear and unusually candid, though it omits the feature, sealing, seed-exposure, and provenance defects found here |
| Conclusion | 4/5 | Accurate summary, but “operational” must remain pair-level and GA causality remains limited |

Terminology needing earlier or clearer definition includes GB-17, GB-18, exact tier, model-scored scope, `name_sim`, `bert_cos`, outer seed, calibrated probability-like scale, genome, and positive REVIEW semantics. The principal reasoning jumps are from a policy improvement to GA value, from disjoint entities to sealed labels, and from pair decisions to Agentic CRM relevance.

# Limitations Coverage Audit

Clearly acknowledged in the manuscript:

- one historical corpus;
- only three outer splits;
- historical platforms;
- candidate-retrieval ceiling;
- mixed MiniLM result;
- illustrative utility;
- increased FP;
- increased REVIEW volume;
- no human-review study;
- no downstream Agentic CRM evaluation;
- no lead-scoring evaluation;
- no generalization beyond LinkSocial.

Missing or insufficiently acknowledged:

- censored/predecessor-dependent `name_sim`;
- actual test-label availability and pre-final test constants;
- historical reuse of the outer seed family;
- incomplete provenance closure and dirty repository state;
- changed prevalence/estimand caused by cross-role negative dropping;
- lack of fair tuned policy/search baselines;
- absence of calibration-quality evidence;
- boundary-hitting and decision-equivalent GA genomes;
- exact-tier error contribution;
- lack of entity-cluster/transitivity metrics;
- no evidence supporting the U coefficients or review-capacity assumption.

# Final Independent Decision

FINAL REVIEW RECOMMENDATION:

REJECT

SUBMISSION READINESS:

MAJOR REVISION REQUIRED

The decision is driven by remediable but central scientific-validity defects, not by formatting or arithmetic. The existing numeric artifact chain is internally consistent, but it validates an experiment whose feature semantics, test-isolation claim, comparative baseline, and provenance closure are not adequate for submission in their current form.
