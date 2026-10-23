# ICSEC 2026 Submission Information

## Final paper title

Genetic Optimization of Three-Way Operational Decisions for Cross-Platform Profile Identity Resolution

## Abstract

Cross-platform identity resolution must link incomplete social-media profiles while controlling false merges, missed matches, and cases retained for review. Pair classifiers supply scores, but operational deployment requires a policy that separates automatic matches, rejections, and uncertain cases. This paper evaluates a staged profile-linkage pipeline on a transformed derivative of the LinkSocial corpus containing Twitter, Google+, and Instagram profiles. A Gradient Boosting baseline using 17 handcrafted profile-pair features (GB-17) is compared with an augmentation by MiniLM cosine similarity (GB-18). A genetic algorithm then selects a four-parameter MATCH/REVIEW/NO_MATCH policy on validation entities while retaining calibrated GB-18 probabilities unchanged. Evaluation uses three repeated outer entity-disjoint partitions with distinct model-training, calibration, policy-selection, and test entities. The GA policy achieves mean F1 of 0.8603, versus 0.8280 for fixed-threshold GB-18, and lowers a declared illustrative utility from 2271.8 to 1802.7. It also increases mean false positives from 38.0 to 75.7 and review decisions from 438.0 to 923.3. The MiniLM fixed-threshold ablation is mixed across outer splits. Candidate generation reduces 449,149,239 possible cross-platform comparisons to 2,086,245 candidates but covers 88.6742% of 29,243 labeled positive pairs, limiting attainable end-to-end recall. Findings are limited to LinkSocial and the declared utility scenario.

## Index terms

Entity resolution; record linkage; cross-platform identity linkage; evolutionary computing; cost-sensitive decision policy; machine learning.

## Primary ICSEC topic

Evolutionary Computing

## Secondary ICSEC topic

Machine Learning and Deep Learning

## Topics not selected

Artificial Intelligence, Natural Language Processing, Data and Knowledge Management, Human Machine Interface, Computer Vision and Image Processing, Software Engineering.

## One-sentence research problem

How can a cross-platform profile-linkage pipeline select MATCH, REVIEW, and NO_MATCH decisions from calibrated pair scores while transparently balancing false positives, missed matches, and review volume?

## One-sentence research gap

Prior work establishes three-way record linkage and GA-based ER separately, but this study evaluates a leakage-safe operational composition of calibrated semantic profile scoring and validation-only evolutionary policy selection with explicit retrieval-ceiling analysis.

## One-sentence proposed method

A GA optimizes a four-gene three-way decision policy on validation entities using frozen calibrated GB-18 probabilities and name evidence, then is evaluated on disjoint outer test entities.

## Short Paper Summary

This paper evaluates a validation-only GA policy that assigns MATCH, REVIEW, or NO_MATCH decisions over frozen calibrated social-profile pair scores. Across three entity-disjoint outer partitions on LinkSocial, the policy improves F1 and the declared illustrative utility relative to fixed-threshold GB-18 while increasing false positives and review volume; candidate-generation recall remains the primary end-to-end limitation.

## Research Contributions

- Separates pair-model training, calibration, GA policy selection, and sealed entity-disjoint testing.
- Isolates MiniLM representation and GA decision-policy effects using GB-17, GB-18, and GB-18-GA ablations.
- Reports repeated-split policy trade-offs together with the candidate-retrieval recall ceiling.

## Three main contributions

1. Entity-disjoint training, calibration, policy-selection, and test evaluation for cross-platform profile linkage.
2. Controlled ablation of a MiniLM cosine representation feature and a frozen-score GA decision policy.
3. Repeated outer-split measurement of policy trade-offs and candidate-retrieval recall ceiling.

## Submission caution

The utility coefficients are illustrative operational assumptions, and the dataset source has no verified machine-readable reuse license. Do not claim economic cost, broad generalization, or unrestricted data release.
