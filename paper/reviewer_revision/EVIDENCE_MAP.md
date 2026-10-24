# Read-only repository audit and claim/evidence map

## Authority and scope

Repository: Project-for-Work. Initial tree was extensively dirty, with deleted legacy scripts and untracked scientific/paper trees. No user changes were reset, committed, or pushed. Current source: paper/overleaf_v3/main.tex. Numerical authority: experiments/icsec_final/authoritative_run_v2r1, as declared in paper/audit/final_v2r1_and_paper_v3_audit.md. Historical authoritative_run and authoritative_run_v2 outputs are not alternate sources of favorable numbers. V2R1 consumes frozen V2 input caches; that is input lineage, not pooling historical V2 results.

The audit was reported in conversation before manuscript changes and before the additive baseline/replay. All 93 V2R1 output-manifest entries passed hash checks. All 15 workflow method/partition artifacts reproduced original F1 and U from unique pair keys and row-level labels/decisions. The primary contribution remains model development plus downstream policy comparison, not a novel GA or classifier.

## CLAIM -> CODE -> RESULT ARTIFACT -> MANUSCRIPT LOCATION

| Claim/definition | Code | Persisted evidence | Revised location |
|---|---|---|---|
| B0 fixed thresholds 0.98/0.95 | authoritative_run_v2/policies.py:b0_decide,B0_FIXED | V2R1 scientific_outputs/outer_*/policies.json and B0_workflow.parquet | IV-B; Table I |
| B1 simple validation tuning | policies.py:b1_search,_simple_genome | policies.json; frozen GB-18 probabilities; B1_workflow.parquet | IV-B; Tables I/III |
| B2/B3 expanded policy | policies.py:decide_four_parameter,BOUNDS,_valid_genome | policies.json; B2/B3_workflow.parquet | Equation 3; Tables I/IV |
| Original decision precision/recall/F1 | authoritative_run_v2/final_runner.py:_metrics,52-62 | unique pair-key workflow decision parquets and summary.json | V; Equations 7-10; Table III |
| End-to-end automatic metrics and positive REVIEW | reviewer_revision.py:metrics; independent verify_revision.py | reviewer_revision/metrics_per_seed.csv and aggregate.json | V; Table III/V; Abstract; VI/VIII |
| REVIEW=1, NO_MATCH=0, MATCH=2 | policies.py action constants and decision functions | row-level decision artifacts | IV/V |
| U lower is better: 2FP+FN+.1REVIEW | policies.py:_cost; final_runner.py:_metrics | summaries and independent per-seed recomputation | IV-A; Equation 1; VI |
| B0->B1 headline and abstention contribution | b0_decide,b1_search; original _metrics | B0/B1 workflow rows; revised independent metrics | Abstract; VI; VIII |
| GB17->GB18 U direction | final_runner.py:_metrics | original summary and revised aggregate: 2351.9667 -> 2364.2000 | VI semantic ablation; Figure 4 |
| Closed-form risk rule | reviewer_revision.py:chow_decide | outer_*/Chow_workflow.parquet, metrics_per_seed.csv | IV-C; Equations 4-6; Table III/V |
| Isotonic calibration | final_runner.py:train_and_calibrate,149-175 | models/GB-18_calibrator.pkl, training.json | III-C; IV-C |
| Scorer and sampling config | final_runner.py:GB_PARAMS,deterministic_sample_indices | models/*_model.pkl; training.json; frozen feature caches | III-C |
| Sobol deterministic sequence and budget | policies.py:b1_search,b2_sobol_search | policies metadata; original fairness.json; replay CSVs | IV; VI; Figure 5 |
| GA population/mutation/budget and ties | policies.py:b3_ga_search | original optimizer_budget_transparency.json, policies.json; replay verification | IV-B; VI; Figure 5 |
| Actual anytime curves and selected vectors | run_reviewer_revision.py validation-only instrumentation | six complete traces, 48 checkpoints, selected_vectors.csv | VI; Figure 5; Table IV |
| Four-way name similarity and missing comparisons | features.py:_normalize,corrected_name_sim | frozen gb17.parquet; original feature schema; boundary/missingness tests | III-C; IV-B; VII |
| Candidate universe/positives/coverage | full_candidate.py:load_profiles,count_cross_platform_all_pairs; run_icsec_authoritative_v2.py:candidate_scope | frozen candidates; profile data SHA; aggregate scope verification | III-A; Figure 2 |
| Entity-disjoint roles and label isolation | run_v2r1.py; real_adapters.py; sealed_guard.py; final_runner_r1.py | split manifests, process_label_access_audit.json, pre_label_prediction_freeze.json | V; Table II |
| Historical family validation AP/AUC | historical development screen, not final scientific training | train_data/stage7_8_rebuilt_experiment_tuned/best_run.json | III-B; Figure 3 |
| CRM/downstream business outcomes | No supporting experiment | None: passages removed | Abstract/I/VII/VIII |
| Exact M5 comment and historical AI-use disclosure | Not present in located source/audits/ZIP TeX variants | Missing author documentation | AUTHOR CONFIRMATION REQUIRED |

## Numerical lineage levels

Main workflow results are independently recomputed from row-level artifacts, not merely accepted from summaries. Closed-form outcomes are independently checked against risk argmin and common exact/miss scopes. Candidate accounting was recomputed from current eligible profiles plus persisted candidate keys: 36,804 eligible profiles, 449,149,239 possible cross-platform pairs, 29,243 cross-platform positives plus 4 same-platform positives, 12,403 exact and 2,073,842 model-scored candidates; 25,931 covered and 3,312 missed positives. Historical development AP/AUC values match the persisted leaderboard but historical training was not rerun and complete row-level validation predictions were not established. Those values remain explicitly development-only.

Every revised table value is generated from additive analysis of this one frozen family. Hyperparameters/bounds/budgets come from code/configuration rather than measured outcomes. Cost coefficients are declared assumptions, not inferred economic costs. Citation years/metadata are bibliography facts, not experiment outputs; the bibliography is copied unchanged and citation closure is verified.

## Missing lineage / unresolved facts

No historical optimizer trace was stored: the new traces are explicitly retrospective validation-only replays, with all six final vectors reproduced exactly. No historical AI-use inventory or exact M5 reviewer wording was found. The MiniLM cache is hash-frozen; the recorded model revision was recovered from local cache metadata rather than an original generation receipt, so complete from-scratch embedding lineage is not proven by that record alone. Historical development-screen training is not reproduced in this revision.
