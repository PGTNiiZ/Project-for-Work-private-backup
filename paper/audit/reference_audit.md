Reference audit — Cross-Platform Profile Identity Resolution

Audit date: 2026-09-03 (Asia/Bangkok)
Scope: paper/overleaf/main.tex and paper/overleaf/references.bib, plus targeted literature searches in ACM DL, IEEE Xplore, Springer, ScienceDirect, Google Scholar result pages, Crossref metadata, arXiv, ACL Anthology, and the LinkSocial repository.

This is an independent, read-only audit. No protected manuscript, bibliography, or figure file was edited. “Verified” means that the title/authors/year/venue/identifier were confirmed from a publisher, proceedings, DOI landing page, or official repository. Search-result snippets were used for discovery, not as sole evidence for substantive claims.

1. Existing citation verification

All seven bibliography keys are cited in main.tex; there are no uncited bibliography entries and no citation keys in main.tex absent from references.bib.

| Key | Bibliographic verification | Status | Claim support and audit finding |
|---|---|---|---|
| linkSocial2018 | Vishal Sharma and Curtis E. Dyreson, “LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms,” 2018 IEEE International Conference on Big Knowledge (ICBK), 2018, pp. 260–267, IEEE Xplore document 8588801. Official dataset repository: https://github.com/vishalshar/Dataset-LinkSocial | PARTIALLY VERIFIED | Title, authors, year, venue, pages, and IEEE identifier are supported by the official repository and IEEE-discovery records. The BibTeX entry omits pages and DOI; no DOI was confirmed in this audit. Supports dataset provenance and the general statement that profile linkage uses profile attributes. It does not support the manuscript’s transformed-data counts, license/ethics conclusion, or experimental results; those require repository/artifact evidence. |
| papadakis2021blocking | George Papadakis, Dimitrios Skoutas, Emmanouil Thanos, and Themis Palpanas, “Blocking and Filtering Techniques for Entity Resolution: A Survey,” ACM Computing Surveys 53(2), 2021, DOI 10.1145/3377455. | VERIFIED | Publisher abstract explicitly describes quadratic ER, blocking, filtering, and candidate restriction. Supports the blocking motivation and the distinction between candidate generation and downstream matching. It does not validate this paper’s candidate counts or recall. |
| ouyang2019threeway | Tinghui Ouyang, Witold Pedrycz, and Nick J. Pizzi, “Record Linkage Based on a Three-Way Decision with the Use of Granular Descriptors,” Expert Systems with Applications 122, 16–26, 2019, DOI 10.1016/j.eswa.2018.12.038. | VERIFIED | DOI/ScienceDirect result and bibliographic records confirm the paper. The publisher description states that three-way decision is applied to record linkage and granular descriptors are used. Supports the statement that three-way linkage is established and therefore should not be claimed as novel. It does not support the manuscript’s particular genome or thresholds. |
| sun2017gaer | Chenchen Sun, Derong Shen, Yue Kou, Tiezheng Nie, and Ge Yu, “A Genetic Algorithm Based Entity Resolution Approach with Active Learning,” Frontiers of Computer Science 11(1), 147–159, 2017, DOI 10.1007/s11704-015-5276-6. | VERIFIED | Springer page confirms exact title, authors, publication date/year, venue, pages, DOI, and an abstract describing GA-learned match rules with active learning. Supports the statement that evolutionary/GA-based ER is prior art. It does not support a claim that this manuscript’s GA policy, calibrated probabilities, or three-way operating rule is prior art. |
| yao2023profile | Xiaolin Yao, “User Identity Linkage Across Multiple Social Network Based on Profile Features,” Proceedings of the 2023 7th International Conference on Electronic Information Technology and Computer Engineering, 2023, pp. 1317–1323, DOI 10.1145/3650400.3650622. | VERIFIED | ACM page confirms metadata and describes string, short-text, and semi-structured profile attributes combined with machine-learning models. Supports the direct social-profile comparator statement. It does not establish comparability with LinkSocial, entity-disjoint evaluation, calibration, or the paper’s results. |
| christen2026consistent | Peter Christen, Sumayya Ziyad, and Charini Nanayakkara, “Consistently Evaluating Record Linkage Classifiers,” Journal of Data and Information Quality 18(1), 2026, DOI 10.1145/3786768. | VERIFIED | ACM page confirms exact metadata and describes the Consistent Record Linkage measure, application-focused error constraints, and threshold robustness. Supports the argument for reporting application-relevant error trade-offs beyond one aggregate metric. It does not support the manuscript’s illustrative utility equation or imply that CRL and the GA policy are equivalent. |
| li2020blocking | Bo-Han Li, Yu Liu, An-Man Zhang, Wen-Huan Wang, and Shuo Wan, “A Survey on Blocking Technology of Entity Resolution,” Journal of Computer Science and Technology 35, 769–793, 2020, DOI 10.1007/s11390-020-0350-4. | VERIFIED | Springer/Crossref bibliographic records confirm metadata and the survey topic. Supports blocking as approximate comparison reduction and the need to account for missed matches. It does not verify this implementation’s blocking rules or recall. |

Existing citation-placement audit:
- Introduction line 37: adequately supports the general profile-linkage and quadratic-blocking motivation, but “asymmetric operational risks” is uncited.
- Introduction line 39 and Related Work lines 50–52: adequately support the claims that three-way linkage, GA-based ER, blocking, and application-focused evaluation have precedents.
- Methodology lines 59–61: LinkSocial is appropriate for source provenance; all numerical values and the reuse/licensing statement are manuscript/repository audit claims, not claims established by the citation alone.
- No existing citation supports MiniLM, isotonic regression, Jaro/Levenshtein, gradient boosting, calibration methodology, reject-option classification, leakage-safe entity-disjoint splitting, or bootstrap methodology. These are the principal citation gaps.

2. Suggested additional references

The following references were independently verified or strongly identified through publisher/official proceedings metadata and are suitable additions if the manuscript’s protected bibliography is later revised. They are recommendations only; they have not been added.

A. Entity resolution / record linkage foundations and evaluation

1. Ivan P. Fellegi and Alan B. Sunter, “A Theory for Record Linkage,” Journal of the American Statistical Association 64(328), 1183–1210, 1969, DOI 10.1080/01621459.1969.10501049. Foundational probabilistic linkage, match/non-match decision regions, and error trade-offs. Difference: statistical linkage theory, not social profiles, embeddings, or GA policy optimization.

2. Peter Christen, “A Survey of Indexing Techniques for Scalable Record Linkage and Deduplication,” IEEE Transactions on Knowledge and Data Engineering 24(9), 2012, DOI 10.1109/TKDE.2011.127. Foundational scalable indexing/blocking survey. Difference: indexing survey, not the present staged classifier/policy evaluation.

3. Pradap Konda et al., “Magellan: Toward Building Entity Matching Management Systems,” Proceedings of the VLDB Endowment 9(13), 2016, 1197–1208, DOI 10.14778/2994509.2994535. End-to-end entity-matching management, feature generation, labeling, and evaluation context. Difference: system/tooling framework rather than cross-platform social identity linkage or a GA-selected three-way policy.

4. Charini Nanayakkara, Peter Christen, Thilina Ranbaduge, and Eilidh Garrett, “Evaluation measure for group-based record linkage,” International Journal of Population Data Science 4(1), published 2020, DOI 10.23889/ijpds.v4i1.1127. The official article page states that traditional pairwise precision/recall can be unsuitable for groups of linked records and presents a cluster-oriented evaluation. Difference: group-based evaluation, while this manuscript reports pair/workflow outcomes and does not evaluate clusters as its primary object.

B. Social identity linkage

5. Xiaoping Zhou, Xun Liang, Haiyan Zhang, and Yuefeng Ma, “Cross-Platform Identification of Anonymous Identical Users in Multiple Social Media Networks,” IEEE Transactions on Knowledge and Data Engineering 28(2), 411–424, 2016, DOI 10.1109/TKDE.2015.2485222. Direct cross-platform identity-linkage precedent. Difference: anonymous-user/network-oriented linkage; not the present LinkSocial-derived profile-pair pipeline, calibration, or GA policy.

6. Kai Shu, Suhang Wang, Jiliang Tang, Reza Zafarani, and Huan Liu, “User Identity Linkage across Online Social Networks,” ACM SIGKDD Explorations Newsletter 18(2), 5–17, 2017, DOI 10.1145/3068777.3068781. Review of user identity linkage methods and features. Difference: review and broader social-network framing, not the present controlled experiment.

C. Neural, semantic, and transformer matching

7. Yuliang Li, Jinfeng Li, Yoshihiko Suhara, AnHai Doan, and Wang-Chiew Tan, “Deep Entity Matching with Pre-Trained Language Models,” Proceedings of the VLDB Endowment 14(1), 50–63, 2020, DOI 10.14778/3421424.3421431. Ditto demonstrates transformer-based sequence-pair entity matching. Difference: fine-tuned transformer matcher; this manuscript uses a frozen MiniLM cosine feature added to handcrafted features and a gradient-boosting classifier.

8. Nils Barlaug and Jon Atle Gulla, “Neural Networks for Entity Matching: A Survey,” ACM Transactions on Knowledge Discovery from Data 15(3), 2021, DOI 10.1145/3442200. Useful taxonomy of neural methods and ER stages. Difference: survey, not a comparable social-profile experiment.

9. Saravanan Thirumuruganathan, Han Li, Nan Tang, Mourad Ouzzani, Yash Govind, Derek Paulsen, Glenn Fung, and AnHai Doan, “Deep learning for blocking in entity matching: a design space exploration,” Proceedings of the VLDB Endowment 14(11), 2459–2472, 2021, DOI 10.14778/3476249.3476294. Directly relevant to learned/dense candidate generation and retrieval recall. Difference: focuses on blocking, whereas this manuscript uses lexical/domain blocks and treats retrieval recall as a ceiling; it is a strong missing comparator for RQ3.

10. Abhishek Arora and Melissa Dell, “LinkTransformer: A Unified Package for Record Linkage with Transformer Language Models,” Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics: System Demonstrations, 2024, pp. 212–220, official ACL Anthology identifier 2024.acl-demos.21. Relevant to practical transformer-based record linkage and embedding retrieval. Difference: software package and transformer workflow, not GA policy optimization or the LinkSocial corpus.

D. Human-in-the-loop, abstention, and decision policy

11. Kun Qian, Lucian Popa, and Prithviraj Sen, “SystemER: A Human-in-the-loop System for Explainable Entity Resolution,” Proceedings of the VLDB Endowment 12(12), 1794–1797, 2019, DOI 10.14778/3352063.3352068. Directly supports the distinction between an offline REVIEW output and an actual human-review system: SystemER includes explainability, active learning, and human interaction. Difference: operational human-in-the-loop ER with explanations; this manuscript has no observed reviewer workload, accuracy, or agreement.

12. C. Chow, “On Optimum Recognition Error and Reject Tradeoff,” IEEE Transactions on Information Theory 16(1), 41–46, 1970, DOI 10.1109/TIT.1970.1054406. Foundational reject-option decision theory. Difference: general classification/reject theory, not ER or genetic optimization. Use to ground the accept/review/reject framing, not to imply that this exact policy is novel.

13. Mohammad Hossein Moslemi, Harini Balamurugan, and Mostafa Milani, “Evaluating Blocking Biases in Entity Matching,” 2024 IEEE International Conference on Big Data, 2024, DOI 10.1109/BigData62323.2024.10825531. Relevant recent work on blocking-induced bias and selection effects. Difference: analyzes bias from blocking; it does not evaluate this manuscript’s GA policy or three-way decisions. Verify final IEEE bibliographic formatting before addition.

E. Calibration and leakage-safe evaluation

14. Chuan Guo, Geoff Pleiss, Yu Sun, and Kilian Q. Weinberger, “On Calibration of Modern Neural Networks,” Proceedings of the 34th International Conference on Machine Learning, PMLR 70, 1321–1330, 2017, official PMLR identifier. Foundational calibration diagnostics and temperature scaling. Difference: neural-network calibration, not isotonic calibration of gradient-boosting ER probabilities; still useful for defining why probability quality matters.

15. Alexander Niculescu-Mizil and Rich Caruana, “Predicting Good Probabilities with Supervised Learning,” Proceedings of the 22nd International Conference on Machine Learning, 2005, pp. 625–632. This is a useful calibration lead, but its DOI was not cleared in this audit; verify it against ACM metadata before adding it.

The last item is deliberately flagged as unresolved and should not be added in its current form. The verified recommendations above are sufficient without it.

3. Missing foundational literature

The current bibliography lacks the standard lineage needed to position the work as record linkage rather than only profile matching:
- Fellegi–Sunter probabilistic record linkage (1969) for formal match/non-match/review decision regions.
- Christen’s scalable indexing/blocking survey (2012) and/or Magellan (2016) for ER pipeline terminology and candidate generation.
- Chow’s reject-option theory (1970) for the accept/review/reject framing.
- A social identity-linkage review and direct cross-platform method (Shu et al., 2017; Zhou et al., 2016).
- A human-in-the-loop ER system (SystemER) if REVIEW is discussed as an operational pathway.
- A neural entity-matching survey or transformer matcher (Barlaug & Gulla, 2021; Ditto, 2020) to contextualize the MiniLM feature.

4. Missing recent literature

Priority additions for a 2020–2026 literature review:
- Ditto (Li et al., 2020) for pretrained-language-model matching.
- DeepBlocker (Thirumuruganathan et al., 2021) for learned blocking and the retrieval/scoring separation.
- Barlaug and Gulla (2021) for the neural entity-matching taxonomy.
- Moslemi et al. (2024) for blocking bias, especially because this manuscript reports a blocking recall ceiling.
- LinkTransformer (Arora and Dell, 2024) for current practical transformer-based linkage tooling.
- Christen et al. (2026) is already present and is appropriately used for application-focused evaluation, but the related work should state that CRL is a different evaluation proposal, not a validation of the manuscript’s utility function.

A 2025/2026 arXiv survey or preprint may be mentioned only if the authors deliberately cover non-peer-reviewed current work. It should not replace the peer-reviewed references above, and no preprint should be used to make a priority/first claim.

5. Claims currently lacking citations

These are not necessarily false; they are claims that would benefit from literature support or clearer labeling as implementation-specific:

- “incorrect merges and missed links have different operational consequences” (main.tex line 37): cite reject-option/application-focused linkage literature, or phrase as the study’s declared engineering motivation.
- “A pair score does not itself specify an operating decision” (line 39): cite Fellegi–Sunter and Chow; three-way citation alone is not the complete decision-theoretic basis.
- “The decision layer assigns MATCH, REVIEW, or NO_MATCH” (abstract and line 39): cite three-way linkage and reject-option theory; clarify that the exact genome is this work’s design.
- MiniLM / sentence embeddings / semantic similarity (line 64): cite a primary Sentence-BERT or MiniLM source and a neural entity-matching source. The current text names all-MiniLM-L6-v2 without a model citation.
- Isotonic calibration (line 71): cite calibration methodology and report a calibration metric/plot if probability semantics are central to the GA policy.
- Jaro, Levenshtein, token similarity, and gradient boosting (line 64): citations are optional for routine implementation detail, but foundational metric/model citations would improve reproducibility and scholarly positioning.
- “Test labels are not accessed…” and entity-disjoint splitting (line 90): these are protocol claims backed by implementation/artifacts, but should be connected to literature on entity-disjoint evaluation and leakage in pairwise ER where possible.
- “REVIEW as an explicit operational outcome” (line 212): cite SystemER and reject-option/three-way decision literature, while retaining the explicit statement that no human study was performed.
- “utility coefficients express an engineering scenario” (lines 77–81, 102): this is a declared assumption, not an external claim. Cite application-focused evaluation only for the need to expose operating trade-offs; do not cite a paper as if it validated 2, 1, and 0.1.
- Claims about the absence of prior combinations (“no exact verified instance found”) should remain cautious. A systematic search protocol would be needed before any “first” claim.

6. Research-gap risk

Overall citation/research-gap risk: HIGH before related-work revision; MEDIUM after adding the priority references and tightening claims.

Main risks:
1. The current related work has only seven references, with no foundational probabilistic linkage, reject-option, human-in-the-loop, transformer matching, calibration, or leakage/evaluation source.
2. The paper’s apparent novelty is vulnerable because GA-based ER and three-way record linkage are already explicitly cited. The bounded empirical-composition framing is defensible; a “first” claim is not established.
3. The paper uses a semantic embedding feature without citing the embedding/matching literature, making RQ1 look under-positioned.
4. The paper separates blocking from scoring correctly, but omits recent learned-blocking work that a reviewer will expect.
5. “REVIEW” is an offline label, not human-in-the-loop evidence. SystemER makes this distinction especially salient.
6. Probability calibration is methodologically central to the GA input but currently uncited and apparently not reported with calibration diagnostics in the manuscript.
7. Pairwise results, workflow results, and entity-level identity resolution are not identical targets. Group-based linkage evaluation should be acknowledged if conclusions use “identity resolution” broadly.
8. The LinkSocial entry is usable for provenance but bibliographically incomplete and lacks a verified DOI. The source repository’s licensing/ethics limitation is correctly disclosed; do not add a redistribution claim.

7. Recommended Related Work structure

7.1 Terminology and probabilistic record linkage
Define entity resolution, record linkage, identity linkage, match/non-match, and review/reject regions. Use Fellegi–Sunter and Chow. State that the paper evaluates pair/workflow decisions, not a new linkage theory.

7.2 Cross-platform social identity linkage
Position LINKSOCIAL, Zhou et al., Shu et al., and Yao. Distinguish profile-attribute linkage from behavioral/network alignment and explain why the transformed LinkSocial derivative is the evaluated corpus.

7.3 Candidate generation and blocking
Use Papadakis, Li, Christen, DeepBlocker, and Moslemi. Explicitly separate candidate recall from classifier recall and state that blocking misses impose an end-to-end ceiling.

7.4 Pair representation and semantic matching
Use Ditto, Barlaug–Gulla, and optionally LinkTransformer. Contrast fine-tuned transformer matching with the manuscript’s single frozen MiniLM cosine feature plus GB classifier.

7.5 Three-way decisions, abstention, and human review
Use Ouyang, Chow, and SystemER. Clarify that the manuscript’s REVIEW count is an offline policy output; it is not reviewer workload, reviewer accuracy, or a human-in-the-loop experiment.

7.6 Calibration and leakage-safe evaluation
Add calibration literature and explicitly describe calibration-role separation, entity-disjoint splitting, and the distinction between pair-disjoint and entity-disjoint evaluation. Add an evaluation-methodology reference for group/entity-level assessment if the scope remains “identity resolution.”

7.7 Gap and contribution boundary
State that the contribution is an empirical evaluation of a staged composition on one transformed corpus: frozen calibrated pair scoring, validation-only policy optimization, three repeated entity-disjoint outer partitions, and retrieval-to-decision decomposition. Avoid “first,” “novel GA,” “general solution,” and “measured CRM benefit.”

8. References that should NOT be added

- Do not add the unresolved Niculescu-Mizil and Caruana DOI above until ACM metadata is checked; the current lead contains a deliberate unresolved marker.
- Do not add arXiv-only 2025/2026 papers as if peer-reviewed, especially for priority claims, when a peer-reviewed survey or proceedings paper covers the point.
- Do not add generic CRM, marketing, or social-media statistics unless a manuscript sentence makes a specific externally verifiable claim requiring them.
- Do not add a citation merely to justify the study’s numerical utility weights (2, 1, 0.1). Those are declared scenario assumptions.
- Do not add DeepBlocker or other learned-blocking work as a baseline unless it is actually implemented/evaluated; use it as related work and a limitation/future comparator.
- Do not add SystemER as evidence that this manuscript has human-in-the-loop validation. It supports the contrast, not the manuscript’s offline REVIEW claim.
- Do not add a paper based only on a search snippet, ResearchGate copy, or unverified bibliographic aggregation when a publisher/official proceedings record is unavailable.
- Do not claim that no prior paper combines GA, calibrated probabilities, semantic embeddings, and three-way decisions. The present search did not establish absence, and the manuscript should not make a first-combination claim.

9. Final citation-risk level

HIGH (revision recommended before submission).

The seven existing citations are mostly correct and relevant, and the manuscript already avoids the most dangerous novelty overclaims. However, the related-work coverage is too narrow for the paper’s methodological scope and current terminology. At minimum, add or discuss Fellegi–Sunter, Chow, one direct social-linkage precedent/review, one transformer matching paper, DeepBlocker, SystemER, and one calibration source. Correct the LinkSocial BibTeX completeness issue if the bibliography is later edited. Re-run DOI and venue checks after any bibliography change.

Audit evidence links

- ACM blocking survey: https://doi.org/10.1145/3377455
- Springer blocking survey: https://doi.org/10.1007/s11390-020-0350-4
- Three-way linkage: https://doi.org/10.1016/j.eswa.2018.12.038
- GA ER: https://doi.org/10.1007/s11704-015-5276-6
- Social profile features: https://doi.org/10.1145/3650400.3650622
- CRL evaluation: https://doi.org/10.1145/3786768
- LinkSocial repository: https://github.com/vishalshar/Dataset-LinkSocial
- Ditto: https://doi.org/10.14778/3421424.3421431
- DeepBlocker: https://doi.org/10.14778/3476249.3476294
- Neural matching survey: https://doi.org/10.1145/3442200
- SystemER: https://doi.org/10.14778/3352063.3352068
- Chow reject option: https://doi.org/10.1109/TIT.1970.1054406
- Fellegi–Sunter: https://doi.org/10.1080/01621459.1969.10501049
- Blocking bias: https://doi.org/10.1109/BigData62323.2024.10825531
- LinkTransformer: https://aclanthology.org/2024.acl-demos.21/
- Social identity linkage: https://doi.org/10.1109/TKDE.2015.2485222 and https://doi.org/10.1145/3068777.3068781
