# Gate 6 — metric definitions

The evaluator operates on unique unordered pairs of distinct profile rows. `exact` and `scored` are candidate tiers; blocking misses are separate positive pairs that were not generated as candidates. Metrics are returned separately for CANDIDATE (exact + scored) and WORKFLOW (candidate + missed positives). No ungenerated negatives are fabricated.

For rows assigned action MATCH / REVIEW / NO_MATCH:

- TP: positive MATCH; FP: negative MATCH.
- FN_candidate: positive NO_MATCH in exact or scored candidates.
- FN_workflow: FN_candidate plus positive blocking-missed pairs.
- R+: positive REVIEW; R−: negative REVIEW; REVIEW=R++R−.
- TN_candidate: negative NO_MATCH among supplied exact + scored candidates only.
- Automatic precision = TP/(TP+FP) (also retained under compatibility key `precision`).
- Decision-conditional recall = TP/(TP+FN_candidate).
- Automatic recall = TP/(TP+FN_workflow+R+).
- Automatic F1 = 2TP/(2TP+FP+FN_workflow+R+).
- Candidate coverage = 1 − REVIEW/(number of exact+scored candidates); misses are not in the denominator.
- U = c_FP·FP + c_FN·FN + c_REVIEW·(R+ + R−); candidate U excludes misses, workflow U includes them.

Undefined ratios return Python `None` (JSON null), not silently zero. Every output must retain scope, denominator/support counts, costs and pair-type coverage. The default illustrative costs `(2,1,0.1)` are an assumption, not measured CRM costs.
