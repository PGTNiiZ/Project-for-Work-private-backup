# Verified Related Work and Novelty Audit

This is a verified working ledger, not yet the paper's Related Work section. Bibliographic fields below were checked against publisher or Crossref metadata.

## A. Entity resolution and candidate generation

### Papadakis, Skoutas, Thanos, and Palpanas (2021)

- Title: *Blocking and Filtering Techniques for Entity Resolution: A Survey*
- Venue: ACM Computing Surveys, 53(2), 2021.
- DOI: 10.1145/3377455
- Problem/method: surveys blocking and filtering methods that reduce ER's quadratic pairwise-comparison cost.
- Relationship: directly supports reporting candidate-space reduction and candidate recall separately from scoring quality.
- Difference: this work does not present a three-way GA policy; it is a blocking/filtering survey.

### Li, Liu, Zhang, Wang, and Wan (2020)

- Title: *A Survey on Blocking Technology of Entity Resolution*
- Venue: Journal of Computer Science and Technology, 35, 769–793, 2020.
- DOI: 10.1007/s11390-020-0350-4
- Problem/method: surveys blocking as approximate candidate generation for ER and emphasizes that blocking reduces computational cost while potentially omitting true pairs.
- Relationship: supports the study's retrieval-recall and recall-ceiling analysis.
- Difference: no cross-platform social-profile three-way GA policy.

## B. Social-profile identity linkage

### Yao (2023)

- Title: *User Identity Linkage Across Multiple Social Network Based on Profile Features*
- Venue: Proceedings of EITCE 2023.
- DOI: 10.1145/3650400.3650622
- Problem/method: links users across social networks using string, short-text, and semi-structured profile attributes with an integrated machine-learning model.
- Evaluation: reports profile-feature-based identity linkage; publisher page does not establish a directly comparable three-way review policy.
- Relationship: nearest recent profile-feature UIL comparator.
- Difference: our frozen experiment evaluates a MiniLM feature ablation and a separate validation-selected MATCH/REVIEW/NO_MATCH policy on calibrated probabilities.

### Senette, Siino, and Tesconi (2024 preprint)

- Title: *User Identity Linkage on Social Networks: A Review of Modern Techniques and Applications*
- Identifier: arXiv:2409.08966v1.
- Status: preprint; not a peer-reviewed primary result source.
- Contribution: reviews 2016–2024 UIL methods, inputs, datasets, and evaluation; it identifies LinkSocial as a Twitter–Instagram–Google+ dataset and cites Sharma and Dyreson (2018).
- Relationship: useful discovery/provenance lead, not sufficient proof of the final research gap.

## C. Three-way entity decisions and evolutionary optimization

### Ouyang, Pedrycz, and Pizzi (2019)

- Title: *Record linkage based on a three-way decision with the use of granular descriptors*
- Venue: Expert Systems with Applications, 122, 16–26, 2019.
- DOI: 10.1016/j.eswa.2018.12.038
- Problem/method: explicitly applies a three-way decision formulation to record linkage using granular descriptors.
- Relationship: proves that three-way record-linkage decisions are prior art.
- Difference: verified metadata does not indicate a GA optimizing a cost-sensitive policy over calibrated probabilities; the final paper must not claim novelty for the existence of MATCH/REVIEW/NO_MATCH alone.

### Sun, Shen, Kou, Nie, and Yu (2017)

- Title: *A genetic algorithm based entity resolution approach with active learning*
- Venue: Frontiers of Computer Science, 11(1), 147–159, 2017.
- DOI: 10.1007/s11704-015-5276-6
- Problem/method: combines genetic-algorithm-based entity resolution with active learning.
- Relationship: proves that applying evolutionary methods to ER is prior art.
- Difference: it is not evidence that the exact frozen policy—cost-sensitive optimization of a three-way review policy on fixed calibrated profile-pair probabilities—was previously evaluated.

### Christen, Ziyad, and Nanayakkara (2026)

- Title: *Consistently Evaluating Record Linkage Classifiers*
- Venue: Journal of Data and Information Quality, 18(1), 2026.
- DOI: 10.1145/3786768
- Problem/method: proposes application-focused evaluation under acceptable error rates and warns that standard summary measures can select a suboptimal linkage classifier.
- Relationship: supports reporting a declared operational objective and error trade-offs rather than F1 alone.
- Difference: it does not constitute a GA three-way policy-optimization method.

## Critical novelty conclusion

The literature search falsifies two broad novelty claims:

1. Three-way record linkage is not new (Ouyang et al.).
2. Genetic/evolutionary entity resolution is not new (Sun et al.).

A narrower, defensible candidate contribution remains:

> A leakage-safe empirical evaluation of a validation-selected GA policy that optimizes a three-way decision rule on fixed calibrated MiniLM-enhanced cross-platform social-profile pair probabilities, with explicit blocking-recall failure decomposition.

This is a combination-and-evaluation contribution, not a claim of a fundamentally new GA, three-way decision model, or entity-resolution paradigm.

Has prior work already optimized exactly this policy?

- No exact match was found in the verified sources above.
- This is not proof of absence. Before submission, perform a final database search in IEEE Xplore, ACM DL, Scopus/Web of Science, and Google Scholar using the exact query family: `("entity resolution" OR "record linkage") AND (genetic OR evolutionary) AND ("three-way" OR reject OR review) AND (cost OR utility OR threshold) AND calibrated`.
- Until that expanded search is archived, phrase novelty conservatively as a evaluated combination, not as the first such system.

## Source URLs

- https://doi.org/10.1145/3377455
- https://doi.org/10.1007/s11390-020-0350-4
- https://doi.org/10.1145/3650400.3650622
- https://arxiv.org/abs/2409.08966
- https://doi.org/10.1016/j.eswa.2018.12.038
- https://doi.org/10.1007/s11704-015-5276-6
- https://doi.org/10.1145/3786768
