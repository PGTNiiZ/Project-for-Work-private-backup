# Frozen Novelty Statement

## WHAT IS ALREADY KNOWN

Entity resolution, social-profile linkage, candidate blocking, semantic text representations, three-way record-linkage decisions, and evolutionary optimization for entity resolution are established research directions.

## WHAT PRIOR WORK ALREADY DOES

- Ouyang, Pedrycz, and Pizzi (2019) apply three-way decision theory to record linkage.
- Sun et al. (2017) apply a genetic-algorithm-based approach to entity resolution.
- Yao (2023) studies cross-social-network identity linkage using profile-feature similarity and machine learning.
- Recent record-linkage evaluation work recognizes that application-dependent error trade-offs cannot be represented adequately by a single conventional metric alone.

## WHAT THIS PAPER DOES DIFFERENTLY

This paper evaluates a deliberately separated operational pipeline on the LinkSocial profile corpus: a calibrated GB-18 pair scorer is frozen before a GA selects a MATCH/REVIEW/NO_MATCH policy on disjoint validation entities. The study then measures the pair-representation ablation, decision-policy ablation, candidate-retrieval ceiling, and policy trade-offs across repeated outer entity-disjoint test partitions.

## WHY THE DIFFERENCE MATTERS

The separation makes it possible to attribute observed changes to either the MiniLM representation or the three-way decision policy rather than conflate them with score-model retraining. Repeated outer partitions show that the GA policy's recall/F1/declared-utility trade-off is more stable than the standalone fixed-threshold MiniLM ablation on this corpus. Retrieval misses are reported explicitly, preventing pair-level improvements from being presented as complete end-to-end resolution improvements.

## WHAT WE DO NOT CLAIM AS NOVEL

- We do not claim to introduce genetic algorithms for entity resolution.
- We do not claim to introduce three-way entity resolution or reject-option classification.
- We do not claim MiniLM, Gradient Boosting, isotonic calibration, or blocking as new methods.
- We do not claim measured business cost, real CRM impact, human-review effectiveness, privacy protection, or generalization beyond the LinkSocial corpus.
- We do not claim the first combination of these components; the literature search did not establish that absence conclusively.
