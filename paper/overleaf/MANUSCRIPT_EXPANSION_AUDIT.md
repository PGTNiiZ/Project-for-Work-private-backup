# Manuscript Expansion Audit

## Scope and narrative

The manuscript now follows one evidence-bounded story: Agentic CRM motivates upstream identity consolidation; candidate generation and pair classification produce calibrated evidence; a three-way policy converts that evidence to MATCH, REVIEW, or NO_MATCH; a Genetic Algorithm selects the policy on validation entities without retraining; entity-disjoint outer tests expose the resulting trade-off and the candidate-retrieval ceiling.

The paper explicitly does not evaluate downstream CRM agents, lead scoring, analyst productivity, privacy protection, or business outcomes.

## Sections expanded or added

- Abstract: rewritten for a first-time reader; 10-part flow from application context through scope limitation.
- Introduction: seven focused paragraphs covering application context, conceptual profile example, conventional pipeline, operational gap, bounded research position, RQs, and evidence-linked contributions.
- Related Work: thematic synthesis covering cross-platform identity resolution, blocking, learned/semantic pair representation, three-way/reject decisions, human review, evolutionary ER, calibration, and evaluation.
- System Overview: new section placed before detailed methodology.
- Methodology: dataset/labels, exact and blocking tiers, grouped 17-feature representation, MiniLM feature, frozen Gradient Boosting settings, isotonic calibration, four-gene policy, Algorithm 1, GA settings, and illustrative utility.
- Experimental Design: repeated entity-disjoint outer protocol, cross-role dropping, test isolation, baseline isolation, metrics, and conditional bootstrap scope.
- Results: separate RQ1–RQ3 interpretation with explicit non-improvements and trade-offs.
- Failure Analysis and Discussion: aggregated lexical/missingness/platform-pair failures, explanation of policy-only recall gains, review-capacity implications, and blocking bottleneck.
- Limitations and Threats to Validity: internal, external, construct, and conclusion validity.
- Conclusion: problem, method, findings, trade-off, strongest limitation, and next steps.

## Figures

1. `figures/system_overview.pdf` — “Cross-Platform Identity Resolution Pipeline.” Shows profiles, candidate generation, pair representation, Gradient Boosting, isotonic calibration, GA policy, and three outcomes.
2. `figures/leakage_safe_evaluation.pdf` — “Entity-Disjoint Training, Calibration, Policy Selection, and Sealed Evaluation.” Shows four disjoint entity roles, no overlap, and test-label isolation.

Editable TikZ source is retained beside each PDF. The optional decision-region figure was omitted because Algorithm 1 already explains the four genes and another figure would be redundant.

## Tables and algorithm

- Table I retained and improved: dataset/platform counts plus candidate decomposition and retrieval ceiling.
- Table II retained: repeated outer-split mean ± SD for precision, recall, F1, FP, FN, REVIEW, and illustrative utility.
- Table III retained: per-split F1 and utility for all three methods.
- Platform-pair table removed; its non-redundant values are reported in failure-analysis prose.
- Algorithm 1 added: exact MATCH/REVIEW/NO_MATCH rule for the four-gene genome.
- No decorative result chart was added because the tables communicate both effect and trade-off more completely within the page budget.

## Evidence sources and numerical checks

Primary experiment family: `experiments/icsec_final/repeated_outer/`.

- Repeated metrics: checked against `all_results.csv` and `summary.csv`.
- Candidate counts: checked against `primary_reproduction/error_analysis/candidate_retrieval_decomposition.csv` and canonical candidate-generation code. The manuscript now distinguishes 36,807 local rows from 36,804 rows eligible after the non-null identifier filters, and decomposes 2,086,245 workflow pairs into 12,403 exact-tier and 2,073,842 model-scored pairs.
- Failure counts: checked against `failure_category_counts.csv` and `platform_pair_scored_metrics.csv`.
- Conditional intervals: checked against `statistical_analysis/paired_bootstrap_ci.csv`.
- Split roles and test isolation: checked against `split_manifest.json`, `run_icsec_repeated_outer.py`, `run_gb_transformer_experiments.py`, and anti-leakage tests.
- Feature definitions: checked against `exp_r2_bert_feature.py` and frozen training metadata.
- GA genome, constraints, mutation, population, generations, elites, and seed selection: checked against `exp_r1_ga_redecision.py`, the runner, and selected-policy artifacts.
- Historical R0–R6 and old notebook metrics were not mixed into the primary tables.

## Reference and anonymity checks

- 16 cited references; all entries have a verified publisher/DOI record or official IEEE document identifier.
- Author block: `Anonymous Submission` only.
- PDF author metadata: `Anonymous`.
- No acknowledgements, affiliations, author repository URLs, local filesystem paths, raw usernames, biographies, entity IDs, or pair IDs appear in manuscript text.
- Dataset release limitation is stated without exposing source records.

## Formatting and visual validation

- Class: `IEEEtran` conference mode.
- Final length: 5 pages including references, figures, tables, and algorithm.
- No margin, font-size, line-spacing, or column-spacing overrides.
- Both figures are vector PDFs.
- Every page was rasterized and visually inspected after the final compile.
- Tables and figures are readable at rendered page scale; no clipping or overlap was observed.
- Compilation has no undefined citations or overfull boxes. Remaining underfull-box warnings are cosmetic line-justification warnings, not overflow.

## Remaining evidence/release issues

- LinkSocial's public repository has no machine-readable license or formal ethics documentation in inspected materials.
- The repeated-outer package reproduces internally but lacks the environment snapshot, source/input hashes, and artifact-hash manifest available for the frozen primary run.
- The frozen cost-sensitivity CSV contains a stale note naming historical 5/1/0.02 selection weights; the policies were selected under 2/1/0.1. The manuscript uses only the arithmetically valid frozen-policy sensitivity conclusion and does not repeat the stale provenance note.
- Only one transformed historical corpus and three outer partitions are available.
- Utility coefficients are illustrative, not measured economic costs.
- REVIEW has not been evaluated with human reviewers.
- Candidate generation retrieves 88.6742% of labeled positives and remains the end-to-end ceiling.
- ICSEC 2026's final author kit/template and double-anonymous instructions should be rechecked when the conference publishes or updates them; the current package uses standard IEEE conference formatting and the supplied project requirements.
