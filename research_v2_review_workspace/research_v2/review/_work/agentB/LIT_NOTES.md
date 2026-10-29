# Agent B — Literature verification notes (V2 review)

Scope: P01–P35 (v1) were re-verified, plus 14 new papers (P36–P49; the cap is 20). Primary sources were the Crossref `/works/<doi>` and query APIs, OpenAlex, publisher and proceedings pages (OpenProceedings, IJCAI, JMLR, NeurIPS, AAAI OJS, Tech Science Press), arXiv, and the GitHub API. dblp and the Semantic Scholar API returned HTTP 429 or a bot wall for most calls, so dblp is not cited as evidence anywhere. Per-row URLs are in `paper_verification.csv`. Paths that start with `agentB/raw/` point to files fetched in the earlier run. I re-read those files as data.

CSV note: the header uses the bare column names. The value hints in the spec, such as `peer_reviewed(Y/N/preprint)`, were dropped because one of them contains a comma. The column order is exactly as specified. The file parses with Python `csv` (49 rows).

## 1. K4 open items

| Item | Status | Resolution / evidence |
|---|---|---|
| P01 DOI | RESOLVED | 10.1109/ACCESS.2024.3500374 confirmed. IEEE Access 12:171241–171268 (2024). https://api.crossref.org/works/10.1109/ACCESS.2024.3500374 |
| P10 volume/year | RESOLVED | Information Systems vol. 120, art. 102307, Feb 2024. https://api.crossref.org/works/10.1016/j.is.2023.102307 |
| P19 DOI | RESOLVED | 10.1007/s10994-021-05964-1. Mach. Learn. 110(3):451–456. |
| P30 DOI | RESOLVED | 10.1007/978-3-319-57454-7_49. PAKDD 2017, LNCS, pp. 628–640. |
| P31 DOI | RESOLVED | 10.1145/3340531.3411931. CIKM 2020, pp. 1485–1494. |
| P28 DOI/volume | RESOLVED (metadata) / PARTIAL (content) | 10.1016/j.eswa.2025.129026. ESWA vol. 296, art. 129026, Jan 2026. The paper has **7 authors** (Peng, Chen, Miao, Zhang, Qin, Du, Lu), not the 4 listed in v1. No abstract was retrievable (ScienceDirect returned 403; Crossref and OpenAlex have none), so the "unsupervised" and "K-Means" details remain UNCONFIRMED. |
| P05 textual/dirty claim | RESOLVED – supported | Full text (`agentB/raw/P05_pdf.txt`): "in the absence of labor-intensive data extraction/cleaning DL is highly promising, outperforming current automatic EM solutions for textual and dirty data". DL significantly beats Magellan on dirty data. On structured data it is competitive but not better. Caveat: "dirty" here means values synthetically moved into other attributes. |
| P08 model list | RESOLVED | Sec. 5.1.2 (arXiv 2508.08076 v2): **DeepMatcher, DITTO, EMTransformer, HierGAT**. The v1 list is correct. The datasets are Abt-Buy, Company, Fodor-Zagat, WDC, Walmart-Amz and iTunes-Amz. |
| 16 V-LIT-KNOWN rows | RESOLVED (all → V-LIT-WEB) | P03, P05, P15, P16, P17, P20, P21, P22, P23, P25, P26, P27, P32 and P33 were confirmed by Crossref DOI records. P06 is confirmed by a DataCite DOI plus the OpenProceedings PDF. P24 has no DOI; the author PDF confirms it and OpenAlex gives pp. 973–978. |
| P34 | RESOLVED – **record exists** | See §4. |

## 2. Metadata corrections vs v1

- **P04** year: the PVLDB 14(1) issue is dated **Sept 2020** (Crossref). v1 changed the year to 2021, but 2021 is the year of the VLDB conference. Cite it as PVLDB 14(1):50–60, 2020.
- **P03** add pp. 41–49 · **P05** add pp. 19–34 · **P06** pp. 463–473. The P06 DOI is a DataCite DOI, which is why Crossref returned 404.
- **P09** pp. 529–541 confirmed. Its DOI is also DataCite.
- **P12** published online Mar 2020; Crossref's print date is 2021. The 53(2) citation is correct; pp. 1–42.
- **P15** pp. 3980–3990 · **P16** pp. 1183–1210 · **P20** 6(4):1–21 · **P22** 10(7):1895–1923 · **P25** 16(1):41–46 · **P26** pp. 625–632 · **P27** pp. 213–220 · **P32** 38(6):946–969 · **P33** 64(12):86–92, 7 authors.
- **P18** online 2017, issue 2018. The v1 year is fine.
- **P24** IJCAI-01 pp. 973–978 (from OpenAlex, a secondary source). There is no DOI.
- **P28** gets a DOI, volume and article number, and its author list is completed.
- **P34** gets a real author list, CMC **86(2):1–23, 2026**, and status V-LIT-WEB.
- "Thai / transliteration" strata in v1 (G-4, E7-3): no paper here supports a Thai-language assumption. Treat it as a data question for D0-2, not as something the literature establishes.

## 3. Misattributions and over-reach

1. **P08**: v1 states "test-time heterogeneity hurts more than training noise" as a general finding. The paper says this for **granularity/hierarchical heterogeneity** only ("generalizing to distorted test data is more challenging than learning from heterogeneous training data"). Label noise in training also degrades AUC. Mark it PARTIAL. The paper also includes MCAR/MAR/MNAR missing-value injection, which v1 did not use and which is relevant to H1/E5-6.
2. **P07**: the abstract supports open entities, imbalance, multimodality and the overestimation of progress. But "entity-disjoint split (G3)" and "candidate vs end-to-end (E7-1)" are **v1's own inferences**, not prescriptions in the paper.
3. **P12**: PC/PQ/RR definitions, token blocking and block purging were not re-checked in the full text this round, only the abstract (PARTIAL).
4. **P03**: the abstract confirms behavioural-redundancy features, but "username-only" could not be checked against the full text (ACM returned 403) (PARTIAL).
5. **P02**: the exact wording "noisy/incomplete/unstructured" was not checked in the full text (PARTIAL).
6. **P14**: the FAISS detail is not in the abstract and was not checked.
7. **P28**: "three-way decision integrated with K-Means" is UNCONFIRMED; the title only says "clustering".
8. No v1 attribution was found to be outright false (no NO verdicts).

## 4. P34 decision

The record is **found and verified**, so P34 should no longer be EXCLUDED.
- Min S., Luo Y., Liu K., Gong Q., Chen Y. "From Identification to Obfuscation: A Survey of Cross-Network Mapping and Anti-Mapping Methods". *Computers, Materials & Continua* 86(2):1–23, 2026, DOI 10.32604/cmc.2025.073175. Received 12 Sep 2025, accepted 29 Oct 2025, issue published 9 Dec 2025.
- Evidence: the Crossref DOI lookup and title search both return the record; publisher page https://www.techscience.com/cmc/v86n2/64808/html; Semantic Scholar (corpus 283537673, DBLP key journals/cmc/MinLLGC26).
- Recommended use: survey context on UIL mapping vs **anti-mapping/obfuscation** (privacy, G1/T8) only. It is a review in a lower-tier open-access venue, so it should not be cited for empirical claims. v1's earlier "not found" was most likely a search failure.

## 5. P36 / P37: papers cited by the historical code

- The existing `_work/P36_crossref.json` / `P36.pdf` is **neither** of the two historical papers. It is Isele & Bizer 2012, GenLink (PVLDB 5(11)), which I kept as **P39** for the H4 gap.
- **P36 – Arford, Lin, Li, Hu, Chen (2025)**, "Assessing the De-Anonymization Risk of Social Media Users: A BERT-Based Entity Resolution Approach", IEEE ISI 2025, pp. 15–20, DOI 10.1109/ISI65680.2025.11201172. Existence and metadata are **VERIFIED** (Crossref, OpenAlex, IEEE ISI 2025 table of contents). Content is **UNCONFIRMED**: there is no open-access copy and the IEEE abstract could not be retrieved. A secondary search summary says it applies BERT-ER to link anonymized and public accounts. OpenAlex shows it **cites LinkSocial (P38)**. Whether it uses the LinkSocial data, and what results it reports, is UNCONFIRMED. Do not cite numbers from it.
- **P37 – Li, Miao, Wang, Sun, Wang (2021)**, "Improving the Efficiency and Effectiveness for BERT-based Entity Resolution", AAAI-21 35(15):13226–13233, DOI 10.1609/aaai.v35i15.17562. **VERIFIED from the full text.** The paper names its model "BERT-ER": siamese BERT tuple encoders, delayed "enhanced alignment" interaction, and a **hash-code blocking module** (binary hash codes into hash buckets) trained jointly with matching (multi-task). The datasets are Amazon-Google, BeerAdvo-RateBeer, iTunes-Amazon and DBLP-ACM, plus large Walmart-Amazon(B) and Amazon-Google(B) sets. The historical description ("BERT-ER with hash blocking") is accurate.

## 6. LinkSocial provenance (G0)

1. **Paper (P38):** Vishal Sharma & Curtis Dyreson, "LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms", 2018 IEEE International Conference on Big Knowledge (ICBK), Singapore, 17–18 Nov 2018. DOI **10.1109/ICBK.2018.00042**, IEEE document 8588801, pp. 260–267. The pages come from the authors' README and the P01 reference list, because Crossref has none. The README says "ICBK 2019" in one place, but the venue is 2018. **Abstract (OpenAlex):** features from profiles go into a cost function, Stochastic Gradient Descent learns the feature weights, clustering selects candidate pairs, and the system performs pair-wise and multi-platform linking. It reports **92% accuracy pair-wise and 74% multi-platform** across Google+, Twitter and Instagram.
2. **Repository:** https://github.com/vishalshar/Dataset-LinkSocial ("Dataset used in our paper LINKSOCIAL…").
   - Created 2019-02-27, last push 2022-01-20, single branch `master`.
   - Top level holds `1.profile.data/`, `2.profile.data/`, `3.profile.data/` and a README.
   - **Commit `fe67dd1102d9…` does NOT exist** in this repository or in any of its 3 forks (GitHub API: "No commit found for SHA"). GitHub commit search also returns 0 results. Upstream commits run from `9f9d741` (2019-02-27) to `fca67be` (2022-01-20).
   - So the project's gitlink points to a commit that is not on GitHub. It is probably a local or re-initialised copy, which means the provenance chain is **unverifiable as recorded** (G0 finding).
   - I did not download the data.
3. **Size and fields (README):**
   - Profiles: Instagram 10,958 · Twitter 13,961 · Google+ 11,892 (total 36,811).
   - Users: Instagram–Google+ 614 · Twitter–Instagram 2,451 · Google+–Twitter 2,974 · all three 7,729.
   - These counts match the project's 36,807 profiles (Twitter 13,960 / Google+ 11,890 / Instagram 10,957) to within 1–2 per platform. That is strong circumstantial evidence the project data is LinkSocial with a few rows dropped.
   - Fields: user name, bio, full name, external URL, and user/full-name bi-grams; profile picture URL for Instagram and Twitter only.
   - P01 lists the same set as "ITG1 (2018), 7,729" users.
4. **Ground-truth construction:** **UNCONFIRMED.** The full paper is paywalled (IEEE; the ResearchGate copy returned 403). The abstract and README do not say how the cross-platform links were obtained, for example self-declared links, About.me, or Google+ "other profiles". Related evidence: Goga et al. (P46) built Google+ ground truth from users' **self-declared links** and warn that such users "might not represent users in general".
5. **License / terms:** **no license file** (GitHub API `license: null`). Legally that defaults to all rights reserved. The README only asks users to cite the paper. No ethics or terms-of-use statement was found. Treat this as a G0/G1 blocker: written permission or a documented legal basis is needed.
6. **Label-proxy risk:** **cannot be ruled out; treat it as HIGH until audited.** If the links came from self-declared cross-links or URLs, then `external URL` and verbatim username equality may encode the label itself, which is the leakage pattern of P20. Required checks (D0-1/D0-4):
   - the share of positive pairs whose external URL points to the other platform or contains the other handle;
   - the share with identical usernames;
   - results with URL features ablated (E5-4).

## 7. New papers (P36–P49) and the gap each fills

| ID | Paper | Gap |
|---|---|---|
| P36 | Arford et al. 2025 ISI | Verifies a historical citation; de-anonymisation framing (content UNCONFIRMED) |
| P37 | Li et al. 2021 AAAI (BERT-ER) | Verifies a historical citation; joint hashing-blocking + PLM matching (H3/H5) |
| P38 | Sharma & Dyreson 2018 ICBK (LinkSocial) | **G0 ground-truth provenance** |
| P39 | Isele & Bizer 2012 PVLDB (GenLink) | H4: GP/evolutionary learning of linkage rules incl. thresholds |
| P40 | de Carvalho et al. 2012 TKDE | H4: GP deduplication functions adapted to a fixed boundary |
| P41 | Bergstra & Bengio 2012 JMLR | H4: random-search baseline, fair HPO comparison (E6-4) |
| P42 | Bergstra et al. 2011 NIPS | H4: TPE / sequential model-based baseline (E6-4) |
| P43 | Geifman & El-Yaniv 2017 NIPS | H4: selective classification, risk–coverage for the review band (E6-6) |
| P44 | Gokhale et al. 2014 SIGMOD (Corleone) | Human-in-the-loop EM workflow (E6-6, D0-1) |
| P45 | Paulsen et al. 2023 PVLDB (Sparkly) | H5: strong sparse top-k TF/IDF baseline |
| P46 | Goga et al. 2015 KDD | H1 attribute availability/missingness; realistic-scale UIL evaluation; label-provenance bias |
| P47 | Papadakis et al. 2024 ICDE | Benchmark difficulty, linear vs non-linear gap (H2), realistic evaluation |
| P48 | Köpcke et al. 2010 PVLDB | H2: learned vs non-learned ER on real tasks |
| P49 | Field & Welsh 2007 JRSS-B | Cluster bootstrap for entity-dependent pairs |

Considered and not added:
- GAEMTBD (Mishra et al., Appl. Intell. 47(1):197–230, 2017, DOI 10.1007/s10489-016-0874-z): it exists, but its abstract was not accessible, and P39/P40 already cover the gap.
- A dense+sparse hybrid-blocking paper beyond P13: P13 already reports the DL+non-DL combination.
- Further PPRL attacks: already covered by P30, P31 and P35.

**Remaining H4 gap:** I found no paper that compares a GA against random search or TPE **at an equal budget** for record-linkage thresholds. A G-3 contribution claim remains plausible but still needs a systematic search (Scopus/IEEE) before thesis use.

## 8. Literature findings by method family (L1: what the literature establishes)

- **Lexical/string similarity matching:**
  - Per-attribute similarity plus a classifier or weighting is the standard pipeline [P17, P16].
  - Profile attributes (screen name, real name, location, photo) are informative, but availability and consistency vary widely by platform [P46].
  - Username behaviour carries signal [P03].
  - High accuracy on small samples does not survive realistic scale: 19% recall at 95% precision [P46].
- **Learned classifiers vs rules:**
  - Learning-based ER generally beats non-learning configurations on real tasks, with large differences between tools [P48].
  - Many standard benchmarks are nearly linearly separable, so a linear-vs-non-linear gap must be measured before claiming DL gains [P47].
  - GP/GA can learn rules that rival hand-written ones [P39, P40].
- **PLM/transformer EM:**
  - Fine-tuned transformers outperform earlier DL matchers, by up to 29% F1 [P04] and by an average +27.5% [P06].
  - DL gains concentrate on textual and dirty data; structured data shows little gain [P05].
  - Siamese and hash blocking can recover efficiency [P37].
  - LLMs approach PLMs with few labels but are prompt-sensitive [P09].
  - Robustness drops under test-time granularity shift and missing values [P08].
  - All of this evidence comes from product and bibliographic benchmarks, not social profiles.
- **Frozen sentence embeddings:** Bi-encoders give cosine-comparable embeddings [P15]. Their quality and vectorisation cost vary greatly by model and dataset, and no model dominates [P14].
- **Blocking (sparse/dense/hybrid, meta-blocking):**
  - Blocking must be evaluated on recall and candidate count together [P12].
  - Label-free DL blockers beat non-DL on textual and dirty data, are only comparable on structured data, and do even better when combined with non-DL [P13].
  - Top-k TF/IDF is a very strong baseline [P45].
  - Supervised meta-blocking prunes candidates with a classifier [P10, P11].
- **GA/evolutionary decision optimisation:**
  - Evidence exists that GP can learn linkage rules and thresholds [P39, P40].
  - Random search [P41] and TPE [P42] are the accepted equal-budget baselines.
  - No GA-vs-RS/TPE equal-budget study for linkage thresholds was found (open gap).
- **Cost-sensitive thresholds and calibration:**
  - The optimal threshold follows from the cost matrix plus calibrated probabilities, so it needs no search [P24].
  - Calibration quality depends on the model, and Platt and isotonic suit different distortions [P26].
  - F-measure weights depend on the method, and accuracy is meaningless under imbalance [P18, P19].
  - PR curves are preferred under imbalance [P23].
- **Reject option / three-way decisions:** the match / possible / non-match theory comes from P16. The error–reject trade-off comes from P25. Risk-controlled selective prediction comes from P43, and crowd/human review workflows from P44. A UIL-specific three-way decision study exists [P28], but its content is UNCONFIRMED.
- **PPRL and attacks:** Bloom-filter q-gram PPRL [P29, P32] is vulnerable to frequency, pattern and graph-matching attacks [P30, P31, P35]. Privacy therefore cannot be claimed without an attack evaluation. UIL anti-mapping methods are surveyed in P34, and the de-anonymisation risk of BERT-ER linkage in P36 (content unconfirmed).
- **Realistic evaluation and leakage:**
  - Benchmark assumptions such as closed entities and balanced labels overstate EM progress [P07, P47].
  - Small-sample UIL evaluation overstates reliability [P46].
  - Leakage needs learn–predict separation [P20].
  - Tuning and estimating on the same CV is optimistically biased [P21].
  - Paired tests assume independent instances [P22]. A cluster bootstrap is consistent for clustered data [P49].
  - Incomplete labels call for PU-style thinking [P27].
  - Datasets need datasheets [P33].
  - Self-declared ground truth is unrepresentative [P46], which applies to the unverified LinkSocial labels [P38].
- **Multimodal / profile images in UIL:** open-world multimodal records make EM harder [P07]. Profile photos are an ACID-analysed attribute with limited availability, for example 69% on Twitter in DATASET FF [P46]. LinkSocial provides picture URLs only for Instagram and Twitter [P38]. P01 and P34 survey multimodal UIL. No controlled photo-ablation evidence on comparable data was found.
