HISTORICAL ARTIFACT CLASSIFICATION

Authoritative comparison target: experiments/icsec_final/authoritative_run/raw_metrics_by_outer.csv and aggregate_metrics.csv, independently derived from the new workflow_decisions.parquet files.

| Historical artifact/family | Classification | Reason |
|---|---|---|
| experiments/icsec_final/primary_reproduction/test_results.csv | DIFFERENT SCOPE | Single historical primary split; not the new three-seed repeated outer family. Its workflow constants also do not reconcile with current row-level evidence. |
| experiments/icsec_final/primary_reproduction/raw_metrics_recomputed.csv | DIFFERENT SCOPE | Same historical primary result family as test_results.csv; agreement with that summary is not reproduction of the new outer family. |
| experiments/icsec_final/primary_reproduction/decisions/sealed_test_decisions.parquet | DIFFERENT SCOPE | Valid pair-key-aligned model-scored test decisions, but excludes exact-tier rows and blocking-missed positives; it is not a complete workflow table. |
| experiments/icsec_final/repeated_outer/all_results.csv and summary.csv | HISTORICAL | Same nominal outer seed family, but generated earlier with a different constant/result lineage. The new run was executed from the current source and fresh candidate artifacts. |
| experiments/icsec_final/primary_reproduction/ | HISTORICAL | Superseded primary reproduction package retained unchanged for audit history; not used as authoritative evidence. |
| experiments/icsec_final/primary_reproduction/statistical_analysis/paired_bootstrap_ci.csv | INCOMPLETE | Conditional bootstrap is tied to the unreconciled historical primary workflow family and was not reused. |
| historical blocking_missed_pairs.csv path recorded in prior manifests | UNVERIFIABLE | The referenced row-level file is absent from the repository; the new package contains a fresh row-level miss artifact. |
| historical cost_sensitivity.csv | STALE | Its note incorrectly associates frozen selection with 5/1/0.02; the new protocol freezes 2/1/0.1 and does not use the historical table for selection. |
| experiments/code/exp_lib.py TOTAL_POS_FULL=29247 | STALE | 29,247 is all-platform scope, while the paper workflow denominator is 29,243 cross-platform positives. |

The historical values are not required to match the new values. They are retained for audit traceability only and are excluded from the authoritative manuscript evidence chain.
