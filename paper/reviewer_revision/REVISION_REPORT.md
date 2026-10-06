# Reviewer revision report

## Outcome

Technical revision implemented and independently checked. Original scientific runs, cost function, B0-B3 definitions, models, calibration, data splits and historical manuscripts were preserved. Submission approval remains blocked on the exact M5 comment and author-confirmed AI disclosure/conference instructions. This is a defensible revision package, not a claim of reviewer acceptance.

Revised source: paper/reviewer_revision/main.tex
Revised PDF: paper/reviewer_revision/main.pdf
Frozen numerical authority: experiments/icsec_final/authoritative_run_v2r1/
Additive analysis: experiments/icsec_final/reviewer_revision/

## 1. Reviewer issue matrix

Paths below are relative to the repository. `main.tex` means paper/reviewer_revision/main.tex; `analysis` means experiments/icsec_final/reviewer_revision/.

| Issue | Status | Evidence | Files Changed | Result |
|---|---|---|---|---|
| M1 decision recall/REVIEW | FIXED | Original _metrics; independent workflow recomputation; analysis/metrics_per_seed.csv | New reviewer_revision.py, run_reviewer_revision.py, tests/test_reviewer_revision.py; main.tex; controlled_results figure; supplementary table | Preserved and explicitly labeled conditional metrics; added positive REVIEW, automatic recall/F1, review rate/coverage, component counts; narrowed headline |
| M2 closed-form Chow | FIXED | Fixed cost matrix; stored GB-18 posteriors; three Chow_workflow.parquet artifacts; independent argmin checks | New baseline/evaluator scripts and tests; main.tex; main table/figure | Untuned risk-minimizing rule compared fairly with B0/B1/Sobol/GA; competitive result retained |
| M3 U direction | FIXED | GB17_B0 and B0 summaries plus row-level recomputation: loss rises by 12.233333 | main.tex retains correct direction; NUMERIC_CLAIM_AUDIT.json and EVIDENCE_MAP.md document check | Current source was already correct; no unsupported reversal or table correction made |
| M4 anytime/vectors | FIXED | Six validation-only replay traces, 48 actual checkpoints; all original final vectors exactly reproduced | run_reviewer_revision.py; generate_figures.py; main.tex; optimizer_anytime PDF/SVG; vector table/CSV | Observed incumbent loss from 100 through 12,000 calls; representative vectors shown; full precision retained; no universal GA superiority claim |
| M5 identity edge case/minor issue | AUTHOR CONFIRMATION REQUIRED | Exact reviewer wording absent; corrected_name_sim and pairwise evaluator inspected | main.tex; boundary/missingness regression checks | Clarified missing-name behavior, non-transitive pairwise scope and exact-match heuristic limitation; cannot certify the unspecified comment is resolved |
| M6 full policy definition | FIXED | Actual BOUNDS, repair, decide_four_parameter and name normalization | main.tex; documented-boundary tests; EVIDENCE_MAP.md | Complete piecewise rule, four ranges, ordering, ties/empty REVIEW band and B1 non-nesting; no unexplained policy gate terminology |
| M7 unrelated Agentic CRM | FIXED | No downstream evidence; source/PDF scans | main.tex; MANUSCRIPT_DIFF.patch; CHANGELOG.json | Removed application claims/disclaimers from Abstract, Introduction, Limitations and Conclusion without speculative replacement |

## 2. Experiment change summary

### Reanalyzed, not retrained

- All five original workflow methods (GB17_B0, B0, B1, B2, B3), each on the same three frozen partitions.
- Recomputed TP/FP/FN, total REVIEW, positive REVIEW, decision precision/recall/F1, automatic end-to-end recall/F1, candidate review rate/coverage, and U from pair-key-unique persisted rows.
- Evaluated one new closed-form policy on the same frozen GB-18 calibrated posteriors. Common exact-tier MATCH decisions and blocking-missed positives stayed unchanged.
- Independently recomputed eligible profile/positive/universe/candidate accounting from current eligible inputs and persisted candidate pair keys. No candidate-generation or feature regeneration was required.

### Rerun computation

- Replayed B2 Sobol and B3 GA only on POLICY_VALIDATION for outer seeds 101, 202, 303, using saved GB-18 models/calibrators and frozen feature caches.
- Exactly 12,000 realized objective calls per optimizer/partition. Stored every objective and incumbent vector, and checkpoints at 100/250/500/1000/2000/4000/8000/12000 actual calls.
- Final selected vectors exactly equal all six original policy vectors.
- The additive runner was executed twice: an initial execution and a deterministic repeat after correcting manifest closure to exclude still-open runtime logs. Both execution logs record identical scientific values/vectors; these are NOT extra independent experimental partitions and no better output was selected.
- Original Sobol sequence is unscrambled and deterministic; the seed argument does not alter its sequence. GA uses outer seed 101/202/303. Original B1 is unchanged and was not retuned.

### Unchanged locked setup

- Outer seeds 101/202/303; complete entities assigned to TRAIN/CALIBRATION/POLICY_VALIDATION/SEALED_TEST; cross-role pairs discarded.
- Split manifests: authoritative_run_v2/splits/outer_101.json, outer_202.json, outer_303.json, consumed unchanged by V2R1.
- Profile counts by role: seed 101 = 17864/3902/4001/11037; 202 = 18271/3778/3793/10962; 303 = 17829/3877/3912/11186.
- Gradient Boosting: 300 estimators, learning rate .05, max depth 6, model random state 42. TRAIN negative sampling ratio 3:1, sampling seed = outer seed.
- Isotonic calibration on CALIBRATION only; GB-17 handcrafted schema and GB-18 additional frozen MiniLM cosine cache unchanged.
- U = 2 FP + FN + .1 REVIEW. No coefficients or action definitions were changed.
- B0 = .98/.95 fixed thresholds; B1 original simple Sobol domain; B2/B3 original four-parameter bounds and clipping; GA population 60, 200 evaluated populations, Gaussian mutation, duplicate evaluations counted. No stopping rule or policy was selected from test performance.
- No scientific model fitting, recalibration, embedding generation, fresh sealed test trial, human review experiment, external validation, or clustering experiment was performed in this revision.

### Outputs

analysis/PROTOCOL.md, metrics_per_seed.csv, aggregate.json, selected_vectors.csv, anytime_checkpoints.csv, provenance.json, execution.log, execution_final.log, tests_final.log, outer_*/Chow_workflow.parquet, outer_*/validation_replay_input.parquet, six B2/B3_anytime.csv traces, and replay_verification.json. These are local audit artifacts, not an authorized release of underlying data.

## 3. Headline result check

Original B0 -> B1 decision F1 is reproduced: 0.850964808 -> 0.891037413. Under the end-to-end automatic metric, the gain is smaller: 0.841951957 -> 0.866721761. The headline remains supported as a mean improvement in this frozen comparison, not as a uniform recall improvement or proof of optimizer superiority.

| Policy | Precision | Decision recall | Automatic recall | Decision F1 | Automatic F1 | Review % | Coverage % | U |
|---|---|---|---|---|---|---|---|---|
| GB17_B0 | 0.9863 | 0.7466 | 0.7187 | 0.8494 | 0.8300 | 0.1884 | 99.8116 | 2352.0 |
| B0 | 0.9870 | 0.7486 | 0.7357 | 0.8510 | 0.8420 | 0.0871 | 99.9129 | 2364.2 |
| B1 | 0.9834 | 0.8146 | 0.7748 | 0.8910 | 0.8667 | 0.3847 | 99.6153 | 1864.6 |
| B2 | 0.9844 | 0.8124 | 0.7654 | 0.8901 | 0.8611 | 0.4273 | 99.5727 | 1860.0 |
| B3 | 0.9844 | 0.8127 | 0.7653 | 0.8903 | 0.8610 | 0.4318 | 99.5682 | 1858.2 |
| Chow | 0.9859 | 0.8384 | 0.7540 | 0.9061 | 0.8542 | 2.0442 | 97.9558 | 1879.0 |

Automatic recall = TP/(TP+FN+positive REVIEW); automatic F1 = 2TP/(2TP+FP+FN+positive REVIEW). Blocking-missed positives are included in FN. Decision recall/F1 retain the old convention, excluding positive REVIEW from their denominators. Precision measures MATCH decisions. Human correction is not assumed. Review rate/coverage use exact-tier plus model-scored candidates, excluding unreviewable blocking misses.

B0 -> B1 mean positive REVIEW increases from 160.7 to 430.0 and total REVIEW from 168.7 to 762.3. Coverage decreases from 99.9129% to 99.6153%. Automatic F1 changes by +0.073760, +0.000479 and +0.000070 in seeds 101/202/303. Thus two partitions have almost no automatic gain despite higher conditional F1. No significance or external-generalization claim is made.

Closed-form comparison: Chow has mean U 1879.0333, compared with B1 1864.5667, B2 1860.0333 and B3 1858.2333. B3's mean advantage is 20.8 U units. Chow is better than B1/B2/B3 in seed 101 (1823.4 versus 1856.9/1832.4/1826.9), whereas the search methods have lower loss in seeds 202 and 303. Direct posterior-risk optimality concerns expected cost under true posteriors, not guaranteed minimum realized loss from imperfect calibrated scores. Search's meaningful general advantage is NOT established.

The direct rule minimizes [p,.1,2(1-p)] in NO_MATCH/REVIEW/MATCH order; it requires no optimization budget. Its higher decision F1 (.9061) comes with 2.0442% review and automatic F1 .8542. This is reported rather than hidden.

## 4. Manuscript changes

- Abstract: conditional versus automatic F1, review burden, competitive direct-risk comparison, removal of CRM and optimizer-superiority implications.
- Introduction: pairwise profile-linkage motivation instead of speculative CRM; retained empirical model development and controlled genetic policy comparison.
- Methods: retained fixed cost; removed unneeded currency/handling-time narrative; defined four parameters/input normalization/ranges/repair/regions/boundaries; added direct posterior-risk baseline.
- Experimental Design: explicit original and automatic metrics, positive REVIEW, candidate denominator and coverage; unchanged original label-sealing protocol.
- Results: new six-method metric table and component counts; data-driven figure showing both F1 definitions; reduced headline interpretation; unchanged correct U ablation direction; actual validation anytime curves and representative vectors.
- Limitations: pairwise/non-transitive scope, missing-name behavior, exact-match heuristic, absent calibration diagnostics and competitive direct-risk baseline; no CRM passages.
- Conclusion: measured loss/coverage trade-offs rather than general classification/GA benefit; no downstream application claims.
- Editorial pass: concise academic clauses and headings; removed generic rhetorical sentences. No spelling/grammar mistakes or AI-detector evasion were introduced. Affected sections and supporting evidence are recorded in CHANGELOG.json and MANUSCRIPT_DIFF.patch.
- Bibliography unchanged. Existing Chow citation reused, not fabricated. Figures 1-3 retain their prior code/data lineage; Figure 3 remains historical development-only. Figure 4 regenerated from new aggregate.json; Figure 5 newly generated from six observed replay traces. Main table shows means to remain readable; complete sample SDs remain in SUPPLEMENTARY_RESULTS.md and aggregate.json.

## 5. AI disclosure audit

No current disclosure was found in the repository manuscript. The reviewer/user's quoted “solely English grammar editing and language polishing” sentence is not a verified repository quotation. Full historical AI usage cannot be established. Current revision assistance demonstrably extends to code and analysis, so a polishing-only description would not accurately describe adoption of this work.

AUTHOR CONFIRMATION REQUIRED. No disclosure was inserted automatically. AI_DISCLOSURE_AUDIT.md contains the actual current-assistance scope, one author-approval wording option, and the verified IEEE general policy (snapshot retained). ICSEC-specific anonymous-review placement still requires confirmation. No independent author review is claimed before authors actually do it.

## 6. Unresolved items

1. Exact M5 reviewer wording/source; added edge-case clarifications do not certify resolution of an unspecified complaint.
2. Actual submitted manuscript/disclosure version, complete historical AI-use inventory, author approval of wording, and conference-specific disclosure placement.
3. ICSEC 2026 page-limit/current submission instructions; the revised PDF is six pages, but conference compliance is not inferred solely from page count.
4. Historical model-family screen is summary-supported development motivation, not retrained or independently reproduced from original validation predictions.
5. Complete from-scratch MiniLM generation lineage: cache SHA is verified, but recovered local revision metadata is not an original generation receipt.
6. Original unresolved data licensing/redistribution/consent/ethics documentation. Local analysis does not authorize public data release.
7. No calibration-quality study, statistical proof of a search advantage, human-review effectiveness, entity clustering, or external generalization is established. These limitations are stated rather than invented experiments.

## 7. Final verification

- Initial frozen outputs: 93 hash-manifest entries verified; frozen source/input hashes checked before additive analysis and validation replay.
- Independent metrics: all 18 policy/partition rows checked; original 15 results preserved; all three new baseline decisions minimize the declared posterior risk and retain original exact/miss scopes.
- Optimizers: six complete 12,000-call traces; 48 actual checkpoints; all original final vectors reproduced exactly; traces have nonincreasing incumbent loss.
- Full repository suite: `uv run --python 3.11 --extra dev pytest -q` -> 102 passed (tests_final.log). New tests cover risk minimization, invalid posteriors, REVIEW denominator/coverage, and documented policy boundaries. Initial TDD failures and subsequent passes were observed.
- Figure generation: `uv run --python 3.11 python paper/reviewer_revision/generate_figures.py` executed successfully.
- Build: Tectonic compilation with BibTeX and reference-settling passes succeeds; revised PDF has six pages. All pages rendered and visually checked; no clipping/overlap or results after the conclusion/references. Fonts embedded; anonymous metadata.
- `verify_revision.py` verifies row-level metrics, aggregation, signed narrative comparisons, table rounding, reference labels, figure files, all 13 cited bibliography keys and no uncited entries, no CRM/application terms, and source anonymity.
- No missing figures, overfull boxes, undefined citations or cross-references. Remaining TeX warnings: font substitutions, one underfull paragraph and one underfull page box. The last page is references-only with whitespace; no filler or formatting hacks were added.
- `git diff --check` passes for the existing tracked diff. New files are checked independently; no commit, push, user-change reset or frozen-artifact rewrite performed.
- Final package checksums are closed after reports/logs exist and verified separately.

## Reproduce locally

From /Users/thawaree.kha/Project-for-Work:

    uv run --python 3.11 --extra dev pytest -q
    uv run --python 3.11 python -m experiments.code.run_reviewer_revision
    uv run --python 3.11 python paper/reviewer_revision/generate_figures.py
    tectonic -X compile paper/reviewer_revision/main.tex --keep-logs --keep-intermediates
    tectonic -X compile paper/reviewer_revision/main.tex --keep-logs --keep-intermediates
    uv run --python 3.11 python paper/reviewer_revision/verify_revision.py
    uv run --python 3.11 python paper/reviewer_revision/verify_scope.py

The additive runner writes only its reviewer_revision directory, not the frozen scientific runs. Reproduction rewrites derived analysis outputs; archive the current revision package before rerunning if byte-level provenance must be preserved. Reclose manifests after any regenerated artifact or report changes.

## Gate status / next safe action

Technical revision: VERIFIED.
Submission approval: NOT READY — M5 and disclosure/conference confirmations remain.
Next safe action: author supplies exact M5 text and approves a factually complete AI disclosure plus conference-specific placement. Then insert only the approved disclosure/necessary edge-case correction, rebuild, re-audit claims, and reclose checksums. No further test-driven policy tuning is justified by this revision.
