ICSEC 2026 / IEEE Submission-Compliance Audit

Scope

Audited only the requested Overleaf submission artifacts:
- paper/overleaf/main.tex
- paper/overleaf/main.pdf
- paper/overleaf/references.bib
- paper/overleaf/figures/figure1.pdf

No manuscript file was modified. The audit uses the ICSEC requirements supplied in the audit brief, the ICSEC 2026 public conference page, the IEEEtran-generated source/log artifacts, and visual inspection of the available rendered pages.

| Requirement | PASS / WARNING / FAIL | Evidence | Required Fix |
|---|---|---|---|
| IEEE conference format | PASS | `main.tex:2` uses `\\documentclass[conference]{IEEEtran}`; the rendered PDF has IEEE conference-paper structure. | None. |
| IEEEtran conference class | PASS | `main.tex:2` explicitly selects `IEEEtran` with the `conference` option; the build log identifies IEEEtran V1.8b. | None. |
| English | PASS | Title, abstract, section headings, body text, captions, and bibliography are written in English. | None. |
| 4–6 pages including references, figures, and tables | PASS | `main.pdf` reports 4 pages via macOS metadata; `main.aux` ends with `\\@abspage@last{4}`; an isolated rebuild also produced a 4-page PDF. | None. Recheck after any parallel manuscript edits. |
| Two-column format | PASS | IEEEtran conference class is used and the rendered pages visibly use two columns. | None. |
| No modified margins | PASS | No `geometry`, margin, or page-dimension redefinition appears in `main.tex`; `\\textwidth` is used only as the figure inclusion width at `main.tex:109`. | None. |
| No unauthorized font-size changes | WARNING | Body text uses the IEEEtran default 10-point conference setting. However, tables explicitly use `\\small` (`main.tex:123,139,187`) and `\\footnotesize` (`main.tex:164`). The supplied brief prohibits unauthorized font-size changes, so these reductions require venue/template confirmation. The XeTeX log also reports unavailable Times font shapes substituted with Latin Modern shapes. | Confirm that reduced table sizes and the XeTeX/font setup are accepted by ICSEC/IEEE. If not explicitly permitted, remove local size changes and compile with the approved IEEE toolchain/font configuration. |
| No spacing manipulation | PASS | No `\\vspace`, `\\hspace`, `\\baselinestretch`, `\\linespread`, or manual length manipulation was found in `main.tex`. | None. |
| Figures readable | PASS | `figure1.pdf` is embedded as a vector figure at `main.tex:107–110`; visual inspection shows labels, arrows, and caption readable on the available rendered page. | None. Recheck at 100% in the final upload viewer. |
| Tables readable | PASS | Tables are structured with `booktabs`; visual inspection shows all four tables readable and contained within their intended column/spanning layout. Table III is compact and should receive a final 100% zoom check. | None for the inspected PDF. If the submission system rasterizes previews, verify Table III again. |
| Captions correct | PASS | The figure has a numbered caption below it (`main.tex:110`); tables have numbered IEEE-style captions above them (`main.tex:121,137,162,184`). Captions describe the displayed content and labels resolve in `main.aux`. | None. |
| Equations formatted correctly | PASS | The utility objective is set in a numbered `equation` environment (`main.tex:78–80`) and is referenced as (1) in the table caption and surrounding prose. | None. |
| References formatted consistently | WARNING | `\\bibliographystyle{IEEEtran}` is used (`main.tex:234`) and all seven bibliography entries are cited/resolved in `main.aux`; the generated `.bbl` uses IEEE numeric formatting. The first entry contains the visible typo `iEEE Xplore document 8588801` (`main.bbl:27`), and several DOI fields in `.bib` are not rendered by this IEEEtran output. | Correct `iEEE` to `IEEE` and perform a final bibliographic metadata check against the authoritative records. Confirm whether the venue expects DOI presentation; do not add URLs that could affect anonymity unless required. |
| No author names | PASS | `main.tex:15` contains only `Anonymous Submission`. Author names in `references.bib` are third-party cited authors, not submitting-author metadata. | None. |
| No affiliations | PASS | No affiliation block, institution, laboratory, employer, or author biography appears in `main.tex` or the rendered pages. | None. |
| No acknowledgements revealing identity | PASS | No acknowledgements section or identity-revealing thanks appears in the manuscript. | None. |
| No personal URLs | PASS | No URL, `\\url`, or `\\href` appears in `main.tex` or `references.bib`; no personal link is visible in the inspected PDF pages. | None. |
| No company/institution identifiers | PASS | The text mentions Twitter, Google+, Instagram, LinkSocial, and an Agentic CRM application context, but does not name a submitting institution, employer, company, or lab. | None. |
| No repository-owner clues | PASS | The manuscript cites the public LinkSocial corpus by scholarly citation but does not include its repository URL, owner handle, project repository, or author-controlled artifact link. | Preserve this condition in the final package. |
| No local paths | PASS | No local filesystem path appears in `main.tex`, `references.bib`, or the inspected PDF metadata. | None. |
| No machine usernames | PASS | No machine username or workspace username appears in the manuscript source or PDF metadata. | None. |
| No identifying PDF metadata | PASS | `main.pdf` metadata shows the manuscript title, subject `Double-anonymous ICSEC 2026 review manuscript`, creator `LaTeX with hyperref`, and no personal author value; macOS metadata reports author `LaTeX with hyperref`, not a person. | Preserve anonymous metadata in the final regenerated PDF and inspect metadata after the last compile. |
| No identifying comments | PASS | Source comments are workflow/evidence notes only; no author identity, institution, path, username, or private repository clue was found. | Remove internal editing comments before final camera-ready publication if the review upload package exposes source files; for the PDF-only review submission, no identifying comment was detected. |
| Title: application context is bounded | PASS | The title includes `Agentic CRM Platform`, but `main.tex:23–25,81,102,219,232` repeatedly limits the claim to an operational/application scenario and states that business benefit/economic cost was not measured. | Keep this qualification. Do not add claims of CRM deployment, lead-scoring performance, agent autonomy, or commercial impact. |
| CRM and Lead Scoring were not presented as experimentally evaluated | PASS | The manuscript evaluates profile linkage, pair scoring, retrieval coverage, three-way decisions, and an illustrative utility. It does not report a CRM experiment or lead-scoring metric; the abstract explicitly says there is no measured business benefit (`main.tex:25`). `Lead Scoring` does not appear in the audited `main.tex`. | None. Keep the title/application framing subordinate to the evaluated linkage task. |
| First-time-reader clarity: abstract | WARNING | The abstract clearly states the problem, data scope, staged pipeline, three-way outcomes, evaluation comparison, main result, retrieval ceiling, and limits (`main.tex:23–25`). It introduces GB-17/GB-18/GB-18-GA and the operational meaning of REVIEW without spelling out the model names in the abstract; a non-specialist reader may need the Introduction to decode them. | Consider one short expansion of the GB labels or a phrase identifying them as the two feature variants and GA policy variant, without adding unsupported claims or increasing page count materially. |
| First-time-reader clarity: introduction | PASS | `main.tex:37–43` explains the cross-platform linkage problem, asymmetric merge/review risks, candidate generation, the distinction between pair score and operating decision, the bounded novelty claim, research questions, and contributions. | None required. A light prose simplification of the dense final contribution sentence is optional. |
| ICSEC topic fit | PASS | The ICSEC 2026 public page lists Evolutionary Computing, Machine Learning and Deep Learning, Data Mining, and Intelligent Systems among invited areas. The paper directly evaluates a genetic policy over a linkage pipeline. | None. |
| Double-blind review expectation | PASS | The ICSEC 2026 public page states that full papers are reviewed through a double-blind process; the manuscript has an anonymous author line and no identified authors or affiliations. | Preserve anonymity in submission-system fields and supplementary/artifact material as well as in the PDF. |

Desk-rejection risk: MEDIUM

Primary risks

1. Font/toolchain compliance is not fully clean. The isolated build succeeds and produces four pages, but the log reports unavailable Times font shapes and fallback substitutions under XeTeX. The brief also prohibits unauthorized font-size changes, while the source applies `\\small` and `\\footnotesize` to tables. Confirm the exact ICSEC/IEEE PDF/font rules and regenerate with the accepted configuration.
2. The bibliography has a visible `iEEE` capitalization typo. This is unlikely to cause desk rejection alone but signals incomplete final quality control.
3. Table III and the dense confidence-interval paragraph have limited layout slack. The build reports several underfull boxes, including an underfull vertical box on the page containing the tables. The inspected PDF remains readable, but the final regenerated PDF should be checked at 100% after any edits.
4. The paper's data-provenance limitation is candidly disclosed: the source repository lacks a machine-readable reuse license and formal ethics documentation in the inspected materials. This is not an anonymity failure, but reviewers or chairs may require confirmation that the transformed data and any artifacts are lawful and ethically releasable.

No critical double-anonymous violation was found. The paper is within the requested page range, uses the IEEEtran conference class, is visibly two-column, and keeps Agentic CRM as application context rather than claiming experimental CRM or Lead Scoring evaluation.

Authoritative reference checked

- ICSEC 2026 About Us / topics and review process: https://cpe.eng.kps.ku.ac.th/ICSEC2026/about.php
- ICSEC 2026 home page: https://cpe.eng.kps.ku.ac.th/ICSEC2026/index.php
