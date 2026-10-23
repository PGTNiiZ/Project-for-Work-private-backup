# Cost-Sensitive Genetic Optimization of a Three-Way Decision Policy for Cross-Platform Profile Identity Resolution

## Abstract

Cross-platform identity resolution must link incomplete social-media profiles while controlling false merges, missed matches, and the volume of cases sent to review. Conventional pair classifiers provide scores, but their operational deployment requires a decision policy that distinguishes automatic matches, rejections, and uncertain cases. This paper evaluates a staged profile-linkage pipeline on a transformed derivative of the LinkSocial corpus containing profiles from Twitter, Google+, and Instagram. A Gradient Boosting baseline using 17 handcrafted profile-pair features (GB-17) is compared with a representation augmented by MiniLM cosine similarity (GB-18). A genetic algorithm then optimizes a four-parameter MATCH/REVIEW/NO_MATCH policy on validation entities while retaining the calibrated GB-18 probabilities unchanged. Evaluation uses three repeated outer entity-disjoint partitions, with separate model-training, calibration, policy-selection, and test entities. Across the outer partitions, the GA policy attains mean F1 of 0.8603 compared with 0.8280 for fixed-threshold GB-18, and reduces a declared illustrative utility from 2271.8 to 1802.7. This trade-off increases mean false positives from 38.0 to 75.7 and review decisions from 438.0 to 923.3. Candidate generation reduces 449,149,239 possible cross-platform comparisons to 2,086,245 candidates but covers 88.6742% of 29,243 labeled positive pairs, limiting attainable end-to-end recall. The findings are limited to this corpus and utility scenario; they do not establish generalization, measured business benefit, or a new three-way or evolutionary entity-resolution method.

## Index Terms

Entity resolution, record linkage, cross-platform identity linkage, evolutionary computing, cost-sensitive decision policy, machine learning.

# I. Introduction

A person may maintain profiles on multiple social platforms, yet identifiers, names, biographies, links, and locations are incomplete or inconsistent. Linking these profiles can support cross-platform data integration, but an incorrect merge can be more damaging than leaving accounts separate. Social-profile linkage research commonly derives profile similarities and uses supervised models to predict whether profile pairs match [1], [5]. Entity-resolution pipelines also require candidate generation because exhaustive pair comparison is quadratic [2], [7].

A scored pair classifier alone does not determine how a system should operate. A deployment policy must decide whether to accept a high-score pair, reject a low-score pair, or retain an ambiguous pair for review. Three-way record linkage is established [3], and evolutionary approaches to entity resolution are also established [4]. Thus, this work does not claim either technique as novel. Instead, it evaluates a separated operational composition: calibrated semantic-enhanced pair scoring followed by validation-only genetic optimization of a three-way decision policy under entity-disjoint partitions.

The study asks: RQ1, how does adding a MiniLM cosine feature affect fixed-threshold workflow outcomes? RQ2, given frozen calibrated GB-18 probabilities, how does a GA-selected three-way policy alter precision, recall, F1, review volume, and an explicit utility scenario? RQ3, how strongly does candidate-generation recall limit end-to-end resolution? The contributions are: (i) an entity-disjoint evaluation protocol separating training, calibration, policy selection, and testing; (ii) controlled representation and decision-policy ablations; (iii) repeated outer-split evidence for the decision policy and its trade-offs; and (iv) an explicit retrieval-to-decision error decomposition.

# II. Related Work

Blocking and filtering reduce the candidate space for entity resolution but can omit true matches, making coverage a distinct concern from downstream classification [2], [7]. This motivates reporting candidate recall and blocking misses rather than treating pair-classification metrics as full-workflow results.

For cross-platform user identity linkage, profile attributes may be represented as string, short-text, and semi-structured similarities and scored by machine-learning models [5]. Our setting follows this profile-based formulation, but focuses on the operational decision layer after a calibrated pair score is produced.

Three-way record linkage has been studied using granular descriptors [3], and genetic algorithms have been applied to entity resolution with active learning [4]. These works rule out claims that three-way decisions or evolutionary ER are new here. The present study instead tests a specific separation between a calibrated pair model and a GA policy, then evaluates it under repeated entity-disjoint partitions. Recent work also cautions that conventional aggregate metrics may be insufficient for application-dependent linkage selection [6]; accordingly, this study reports FP, FN, review volume, F1, and a declared utility together.

# III. Method

## A. Dataset, Labels, and Candidate Generation

The experiments use a locally transformed derivative of the public LinkSocial corpus [1]. The local derivative contains 36,807 profiles from Twitter, Google+, and Instagram. A positive pair consists of two profiles with the same non-empty source entity identifier. The source repository documents profile fields including username, full name, biography, external URL, and, for two platforms, profile-image URL [1]. Because the source repository does not state a machine-readable reuse license or formal ethics documentation, raw data are not redistributed and all reported examples are aggregate-only.

Candidate generation applies an exact tier and blocking keys derived from username prefix, full-name prefix, and external domain. Across platforms, the candidate workflow retains 2,086,245 pairs from 449,149,239 possible pairs. Of 29,243 labeled positive pairs, 25,931 are present in the candidate workflow; 3,312 are missed. Hence retrieval recall is 0.886742. The candidate stage therefore defines a recall ceiling for all downstream scorers and policies.

## B. Pair Models

GB-17 is a `GradientBoostingClassifier` trained on 17 handcrafted signals: username and full-name Jaro/Levenshtein/token similarities, cross-field name similarity, bio overlap and length features, location features, availability indicators, platform indicator, and length/prefix features. GB-18 adds exactly one feature, `bert_cos`: cosine similarity of normalized `all-MiniLM-L6-v2` embeddings of concatenated full name, biography, and location.

Both models use 300 estimators, learning rate 0.05, maximum depth 6, and seed 42. Training negatives are deterministically undersampled to a 3:1 negative-to-positive ratio. Isotonic regression is fitted only on calibration entities. The fixed-threshold baseline assigns MATCH for probability at least 0.98, REVIEW for probability in [0.95, 0.98), and NO_MATCH otherwise.

## C. Three-Way GA Policy

GB-18-GA does not update the model or calibrator. It uses the persisted calibrated GB-18 probability p and name evidence n. The genome g = [t_m, t_r, c_p, c_d] satisfies 0.90 <= t_m <= 0.999, 0.50 <= t_r <= t_m, 0.50 <= c_p <= 1, and 0 <= c_d <= c_p. Its decision function is

D(p,n) = MATCH if p >= t_m;
MATCH if t_r <= p < t_m and n >= c_p;
NO_MATCH if t_r <= p < t_m and n < c_d;
REVIEW otherwise in that band; and NO_MATCH if p < t_r.

The GA uses five seeds {7, 42, 123, 999, 2025}, population 60, 40 generations, 12 elites, uniform crossover, and Gaussian mutation (probability 0.30, standard deviation 0.02). The selected policy minimizes the illustrative utility

U = 2 FP + FN + 0.1 REVIEW.

This is a declared operational scenario rather than measured economic cost. The policy is selected solely on GA-validation entities; ties use the smallest seed.

## D. Leakage-Safe Evaluation

For each of three deterministic outer partitions (seeds 101, 202, and 303), entities are assigned to outer test when an MD5-based function yields a value below 30%; remaining entities are deterministically partitioned into model training (70%), calibration (15%), and GA validation (15%). Pairs whose endpoints cross roles are dropped. The implementation checks that entities do not overlap across roles. Test labels are not accessed during feature/model fitting, calibration, GA optimization, or seed selection.

Metrics are workflow-level precision, recall, F1, FP, FN, and REVIEW. Exact-tier results and outer-test blocking misses are included as fixed split-specific constants. We report mean and standard deviation over outer partitions. A 2,000-resample paired conditional bootstrap on the primary held-out scored pairs estimates uncertainty while holding exact/blocking constants fixed.

# IV. Results and Discussion

## A. Repeated Outer-Split Results

| Method | Precision | Recall | F1 | FP | FN | REVIEW | Utility |
|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 0.9909 ± 0.0051 | 0.7137 ± 0.0431 | 0.8292 ± 0.0277 | 59.0 ± 35.8 | 2266.3 ± 113.4 | 264.7 ± 395.9 | 2410.8 ± 98.9 |
| GB-18 | 0.9940 ± 0.0010 | 0.7099 ± 0.0322 | 0.8280 ± 0.0222 | 38.0 ± 7.0 | 2152.0 ± 232.6 | 438.0 ± 406.1 | 2271.8 ± 198.5 |
| GB-18-GA | 0.9889 ± 0.0054 | 0.7614 ± 0.0028 | 0.8603 ± 0.0011 | 75.7 ± 38.4 | 1559.0 ± 38.1 | 923.3 ± 151.1 | 1802.7 ± 68.3 |

RQ1 yields mixed evidence. On the separately frozen primary split, GB-18 improves F1 from 0.5963 to 0.8387. However, across repeated outer splits, GB-18 does not consistently exceed GB-17: its mean F1 is slightly lower and varies by split. Thus, MiniLM cosine is a controlled representation component but cannot be claimed as a consistently superior fixed-threshold method on this corpus.

For RQ2, GB-18-GA exceeds GB-18 F1 on all outer splits by 0.0208, 0.0192, and 0.0571, respectively. Its mean recall rises from 0.7099 to 0.7614 and its mean FN falls from 2152.0 to 1559.0. These gains trade against more FP and review outcomes. The result is therefore a policy trade-off, not a uniform improvement in every error dimension.

On the primary frozen split, paired conditional bootstrap intervals for GB-18-GA minus GB-18 exclude zero for F1 (+0.0235, 95% CI [+0.0208,+0.0262]), recall (+0.0386, [+0.0344,+0.0427]), FP (+32, [+22,+44]), FN (-266, [-299,-234]), REVIEW (+224, [+166,+283]), and declared utility (-179.6, [-214.7,-144.1]). These intervals condition on the scored held-out candidates and fixed exact/blocking constants; they do not establish population-level generalization.

## B. Candidate-Generation Constraint

RQ3 shows that 3,312 positives are absent before scoring. Across outer tests, candidate recall is 0.8838 ± 0.0002 and blocking misses are 1023.7 ± 10.2. This stability describes the fixed candidate generator, not a retrieval contribution. Improvements in scorer or policy performance therefore remain bounded by candidate coverage.

## C. Utility Sensitivity

The utility scenario is not universally favorable to GB-18-GA. A post-hoc 12-scenario analysis varies false-positive penalty {1,2,5,10} and review penalty {0.02,0.1,0.5}, with missed-match penalty fixed at 1. GB-18-GA has minimum frozen-policy utility in 8 of 12 scenarios. The policy is not re-optimized per scenario; hence the analysis demonstrates sensitivity rather than a new selection result.

# V. Limitations and Threats to Validity

The evaluation uses one transformed corpus and does not establish performance on other platforms, languages, time periods, or datasets. The LinkSocial source is publicly hosted but lacks a machine-readable license and formal ethics documentation in the inspected repository; this limits data release and reproducibility claims. The source labels are treated as ground truth but may contain noise. Only three outer partitions were evaluated. The utility coefficients are illustrative assumptions. Candidate blocking excludes positives before scoring, and no new blocking method is proposed. Finally, REVIEW counts are offline policy outputs, not observed human-review workload or accuracy.

# VI. Conclusion

This study evaluated a staged cross-platform profile-linkage pipeline in which a GA selects a three-way operational policy over fixed calibrated probabilities. Repeated entity-disjoint outer evaluation showed that the GA policy improved F1, recall, and the declared utility scenario relative to fixed-threshold GB-18, while increasing false positives and review decisions. The MiniLM feature’s fixed-threshold effect was not stable across outer partitions. Candidate coverage remained a binding limitation: approximately 11.3% of positive pairs were unavailable to downstream scoring. The findings support a bounded operational trade-off on LinkSocial, not a claim of new GA, three-way linkage, universal cost reduction, or broad generalization.

# References

[1] V. Sharma and C. E. Dyreson, “LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms,” 2018 IEEE International Conference on Big Knowledge, 2018, IEEE Xplore document 8588801.

[2] G. Papadakis, D. Skoutas, E. Thanos, and T. Palpanas, “Blocking and Filtering Techniques for Entity Resolution: A Survey,” ACM Computing Surveys, vol. 53, no. 2, 2021, doi: 10.1145/3377455.

[3] T. Ouyang, W. Pedrycz, and N. J. Pizzi, “Record Linkage Based on a Three-Way Decision with the Use of Granular Descriptors,” Expert Systems with Applications, vol. 122, pp. 16–26, 2019, doi: 10.1016/j.eswa.2018.12.038.

[4] C. Sun, D. Shen, Y. Kou, T. Nie, and G. Yu, “A Genetic Algorithm Based Entity Resolution Approach with Active Learning,” Frontiers of Computer Science, vol. 11, no. 1, pp. 147–159, 2017, doi: 10.1007/s11704-015-5276-6.

[5] X. Yao, “User Identity Linkage Across Multiple Social Network Based on Profile Features,” in Proceedings of EITCE 2023, 2023, pp. 1317–1323, doi: 10.1145/3650400.3650622.

[6] P. Christen, S. Ziyad, and C. Nanayakkara, “Consistently Evaluating Record Linkage Classifiers,” Journal of Data and Information Quality, vol. 18, no. 1, 2026, doi: 10.1145/3786768.

[7] B.-H. Li, Y. Liu, A.-M. Zhang, W.-H. Wang, and S. Wan, “A Survey on Blocking Technology of Entity Resolution,” Journal of Computer Science and Technology, vol. 35, pp. 769–793, 2020, doi: 10.1007/s11390-020-0350-4.
