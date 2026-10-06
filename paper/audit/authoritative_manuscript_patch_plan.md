AUTHORITATIVE MANUSCRIPT PATCH PLAN
ICSEC 2026 — do not apply in this audit

Basis

The authoritative source is experiments/icsec_final/authoritative_run/. The new central experiment is the repeated outer family, not the historical primary split. Values below come from raw_metrics_by_outer.csv and aggregate_metrics.csv, which were independently recomputed from workflow_decisions.parquet.

Status by quantitative statement in paper/overleaf/main.tex

| Location | Current statement/value | Action | Recommended authoritative handling |
|---|---|---|---|
| Abstract, line 19 | Mean F1 GA 0.8603 vs 0.8280; recall 0.7099 to 0.7614; FP 38.0 to 75.7; REVIEW 438.0 to 923.3 | CHANGE | GA F1 0.860406 ± 0.001204 vs GB-18 0.828038 ± 0.022279; recall 0.761481 ± 0.002898 vs 0.709996 ± 0.032258; FP 75.667 ± 38.423 vs 38.0 ± 7.0; REVIEW 923.333 ± 151.133 vs 438.0 ± 406.089. Keep the qualitative trade-off. |
| Abstract, line 19 | 36,807 profiles and about 449m to 2.09m; retrieval 88.6742% | KEEP | Retain, but identify retrieval as cross-platform and state exact/model-scored decomposition in methodology. |
| Methodology, line 66 | Raw platform counts 13,960 / 11,890 / 10,957; eligible 36,804 | CLARIFY SCOPE | Raw counts are retained. Candidate generation uses 36,804 eligible rows with current valid-identifier filters; authoritative eligible platform counts are 13,959 / 11,889 / 10,956. |
| Methodology, line 68 | Workflow 2,086,245 of 449,149,239; omits 3,312 | KEEP | Retain with explicit “cross-platform blocking misses” wording. |
| Retrieval table, lines 78–86 | Raw platform counts; 36,804; 449,149,239; 12,403/2,073,842; 2,086,245; 99.5355%; 29,243; 25,931/3,312; 88.6742% | KEEP / CLARIFY SCOPE | Values are authoritative. Label 29,243 as cross-platform labeled positives; label 3,312 as cross-platform blocking misses. Add a separate note if 29,247 all-platform positives is mentioned. |
| Experimental Design, line 134 | Historical primary role counts 510,981 / 26,246 / 22,873 / 195,440 / 1,330,705 | REMOVE | Remove the separately frozen primary split counts. If role counts are useful, cite the new per-seed split_manifest.json files and report their authoritative values only. |
| Experimental Design, line 143 | Old frozen-primary conditional bootstrap | REMOVE | The old primary split is not independently reproducible. No new bootstrap was generated; do not retain the old interval. |
| Results, line 147 | Primary GB-17 0.5963 to GB-18 0.8387; outer means 0.8292 vs 0.8280 | CHANGE | Remove the primary-split comparison. Use the new outer result: GB-18 mean F1 0.828038 ± 0.022279 versus GB-17 0.829259 ± 0.027775; describe the effect as mixed/non-uniform. |
| Main performance table, lines 157–159 | Historical repeated means and SDs | CHANGE | GB-17: P 0.990951±0.005090, R 0.713792±0.043091, F1 0.829259±0.027775, FP 59.0±35.763, FN 2265.333±111.689, REVIEW 264.667±395.880, U 2409.8±97.216. GB-18: P 0.993957±0.001072, R 0.709996±0.032258, F1 0.828038±0.022279, FP 38.0±7.0, FN 2151.0±234.207, REVIEW 438.0±406.089, U 2270.8±200.171. GB-18-GA: P 0.988901±0.005469, R 0.761481±0.002898, F1 0.860406±0.001204, FP 75.667±38.423, FN 1558.0±39.0, REVIEW 923.333±151.133, U 1801.667±69.278. |
| Per-seed table, lines 173–175 | Historical F1/U rows | CHANGE | Seed 101: GB-17 .839577/U 2520.2; GB-18 .840998/U 2048.2; GA .861751/U 1756.2. Seed 202: .797801/2337.0; .840802/2436.0; .860040/1767.4. Seed 303: .850398/2372.2; .802313/2328.2; .859428/1881.4. |
| RQ2, line 181 | Old GA minus GB-18 F1/recall/FN/U changes | CHANGE | Use new paired differences: F1 +0.020753/+0.019238/+0.057114; U -292.0/-668.6/-446.8 by seeds. Across seeds, F1 +0.032368, recall +0.051485, FN -593.0, U -469.133; FP +37.667 and REVIEW +485.333. |
| RQ2, line 183 | Old primary bootstrap intervals | REMOVE | The old bootstrap is tied to the unreconciled primary family. Do not reuse it. State that uncertainty is represented by outer-split variation unless a new paired bootstrap is separately generated. |
| RQ3, line 186 | 99.5355%, 25,931/29,243, 88.6742%, 3,312; outer recall 0.8838±0.0002 and misses 1023.7±10.2 | CHANGE | First four values KEEP. New outer candidate recall is 0.883872 ± 0.000136 (sample SD), with 1,025 / 1,012 / 1,031 misses for seeds 101 / 202 / 303. Do not retain the old mean±SD. |
| Sensitivity, line 188 | 8 of 12 scenarios; fixed-policy sensitivity | CLARIFY SCOPE | Keep only if the stale note in historical cost_sensitivity.csv is explicitly corrected in a regenerated table. Identify all scenarios as post-hoc and state that frozen selection used 2/1/0.1, not 5/1/0.02. |
| Failure analysis, line 191 | Primary GA scored FP 96, FN 559 and feature-missingness counts | REMOVE | These are old-primary scoped and are not part of the new authoritative package. Recompute from new row-level decisions before making any replacement claim. |
| Platform-pair failure analysis, line 193 | Primary scored-candidate F1 by platform pair | REMOVE | Not regenerated for the authoritative run. Do not carry forward historical primary values. |
| REVIEW interpretation, line 195 | Primary 480 positive / 367 negative review counts | REMOVE | Not regenerated for the authoritative run. Replace only after a new aggregate analysis from authoritative rows. |
| Conclusion, line 207 | GA consistently improves across three outer partitions; candidate omission about 11.3% | KEEP / CLARIFY | GA F1 and recall do improve in all three new outer splits; cite new values. Keep the retrieval ceiling, but name 3,312 as the full cross-platform miss constant and distinguish it from per-outer test misses. |

Global required clarifications

1. Replace the central evidence family with the new repeated outer package.
2. Remove all dependency on the old frozen primary split, including its role counts, primary F1/utility results, old failure counts, and conditional bootstrap.
3. Replace the main repeated-outer table with the new aggregate_metrics.csv values.
4. State that all workflow metrics are exact-tier + model-scored + blocking-missed rows, and cite row-level local artifacts.
5. State that 29,247 is TOTAL LABELED POSITIVES, 29,243 is CROSS-PLATFORM LABELED POSITIVES, and 4 is SAME-PLATFORM POSITIVES excluded from the workflow.
6. Keep U = 2*FP + FN + 0.1*REVIEW and call it illustrative, not measured cost.
7. Do not use historical 5/1/0.02 metadata as the frozen objective.
8. Cite the authoritative package's environment, package, commit, status, and SHA256SUMS artifacts in the reproducibility statement.
9. Preserve the dual eligibility rule: valid profile_row_id and valid profile_id.
10. Do not patch the manuscript until final hash verification and tests pass.
