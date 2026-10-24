# Gate 06 — standalone evaluator specification

## Evidence read (read-only)

Primary evidence consulted: `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md` sections 2, 8, and acceptance table (especially 31–48, 122–141, 166–180); `docs/research_rebuild/phase_01/04_RESULT_COMPARISON_TH.md` definitions and scope cautions; `03_MODEL_AND_GA_EXPLANATION_TH.md` pair-role / REVIEW interpretation; and `06_PHASE_1_READINESS_GATE.md` criterion 5. In keeping with the Phase 1 boundary, no training, optimization, model loading, TEST artifact reads, or production-code edits were made. The evaluator and tests use synthetic rows only.

## Pair roles and unit

Each row denotes one unordered pair of distinct, non-empty profile-row IDs. Ground-truth `label` is integer 1 (same entity/positive) or 0 (different/negative). `exact` and `scored` rows are candidate decisions and must be disjoint. Exact decisions are predictions, not assumed truth. Scored rows additionally require finite `score` in `[0,1]` as trace metadata; the evaluator does not use scores to make decisions. Blocking-miss rows are positives not generated as candidates, disjoint from both candidate scopes, and are counted as workflow FN. This implementation expects caller-supplied decision labels; it does not infer split roles or labels from files.

Canonical keys lexically sort endpoint IDs, so `(A,B)==(B,A)`. Duplicate keys within a role and cross-scope overlap are rejected. Self-pairs, invalid IDs, invalid labels/actions, malformed costs, and non-positive blocking misses are rejected.

## Counts and metrics

For candidate scope, TP/FP are positive/negative MATCH; FN is positive NO_MATCH; R+/R− are positive/negative REVIEW; REVIEW=R++R−; TN_candidate is negative NO_MATCH in provided candidates only. Workflow FN additionally includes every blocking-missed positive. All-positive denominator is TP+FN+R+; with `expected_positives`, the workflow total and candidate-positive-plus-misses identity are checked. Required identities are `TP+FN+R+ = all positives` (workflow), `candidate positives + misses = all positives`, exact+scored=candidates, and REVIEW=R++R−.

Reported metrics: precision=TP/(TP+FP); decision-conditional recall=TP/(TP+FN_candidate); conditional F1=2TP/(2TP+FP+FN_candidate); automatic recall=TP/(TP+FN_workflow+R+); automatic F1=2TP/(2TP+FP+FN_workflow+R+); candidate coverage=(candidate rows−REVIEW)/candidate rows; and `U=c_FP*FP+c_FN*FN+c_REVIEW*REVIEW`. Candidate U excludes misses; workflow U includes them. Default scenario `(2,1,0.1)` is explicitly an assumed cost scenario, not verified business cost. Costs are explicit arguments and returned in output. Undefined ratios are Python `None`, which serializes as JSON `null`; in particular precision is `None` when TP+FP=0, and recall/F1 are `None` when their positive denominator is zero.

Metrics are provided for both candidate and workflow scope. An independent second-pass accumulator recomputes workflow TP/FP/FN/R+/R−/REVIEW/TN_candidate/U from raw label/action rows and miss count and asserts agreement. It intentionally does not treat ungenerated negatives as TN.

## Synthetic test contract

`python3.11 -m unittest -v test_evaluator.py` exercises exact FP, scored candidates, blocking misses, review class transitions, all-review, zero-positive and undefined precision, reversed-endpoint duplicate, invalid action, overlapping scopes, positive accounting mismatch, changed costs, and cost reconciliation. Tests are artificial implementation checks, not scientific evidence.

## Scope and limitation

This is a minimal row-level evaluator contract, not a data adapter, pair generator, split validator, optimizer, or authoritative-result runner. It requires upstream provenance and correct role/label construction. It does not read project data or any TEST artifact. No cost policy selection or scientific evaluation was performed.
