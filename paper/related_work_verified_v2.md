# Related Work: Verified Comparative Map v2

## 1. Blocking and candidate generation

**Papadakis, George; Skoutas, Dimitrios; Thanos, Emmanouil; Palpanas, Themis.** “Blocking and Filtering Techniques for Entity Resolution: A Survey.” *ACM Computing Surveys*, 53(2), 2021. DOI: `10.1145/3377455`.

- Problem: scalable ER despite quadratic pair comparisons.
- Method: survey of blocking/filtering frameworks.
- Dataset/evaluation: survey; no single comparable dataset/protocol.
- Relevant finding: blocking restricts comparisons to likely matches, making candidate coverage a separate system concern.
- Limitation/relationship: does not optimize downstream MATCH/REVIEW/NO_MATCH decisions. Supports RQ3 framing only.

**Li, Bo-Han; Liu, Yu; Zhang, An-Man; Wang, Wen-Huan; Wan, Shuo.** “A Survey on Blocking Technology of Entity Resolution.” *Journal of Computer Science and Technology*, 35, 769–793, 2020. DOI: `10.1007/s11390-020-0350-4`.

- Problem/method: blocking as approximate computational reduction for ER.
- Relevant finding: blocking can omit true pairs; downstream scoring cannot recover omitted candidates.
- Limitation/relationship: supports measuring retrieval recall and blocking misses, not a new blocking contribution.

## 2. Social-profile identity linkage

**Yao, Xiaolin.** “User Identity Linkage Across Multiple Social Network Based on Profile Features.” *Proceedings of the 2023 7th International Conference on Electronic Information Technology and Computer Engineering*, 2023, pp. 1317–1323. DOI: `10.1145/3650400.3650622`.

- Problem: cross-platform social-profile identity linkage from basic profile attributes.
- Method: string, short-text, and semi-structured profile features with integrated machine-learning models.
- Dataset/evaluation: publisher page describes profile-feature identity-linkage evaluation; details are not directly comparable to the frozen LinkSocial protocol.
- Limitation/relationship: no verified GA-selected three-way policy on fixed calibrated probabilities. It is the closest direct domain comparator.

**Sharma, Vishal; Dyreson, Curtis E.** “LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms.” *2018 IEEE International Conference on Big Knowledge (ICBK)*, 2018, IEEE Xplore document `8588801`.

- Stable identifier: IEEE document 8588801; official dataset repository: `https://github.com/vishalshar/Dataset-LinkSocial`.
- Problem/method: original LinkSocial social-profile linkage corpus/publication.
- Dataset: public repository documents Google+, Instagram, and Twitter profiles and profile fields.
- Relationship: dataset provenance/source, not a fair performance baseline.
- Citation metadata beyond the official repository and IEEE record should be re-exported from IEEE Xplore before final bibliography generation.

## 3. Three-way decisions and evolutionary ER

**Ouyang, Tinghui; Pedrycz, Witold; Pizzi, Nick J.** “Record Linkage Based on a Three-Way Decision with the Use of Granular Descriptors.” *Expert Systems with Applications*, 122, 16–26, 2019. DOI: `10.1016/j.eswa.2018.12.038`.

- Problem: record linkage with an explicit three-way decision.
- Method: granular descriptors and three-way decision rules.
- Evaluation: published linkage experiment; detailed data/metrics are not comparable to this project from retrieved metadata.
- Main finding/relation: three-way MATCH/REVIEW/NO_MATCH-style linkage is established. This paper cannot claim that concept as new.

**Sun, Chenchen; Shen, Derong; Kou, Yue; Nie, Tiezheng; Yu, Ge.** “A Genetic Algorithm Based Entity Resolution Approach with Active Learning.” *Frontiers of Computer Science*, 11(1), 147–159, 2017. DOI: `10.1007/s11704-015-5276-6`.

- Problem: entity resolution with an evolutionary method and active learning.
- Method: GA-based ER approach.
- Evaluation: published ER study; exact protocol not directly comparable to frozen LinkSocial policy evaluation.
- Main finding/relation: evolutionary optimization in ER is established. This paper cannot claim GA-for-ER novelty.

## 4. Operational linkage evaluation

**Christen, Peter; Ziyad, Sumayya; Nanayakkara, Charini.** “Consistently Evaluating Record Linkage Classifiers.” *Journal of Data and Information Quality*, 18(1), 2026. DOI: `10.1145/3786768`.

- Problem: conventional precision/recall/F1 can rank linkage classifiers inconsistently for application goals.
- Method: Consistent Record Linkage measure using acceptable application error rates and threshold robustness.
- Evaluation: synthetic and real-world data according to publisher abstract.
- Main finding/relation: supports transparent operational trade-off reporting. It does not supply a GA three-way policy.

## Direct answers to the novelty questions

1. Three-way entity resolution already established? **Yes.** Ouyang et al. directly establishes three-way record linkage.
2. GA-based entity resolution already established? **Yes.** Sun et al. directly establishes GA-based ER.
3. Has GA previously optimized MATCH/REVIEW/NO_MATCH policies? **No exact verified instance found.** Existing sources establish GA ER and three-way ER separately. Absence is not proven.
4. Has GA previously operated on calibrated classifier probabilities? **No exact verified instance found.** Do not claim first use.
5. Has semantic profile embedding been combined with a cost-sensitive three-way layer? **No directly comparable verified source found.** Do not claim first combination.
6. Has comparable work used strict entity-disjoint train/calibration/policy-selection/test partitions? **No directly comparable verified source found in accessible sources.** Do not claim uniqueness.
7. Has prior work explicitly decomposed blocking misses from scoring/decision errors? **Blocking literature recognizes candidate omission; no directly comparable verified decomposition found.** Treat this as transparent evaluation practice, not novelty.

## Final literature-grounded gap

The paper investigates, rather than claims to invent, an operational composition: calibrated semantic-enhanced social-profile pair scoring plus validation-only evolutionary selection of a three-way decision policy, evaluated through repeated entity-disjoint outer partitions while exposing the candidate-generation recall ceiling. Its contribution is empirical design and evidence discipline on one corpus.
