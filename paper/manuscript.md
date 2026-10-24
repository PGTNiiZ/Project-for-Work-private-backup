# Genetic Optimization of Three-Way Operational Decisions for Cross-Platform Profile Identity Resolution

## Abstract

Cross-platform identity resolution must link incomplete social-media profiles while controlling false merges, missed matches, and cases retained for review. Pair classifiers supply scores, but operational deployment requires a policy that separates automatic matches, rejections, and uncertain cases. This paper evaluates a staged profile-linkage pipeline on a transformed derivative of the LinkSocial corpus containing Twitter, Google+, and Instagram profiles. A Gradient Boosting baseline using 17 handcrafted profile-pair features (GB-17) is compared with an augmentation by MiniLM cosine similarity (GB-18). A genetic algorithm then selects a four-parameter MATCH/REVIEW/NO_MATCH policy on validation entities while retaining calibrated GB-18 probabilities unchanged. Evaluation uses three repeated outer entity-disjoint partitions with distinct model-training, calibration, policy-selection, and test entities. The GA policy achieves mean F1 of 0.8603, versus 0.8280 for fixed-threshold GB-18, and lowers a declared illustrative utility from 2271.8 to 1802.7. It also increases mean false positives from 38.0 to 75.7 and review decisions from 438.0 to 923.3. The MiniLM fixed-threshold ablation is mixed across outer splits. Candidate generation reduces 449,149,239 possible cross-platform comparisons to 2,086,245 candidates but covers 88.6742% of 29,243 labeled positive pairs, limiting attainable end-to-end recall. Findings are limited to LinkSocial and the declared utility scenario; they do not establish generalization, measured business benefit, or a new three-way or evolutionary entity-resolution method.

## Index Terms

Entity resolution, record linkage, cross-platform identity linkage, evolutionary computing, cost-sensitive decision policy, machine learning.

# I. Introduction

People may maintain profiles on multiple social platforms while identifiers, names, biographies, links, and locations differ or are incomplete. Linking these profiles supports data integration but creates asymmetric risks: incorrect merges and missed links have different operational consequences. Profile linkage commonly uses similarity features and supervised pair classification [1], [5]. Candidate generation is also necessary because exhaustive entity-resolution comparison is quadratic [2], [7].

A pair score does not itself specify an operating decision. A system must decide whether to accept a pair, reject it, or retain it for review. Three-way record linkage is established [3], as are evolutionary approaches to entity resolution [4]. Therefore, this work does not claim novelty for GA optimization or three-way linkage. It evaluates a separated operational composition: semantic-enhanced calibrated pair scoring followed by validation-only genetic selection of a three-way policy under entity-disjoint evaluation.

We investigate: RQ1, how does a MiniLM cosine feature affect fixed-threshold workflow outcomes? RQ2, given frozen calibrated GB-18 probabilities, how does a GA-selected three-way policy alter precision, recall, F1, review volume, and an illustrative utility? RQ3, how strongly does candidate-generation recall constrain end-to-end resolution? Contributions are: 1) an entity-disjoint protocol separating training, calibration, policy selection, and testing; 2) controlled representation and decision-policy ablations; 3) repeated outer-split evidence for the policy trade-off; and 4) retrieval-to-decision failure decomposition.

# II. Related Work

Blocking and filtering reduce ER candidate sets but may exclude true pairs, making candidate coverage distinct from downstream classification [2], [7]. This motivates reporting retrieval recall and blocking misses separately from scoring results.

Profile-based user identity linkage uses string, short-text, and semi-structured attributes with machine-learning models [5]. This paper follows that profile-based setting but studies the policy applied after a calibrated score is produced. Three-way record linkage has been studied through granular descriptors [3], while GA-based ER with active learning has also been studied [4]. These works preclude claims that the basic decision formulation or evolutionary method is new.

Application-specific linkage evaluation can require more than a single aggregate classification measure [6]. Accordingly, the present study reports FP, FN, review count, precision, recall, F1, and declared utility together. Its contribution is empirical evidence for a staged composition, not a claim of the first combination of calibrated probabilities, semantic features, and a GA policy.

# III. Method

## A. Data, Labels, and Candidate Generation

Experiments use a locally transformed derivative of the public LinkSocial corpus [1], with 36,807 profiles from Twitter, Google+, and Instagram. A positive pair has the same non-empty source entity identifier. The public source documents usernames, full names, biographies, external URLs, bi-grams, and profile-image URLs for some platforms [1]. The source repository does not state a machine-readable reuse license or formal ethics documentation; raw records are not redistributed.

Candidate generation combines an exact tier with username-prefix, full-name-prefix, and external-domain blocking. It retains 2,086,245 pairs from 449,149,239 possible cross-platform comparisons. Of 29,243 labeled positive pairs, 25,931 enter the candidate workflow and 3,312 do not, yielding retrieval recall 0.886742. Any downstream model or policy is constrained by this coverage.

## B. Pair Models

GB-17 uses a `GradientBoostingClassifier` with 17 handcrafted pair features: username/full-name Jaro, normalized Levenshtein, and token similarities; cross-field name similarity; bio overlap/length features; location features; platform and availability indicators; and length/prefix features. GB-18 adds only `bert_cos`, the cosine similarity of normalized `all-MiniLM-L6-v2` embeddings of concatenated full name, biography, and location.

Both variants use 300 estimators, learning rate 0.05, maximum depth 6, and seed 42. Training negatives are deterministically undersampled to a 3:1 negative-to-positive ratio. Isotonic regression is fitted only on calibration entities. The fixed policy outputs MATCH for probability >=0.98, REVIEW for [0.95,0.98), and NO_MATCH otherwise.

## C. GA Decision Policy

GB-18-GA retains persisted calibrated GB-18 probabilities unchanged. It neither updates the Gradient Boosting classifier nor refits the calibrator. For calibrated probability p and name evidence n, the genome g=[t_m,t_r,c_p,c_d] has constraints 0.90<=t_m<=0.999, 0.50<=t_r<=t_m, 0.50<=c_p<=1, and 0<=c_d<=c_p. The policy returns MATCH when p>=t_m; within t_r<=p<t_m it returns MATCH when n>=c_p, NO_MATCH when n<c_d, and REVIEW otherwise; it returns NO_MATCH when p<t_r.

The GA uses five seeds {7,42,123,999,2025}, population 60, 40 generations, 12 elites, uniform crossover, and Gaussian mutation with probability 0.30 and standard deviation 0.02. Validation-only selection minimizes the illustrative utility

U = 2FP + FN + 0.1REVIEW.                                            (1)

Equation (1) is a declared scenario-specific objective, not a measured economic cost. All component metrics are reported alongside utility.

## D. Entity-Disjoint Evaluation

For each deterministic outer partition (seeds 101, 202, and 303), an MD5-based rule assigns approximately 30% of entities to outer test. Remaining entities are allocated to model training (70%), calibration (15%), and GA validation (15%). Cross-role candidate pairs are dropped. The implementation asserts no entity overlap across roles. Test labels are not accessed during training, calibration, GA optimization, or seed selection.

Workflow-level metrics include split-specific exact-tier outputs and blocking-missed positives as fixed constants. We report mean and standard deviation across outer partitions. On a separately frozen primary test role, a 2,000-resample paired conditional bootstrap estimates uncertainty over scored held-out candidate pairs while retaining exact/blocking constants fixed.

# IV. Results and Discussion

## A. Repeated Outer-Split Evaluation

| Method | F1 by outer seed (101/202/303) | Precision (mean±SD) | Recall (mean±SD) | F1 (mean±SD) | FP | FN | REVIEW | Utility |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | .8394/.7978/.8504 | .9909±.0051 | .7137±.0431 | .8292±.0277 | 59.0±35.8 | 2266.3±113.4 | 264.7±395.9 | 2410.8±98.9 |
| GB-18 | .8408/.8408/.8023 | .9940±.0010 | .7099±.0322 | .8280±.0222 | 38.0±7.0 | 2152.0±232.6 | 438.0±406.1 | 2271.8±198.5 |
| GB-18-GA | .8616/.8600/.8594 | .9889±.0054 | .7614±.0028 | .8603±.0011 | 75.7±38.4 | 1559.0±38.1 | 923.3±151.1 | 1802.7±68.3 |

RQ1 produces mixed evidence. On the separately frozen primary split, GB-18 raises F1 from 0.5963 to 0.8387. Across repeated outer splits, however, fixed-threshold GB-18 does not consistently exceed GB-17: its mean F1 is slightly lower and the seed-303 result is lower. MiniLM cosine is therefore a controlled representation component, not a consistently superior standalone fixed-threshold method on this corpus.

For RQ2, GB-18-GA has higher F1 than GB-18 in each outer partition, by 0.0208, 0.0192, and 0.0571. Mean recall rises from 0.7099 to 0.7614, and mean FN decreases from 2152.0 to 1559.0. This occurs with higher mean FP and review volume. Thus, the GA policy changes the operating trade-off; it is not uniformly better in every error dimension.

On the primary frozen split, conditional paired bootstrap intervals for GB-18-GA minus GB-18 exclude zero for F1 (+0.0235, 95% CI [+0.0208,+0.0262]), recall (+0.0386, [+0.0344,+0.0427]), FP (+32, [+22,+44]), FN (-266, [-299,-234]), REVIEW (+224, [+166,+283]), and utility (-179.6, [-214.7,-144.1]). These intervals are conditional on one scored test population and fixed retrieval constants; they are not population-level significance claims.

## B. Candidate-Generation Ceiling

RQ3 establishes a pipeline limitation, not a retrieval improvement. The 3,312 positives absent from candidates cannot be corrected by GB-17, GB-18, or the GA policy. Across outer test partitions, candidate recall is 0.8838±0.0002 with 1023.7±10.2 blocking-missed positives. Pair-model improvements should therefore not be interpreted as complete end-to-end resolution improvements.

## C. Utility Sensitivity

A 12-scenario frozen-policy sensitivity analysis varies FP penalty {1,2,5,10} and REVIEW penalty {0.02,0.1,0.5}, fixing FN penalty at 1. GB-18-GA has lowest utility in 8 of 12 scenarios, not all. Policies were not retuned after changing scenarios; the analysis describes sensitivity and does not select a new test policy.

# V. Limitations, Ethics, and Threats to Validity

This experiment evaluates a single transformed corpus and does not establish outcomes for other platforms, languages, time periods, or datasets. Only three outer partitions are used. The source labels may contain noise. The utility coefficients are illustrative assumptions, not measured business cost. Candidate blocking omits positives before scoring, and no improved blocking method is proposed. REVIEW is an offline policy output, not observed human-review workload or accuracy.

The public LinkSocial repository identifies the source corpus but lacks a machine-readable license and formal ethics documentation in the inspected materials. The study does not claim redistribution rights, consent, or ethical approval. Reproducibility materials should be limited to code where permitted, configurations, hashes, aggregate results, and non-identifying error categories; raw profile records and decision data must not be released without source-owner permission.

# VI. Conclusion

This work evaluated a staged cross-platform profile-linkage pipeline in which a GA selects a three-way operating policy over frozen calibrated pair probabilities. Across three repeated entity-disjoint outer splits, the policy improved F1, recall, and the declared utility scenario relative to fixed-threshold GB-18, while increasing false positives and review outcomes. The MiniLM fixed-threshold ablation showed mixed repeated-split behavior. Candidate coverage remained a binding constraint: approximately 11.3% of labeled positive pairs were unavailable to downstream scoring. These findings support a bounded operating trade-off on LinkSocial, not a new GA or three-way linkage method, universal cost reduction, or generalization beyond the evaluated corpus.

# References

[1] V. Sharma and C. E. Dyreson, “LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms,” 2018 IEEE International Conference on Big Knowledge, 2018, IEEE Xplore document 8588801.

[2] G. Papadakis, D. Skoutas, E. Thanos, and T. Palpanas, “Blocking and Filtering Techniques for Entity Resolution: A Survey,” ACM Computing Surveys, vol. 53, no. 2, 2021, doi: 10.1145/3377455.

[3] T. Ouyang, W. Pedrycz, and N. J. Pizzi, “Record Linkage Based on a Three-Way Decision with the Use of Granular Descriptors,” Expert Systems with Applications, vol. 122, pp. 16–26, 2019, doi: 10.1016/j.eswa.2018.12.038.

[4] C. Sun, D. Shen, Y. Kou, T. Nie, and G. Yu, “A Genetic Algorithm Based Entity Resolution Approach with Active Learning,” Frontiers of Computer Science, vol. 11, no. 1, pp. 147–159, 2017, doi: 10.1007/s11704-015-5276-6.

[5] X. Yao, “User Identity Linkage Across Multiple Social Network Based on Profile Features,” in Proceedings of EITCE 2023, 2023, pp. 1317–1323, doi: 10.1145/3650400.3650622.

[6] P. Christen, S. Ziyad, and C. Nanayakkara, “Consistently Evaluating Record Linkage Classifiers,” Journal of Data and Information Quality, vol. 18, no. 1, 2026, doi: 10.1145/3786768.

[7] B.-H. Li, Y. Liu, A.-M. Zhang, W.-H. Wang, and S. Wan, “A Survey on Blocking Technology of Entity Resolution,” Journal of Computer Science and Technology, vol. 35, pp. 769–793, 2020, doi: 10.1007/s11390-020-0350-4.
