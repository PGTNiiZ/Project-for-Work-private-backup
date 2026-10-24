# Gate 6 — accounting invariants

The central evaluator rejects the input before scoring if any invariant fails:

1. Canonical `pair_key` is unordered over two distinct, nonempty endpoint IDs; no duplicate within a tier or blocking-miss list.
2. Exact, scored and blocking-miss key sets are pairwise disjoint.
3. Every exact/scored row has binary label and valid action in `{MATCH, REVIEW, NO_MATCH}`; every scored row has finite score in [0,1]; every blocking miss has positive label.
4. `exact_n + scored_n = candidate_n`; candidate generation identities must be independently reconciled upstream.
5. `candidate_positives + blocking_missed_positives = all_workflow_positives` when `expected_positives` is supplied.
6. `TP + FN_workflow + R+ = all_workflow_positives`.
7. `REVIEW = R+ + R−`.
8. Utility exactly recomputes from the returned FP/FN/REVIEW counts and explicit cost tuple for each scope.
9. Independent accumulator over row-level actions/labels and miss count must agree with reported workflow counts and utility.
10. `TN_candidate` is explicitly candidate-scoped. It does not include ungenerated negative pairs.

The evaluator cannot prove an upstream label, split, exact-tier or missed-pair source correct. Those sources require versioned manifests and a keyed independent audit.
