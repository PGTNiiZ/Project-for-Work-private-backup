# Cross-Platform Profile Identity Resolution for an Agentic CRM Platform Using Genetic Optimization of Three-Way Decisions

<!-- SAFE TO REWORD: Title is editable. Keep technical scope and avoid claims of measured CRM impact. -->

## ABSTRACT

<!-- SAFE TO REWORD: Reader-friendly abstract prose. Preserve the marked values and limitations. -->
An Agentic CRM platform needs a reliable way to recognize when profiles on different social networks may belong to the same person before an automated workflow acts on that information. This study evaluates cross-platform profile identity resolution on a transformed derivative of the LinkSocial corpus from Twitter, Google+, and Instagram. The pipeline first creates a manageable set of candidate profile pairs, represents each pair with profile similarities, and estimates whether the profiles correspond to one person. Instead of making every decision with one fixed cutoff, the proposed decision layer assigns each pair to MATCH, REVIEW, or NO_MATCH. A Genetic Algorithm selects the thresholds and name-evidence cutoffs for this three-way policy on validation entities while leaving the calibrated pair classifier unchanged. Three repeated entity-disjoint outer evaluations compare a handcrafted baseline (GB-17), a MiniLM-augmented variant (GB-18), and the GA policy (GB-18-GA). <!-- VERIFIED EXPERIMENTAL RESULT — change only if experiment changes --> GB-18-GA achieved mean F1 = 0.8603, compared with 0.8280 for fixed-threshold GB-18, but it increased mean false positives from 38.0 to 75.7 and REVIEW decisions from 438.0 to 923.3. Candidate generation covered <!-- VERIFIED EXPERIMENTAL RESULT — change only if experiment changes --> 88.6742% of 29,243 labeled positive pairs, limiting attainable end-to-end recall. The findings are limited to LinkSocial and an illustrative operational utility scenario; they do not establish generalization, measured business benefit, or a new three-way or evolutionary identity-resolution method.

## INDEX TERMS

Entity resolution; record linkage; cross-platform identity linkage; evolutionary computing; operational decision policy; machine learning; Agentic CRM.

# I. INTRODUCTION

<!-- SAFE TO REWORD: Motivation and application context. -->
People can have profiles on several social platforms while names, identifiers, biographies, links, and locations differ or are incomplete. In an Agentic CRM context, resolving such profiles can provide a more coherent profile view before a workflow recommends, routes, or summarizes information. The present study evaluates identity resolution only; it does not evaluate CRM deployment, agents, conversion outcomes, or human workflow performance.

<!-- SAFE TO REWORD: Research-context wording. -->
Pair classifiers produce a score, but a practical system must decide whether to accept a likely match, reject a likely non-match, or reserve an uncertain case for review. Three-way record linkage and evolutionary entity resolution are established research directions. This study therefore evaluates a separated operational composition rather than claiming a new GA or three-way linkage method.

Research questions:

- RQ1: How does adding MiniLM cosine similarity affect fixed-threshold workflow outcomes?
- RQ2: Given frozen calibrated GB-18 probabilities, how does a GA-selected MATCH/REVIEW/NO_MATCH policy affect precision, recall, F1, review volume, and an illustrative utility?
- RQ3: How strongly does candidate-generation recall constrain attainable end-to-end resolution?

Contributions:

1. Entity-disjoint evaluation that separates training, calibration, policy selection, and testing.
2. Controlled MiniLM representation and GA decision-policy ablations.
3. Repeated outer-split evidence for policy trade-offs and candidate-retrieval failure decomposition.

# II. RELATED WORK

<!-- SAFE TO REWORD: Related-work synthesis. Do not alter citations without verification. -->
Blocking and filtering reduce entity-resolution candidate sets but can omit true pairs, making candidate coverage distinct from downstream classification [2], [7]. Cross-platform profile linkage uses profile similarities and supervised machine-learning models [1], [5]. Three-way record linkage has been studied using granular descriptors [3], and GAs have been applied to entity resolution [4]. These prior works mean that this study does not claim novelty for GAs or MATCH/REVIEW/NO_MATCH decisions themselves. Application-oriented linkage evaluation can require more than one aggregate metric [6]; this study consequently reports FP, FN, REVIEW, precision, recall, F1, and illustrative utility together.

# III. METHODOLOGY

## A. Data, Labels, and Candidate Generation

<!-- SAFE TO REWORD: Dataset/context explanation. -->
Experiments use a locally transformed derivative of the public LinkSocial corpus [1], containing Twitter, Google+, and Instagram profiles. A positive pair has the same non-empty source entity identifier. The public source documents usernames, full names, biographies, external URLs, bi-grams, and profile-image URLs for some platforms. The source repository does not state a machine-readable reuse license or formal ethics documentation; raw records are not redistributed.

<!-- VERIFIED DATASET COUNT — change only if dataset/pipeline changes -->
- Profiles: 36,807.

<!-- VERIFIED RETRIEVAL RESULTS — change only if candidate-generation experiment changes -->

| Retrieval measure | Value |
|---|---:|
| Possible cross-platform pairs | 449,149,239 |
| Candidate pairs | 2,086,245 |
| Space reduction | 99.5355% |
| Labeled positive pairs | 29,243 |
| Covered positives | 25,931 |
| Blocking misses | 3,312 |
| Retrieval recall | 88.6742% |

Candidate generation combines an exact tier with username-prefix, full-name-prefix, and external-domain blocking. The 3,312 positive pairs missing from the candidate set cannot be recovered by the pair model or the decision policy.

## B. Pair Models and Decision Policy

<!-- SAFE TO REWORD: Technical explanation. Preserve model settings and decision rule. -->
GB-17 uses Gradient Boosting with 17 handcrafted pair features, including name similarities, bio overlap/length features, location features, availability indicators, platform indicators, and length/prefix features. GB-18 adds one feature, `bert_cos`: cosine similarity of normalized `all-MiniLM-L6-v2` embeddings of concatenated full name, biography, and location.

<!-- VERIFIED MODEL SETTINGS — do not modify without rerunning/verification -->
- Gradient Boosting estimators: 300.
- Learning rate: 0.05.
- Maximum depth: 6.
- Model seed: 42.
- Training negative undersampling: 3:1 negative-to-positive ratio.
- Calibration: isotonic regression on calibration entities only.
- Fixed-threshold policy: MATCH at probability >= 0.98; REVIEW for [0.95, 0.98); otherwise NO_MATCH.

GB-18-GA consumes frozen calibrated GB-18 probabilities. It does not retrain the pair classifier or refit the calibrator. For calibrated probability p and name evidence n, the genome is g = [t_match, t_review, c_promote, c_demote]. It produces:

- MATCH if p >= t_match.
- MATCH if t_review <= p < t_match and n >= c_promote.
- NO_MATCH if t_review <= p < t_match and n < c_demote.
- REVIEW otherwise within that band.
- NO_MATCH if p < t_review.

<!-- VERIFIED GA SETTINGS — do not modify without rerunning/verification -->
- Seeds: {7, 42, 123, 999, 2025}.
- Population: 60.
- Generations: 40.
- Elites: 12.
- Crossover: uniform.
- Mutation probability: 0.30.
- Mutation standard deviation: 0.02.
- Selection: lowest validation utility; ties resolved by smallest seed.

<!-- VERIFIED OBJECTIVE — engineering assumption, not measured economic cost -->

U = 2 × FP + 1 × FN + 0.1 × REVIEW

This is an illustrative operational utility scenario, not measured CRM or economic cost.

# IV. EXPERIMENTAL SETUP

<!-- SAFE TO REWORD: Protocol explanation. -->
Three deterministic outer entity partitions use seeds 101, 202, and 303. Approximately 30% of entities form each outer test set. Remaining entities are allocated to model training (70%), calibration (15%), and GA validation (15%). Candidate pairs crossing roles are dropped, and the implementation asserts no entity overlap across roles.

<!-- VERIFIED SPLIT COUNTS — do not modify without experiment verification -->
In the frozen primary run before scored-pair filtering, role counts were 510,981 training, 26,246 calibration, 22,873 GA-validation, and 195,440 test candidate pairs; 1,330,705 cross-role candidates were dropped.

[FIGURE 1 — Leakage-Safe Entity-Disjoint Evaluation Pipeline]

Figure 1. Leakage-safe evaluation pipeline. The GA uses validation entities only; sealed-test labels are accessed only for final evaluation.

Test labels are not accessed during training, calibration, GA optimization, or seed selection. Workflow metrics include split-specific exact-tier outputs and blocking-missed positives as fixed constants. A 2,000-resample paired conditional bootstrap on a separately frozen primary test role estimates uncertainty for scored candidates while retaining exact/blocking constants fixed.

# V. RESULTS AND DISCUSSION

## A. Repeated Outer-Split Evaluation

<!-- VERIFIED EXPERIMENTAL RESULTS — change only if experiment changes -->

| Method | Precision (mean ± SD) | Recall (mean ± SD) | F1 (mean ± SD) | FP (mean ± SD) | FN (mean ± SD) | REVIEW (mean ± SD) | Utility (mean ± SD) |
|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 0.9909 ± 0.0051 | 0.7137 ± 0.0431 | 0.8292 ± 0.0277 | 59.0 ± 35.8 | 2,266.3 ± 113.4 | 264.7 ± 395.9 | 2,410.8 ± 98.9 |
| GB-18 | 0.9940 ± 0.0010 | 0.7099 ± 0.0322 | 0.8280 ± 0.0222 | 38.0 ± 7.0 | 2,152.0 ± 232.6 | 438.0 ± 406.1 | 2,271.8 ± 198.5 |
| GB-18-GA | 0.9889 ± 0.0054 | 0.7614 ± 0.0028 | 0.8603 ± 0.0011 | 75.7 ± 38.4 | 1,559.0 ± 38.1 | 923.3 ± 151.1 | 1,802.7 ± 68.3 |

<!-- VERIFIED PER-SPLIT RESULTS — change only if experiment changes -->

| Outer seed | GB-17 F1 | GB-17 Utility | GB-18 F1 | GB-18 Utility | GB-18-GA F1 | GB-18-GA Utility |
|---:|---:|---:|---:|---:|---:|---:|
| 101 | 0.8394 | 2,523.2 | 0.8408 | 2,051.2 | 0.8616 | 1,759.2 |
| 202 | 0.7978 | 2,337.0 | 0.8408 | 2,436.0 | 0.8600 | 1,767.4 |
| 303 | 0.8504 | 2,372.2 | 0.8023 | 2,328.2 | 0.8594 | 1,881.4 |

<!-- SAFE TO REWORD: Results interpretation. Preserve the direction of findings. -->
RQ1 has mixed evidence. GB-18 improved F1 on the separately frozen primary split, but its fixed-threshold performance did not consistently exceed GB-17 across repeated outer splits. MiniLM cosine must therefore not be described as consistently improving results on this corpus.

<!-- VERIFIED RQ2 RESULTS — change only if experiment changes -->
RQ2 shows that GB-18-GA exceeded GB-18 F1 in all outer partitions by 0.0208, 0.0192, and 0.0571. It reduced FN and improved recall, while increasing FP and REVIEW decisions. The policy changes an operational trade-off rather than improving every error dimension.

<!-- VERIFIED CONDITIONAL BOOTSTRAP RESULTS — change only if experiment changes -->
On the frozen primary split, GB-18-GA minus GB-18 had F1 difference +0.0235, 95% CI [+0.0208, +0.0262]; recall difference +0.0386, 95% CI [+0.0344, +0.0427]; FP difference +32, 95% CI [+22, +44]; FN difference -266, 95% CI [-299, -234]; REVIEW difference +224, 95% CI [+166, +283]; and utility difference -179.6, 95% CI [-214.7, -144.1]. These intervals are conditional on one scored test population and fixed retrieval constants; they are not population-level significance claims.

## B. Candidate-Generation Ceiling

<!-- VERIFIED RQ3 RESULTS — change only if candidate-generation experiment changes -->
RQ3 is a limitation result, not a retrieval improvement. The 3,312 positives absent from the candidate set cannot be corrected by GB-17, GB-18, or GB-18-GA. Across outer tests, candidate recall was 0.8838 ± 0.0002 and blocking misses were 1,023.7 ± 10.2.

<!-- SAFE TO REWORD: Utility sensitivity explanation. -->
A 12-scenario frozen-policy sensitivity analysis varied FP penalty {1, 2, 5, 10} and REVIEW penalty {0.02, 0.1, 0.5}, fixing FN penalty at 1. GB-18-GA had lowest frozen-policy utility in 8 of 12 scenarios, not all. The policy was not retuned per scenario.

## C. Failure Modes

<!-- VERIFIED FAILURE-ANALYSIS RESULTS — change only if experiment changes -->
The frozen primary test analysis found 96 scored-candidate false-positive MATCH decisions under GB-18-GA; 66 were in the high name-similarity band. Among 559 scored-candidate false-negative NO_MATCH decisions, 242 lacked paired biography evidence and 236 lacked usable paired URL evidence. All 559 lacked paired usable location evidence in the reconstructed test representation. The review region contained 480 positive and 367 negative scored candidates.

<!-- SAFE TO REWORD: Failure interpretation. -->
These counts do not prove that missing fields cause every error. They show that lexical agreement can create false-merge risk and that several secondary evidence channels are unavailable where decisions fail. REVIEW remains an explicit operational outcome, but its practical usefulness requires a separate human-review study.

# VI. LIMITATIONS AND THREATS TO VALIDITY

<!-- EDIT CAREFULLY: Preserve all scope limits. -->
The study evaluates one transformed corpus and does not establish outcomes for other platforms, languages, time periods, or datasets. Only three outer partitions are used. Source labels may contain noise. The utility coefficients are illustrative assumptions, not measured business cost. Candidate blocking omits positives before scoring, and no improved blocking method is proposed. REVIEW is an offline policy output, not observed human-review workload or accuracy.

The public LinkSocial repository identifies the source corpus but lacks a machine-readable license and formal ethics documentation in inspected materials. This study does not claim redistribution rights, consent, or ethical approval. Reproducibility materials should be restricted to code where permitted, configurations, hashes, aggregate results, and non-identifying error categories; raw profiles and decision data must not be released without source-owner permission.

<!-- EDIT CAREFULLY: Threats-to-validity wording. -->
Internal validity is strengthened by entity-level role assignment and dropped cross-role pairs. Construct validity is limited because REVIEW is not a measured reviewer outcome. The conditional bootstrap estimates uncertainty over scored candidates in one frozen test population while holding exact-tier and blocking-miss constants fixed. External validity is limited by three historical social platforms and archived profile fields. Platform-pair differences show that aggregate performance can conceal heterogeneous errors. The 12-scenario analysis also shows that GB-18-GA is not preferred for every utility configuration.

# VII. CONCLUSION

<!-- SAFE TO REWORD: Conclusion wording. Preserve evidence limits and trade-offs. -->
This study evaluated a staged cross-platform profile-linkage pipeline in which a GA selects a three-way operating policy over frozen calibrated pair probabilities. Across three repeated entity-disjoint outer splits, the policy improved F1, recall, and the declared utility scenario relative to fixed-threshold GB-18, while increasing false positives and REVIEW outcomes. The MiniLM fixed-threshold ablation showed mixed repeated-split behavior. Candidate coverage remained binding: approximately 11.3% of labeled positive pairs were unavailable to downstream scoring. These findings support a bounded operating trade-off on LinkSocial, not a new GA or three-way linkage method, universal utility reduction, or generalization beyond the evaluated corpus.

# REFERENCES

[1] V. Sharma and C. E. Dyreson, “LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms,” 2018 IEEE International Conference on Big Knowledge, 2018, IEEE Xplore document 8588801.

[2] G. Papadakis, D. Skoutas, E. Thanos, and T. Palpanas, “Blocking and Filtering Techniques for Entity Resolution: A Survey,” ACM Computing Surveys, vol. 53, no. 2, 2021, doi: 10.1145/3377455.

[3] T. Ouyang, W. Pedrycz, and N. J. Pizzi, “Record Linkage Based on a Three-Way Decision with the Use of Granular Descriptors,” Expert Systems with Applications, vol. 122, pp. 16–26, 2019, doi: 10.1016/j.eswa.2018.12.038.

[4] C. Sun, D. Shen, Y. Kou, T. Nie, and G. Yu, “A Genetic Algorithm Based Entity Resolution Approach with Active Learning,” Frontiers of Computer Science, vol. 11, no. 1, pp. 147–159, 2017, doi: 10.1007/s11704-015-5276-6.

[5] X. Yao, “User Identity Linkage Across Multiple Social Network Based on Profile Features,” in Proceedings of the 2023 7th International Conference on Electronic Information Technology and Computer Engineering, 2023, pp. 1317–1323, doi: 10.1145/3650400.3650622.

[6] P. Christen, S. Ziyad, and C. Nanayakkara, “Consistently Evaluating Record Linkage Classifiers,” Journal of Data and Information Quality, vol. 18, no. 1, 2026, doi: 10.1145/3786768.

[7] B.-H. Li, Y. Liu, A.-M. Zhang, W.-H. Wang, and S. Wan, “A Survey on Blocking Technology of Entity Resolution,” Journal of Computer Science and Technology, vol. 35, pp. 769–793, 2020, doi: 10.1007/s11390-020-0350-4.
