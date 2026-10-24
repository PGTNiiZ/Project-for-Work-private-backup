# Detailed Report: Model Weights and Feature-Aware GA

## Scope and Interpretation

This automated run answers two distinct questions on the labeled feature population in
`pub_multi/data/train_all.parquet` (**58,696 pairs**):

1. Which feature groups help a pair-scoring model predict identity probability?
2. Which evidence group should guard GA decisions in the review band, and which available
   evidence weights minimize business decision cost?

This is **not** a full-production decision report. The historical GA cache contains 2,073,842
scored candidates, while the labeled feature matrix overlaps with only 20,757 of them (1.00%).
The report is valid for model/feature research; production GA promotion requires rebuilding the
same availability-aware cache for every full candidate pair.

## What Was Done

1. Created `decisioning_features.parquet` with raw evidence scores plus a separate availability
   mask for name, bio, URL, location, image, and style. Missing evidence is never treated as
   negative similarity.
2. Trained Logistic Regression for readable standardized coefficients and Gradient Boosting for
   non-linear pair scoring. Model selection used validation AP only.
3. Ran GA selector policies: score-only plus one availability-gated evidence guard per eligible group.
4. Ran a weighted GA policy. It learned non-negative evidence weights whose available weights
   normalize per pair; unavailable fields contribute neither score nor denominator.
5. Evaluated test only after each GA policy was selected on validation.

## Pair-Scoring Model

Selected model: **gradient_boosting**

| Validation AP | AUC | Precision | Recall | F1 | Threshold |
|---:|---:|---:|---:|---:|---:|
| 0.979692 | 0.972393 | 0.9688 | 0.8997 | 0.9330 | 0.51 |

The readable Linear-model coefficients are in `logistic_coefficients.csv`. The model-independent
validation importance is in `grouped_permutation_importance_validation.csv`; use these together,
not a single coefficient, when deciding a feature role.

## Coverage and Reliability

| Evidence group | Availability coverage | Positive support when available | Positive rate when score >= 0.5 | Eligible for global GA weight |
|---|---:|---:|---:|---|
| name | 99.42% | 4,355 | 0.596 | yes |
| bio | 66.18% | 3,005 | 0.954 | yes |
| url | 67.93% | 3,148 | 0.941 | yes |
| location | 0.00% | 0 | 0.000 | no |
| image | 10.02% | 450 | 1.000 | yes |
| style | 66.18% | 3,005 | 0.533 | yes |

An ineligible group is not automatically useless. It is too sparse to receive a global GA weight
in this run and remains a candidate for an availability-gated override after full-candidate coverage is rebuilt.

## GA Guard Comparison

| Guard | Validation cost | Val precision | Val recall | Val FP | Val FN | Val review |
|---|---:|---:|---:|---:|---:|---:|
| bio | 150.34 | 0.9989 | 0.6040 | 3 | 56 | 3967 |
| style | 151.66 | 0.9988 | 0.5885 | 3 | 56 | 4033 |
| score_only | 151.72 | 0.9988 | 0.5882 | 3 | 56 | 4036 |
| image | 152.68 | 0.9988 | 0.5882 | 3 | 57 | 4034 |
| url | 156.64 | 0.9985 | 0.5889 | 4 | 56 | 4032 |
| name | 468.36 | 0.9787 | 0.7241 | 69 | 56 | 3368 |

Validation winner: **bio**. Its genome and all generation histories are in
`selector_generation_history.json` and `selector_leaderboard.csv`.

## Weighted Evidence GA

The selected weighted policy uses these availability-conditioned weights:

| Evidence group | GA weight |
|---|---:|
| name | 0.3939 |
| bio | 0.0000 |
| url | 0.1186 |
| image | 0.1833 |
| style | 0.3043 |

Validation metrics: `{"fp": 28, "fn": 56, "review": 3892, "precision": 0.9897323065639897, "recall": 0.6153670770633834, "f1": 0.7588921692675383, "cost": 273.84000000000003}`

The weighted policy is selected on validation only. The one policy with lowest validation cost
between the selector winner and weighted policy is frozen before test.

## One Sealed Test Evaluation

Frozen policy: **selector:bio**

Test metrics: `{"fp": 7, "fn": 63, "review": 3812, "precision": 0.9973138910207214, "recall": 0.5924321860041031, "f1": 0.7433147433147432, "cost": 174.24}`

## Conclusion

The model-weight stage and GA stage are deliberately separate. The pair-scoring model learns
probability from feature values and masks; the GA never changes those model parameters. GA only
chooses how the frozen probability and available evidence make MATCH/REVIEW/NO_MATCH decisions.
Before promoting this policy to production, rebuild `decisioning_features.parquet` for the full
2.07M scored candidate population, repeat the coverage audit, then perform one new sealed test.
