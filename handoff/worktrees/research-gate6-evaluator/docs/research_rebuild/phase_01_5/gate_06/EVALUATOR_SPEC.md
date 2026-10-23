# Central workflow evaluator specification — Gate 6

The implementation in `evaluator.py` is a standalone, stdlib-only reference; it does not modify or import the historical/production evaluator.

## Inputs

- `exact`: exact-tier decision rows, each with unique canonical unordered `pair_key`, binary `label`, and policy `action`.
- `scored`: disjoint model-scored rows with the same fields plus finite score in [0,1]. The evaluator consumes the decision, not a score-derived threshold.
- `blocking_misses`: positive pairs omitted from both candidate tiers; unique pair keys and label=1.
- Explicit non-negative finite `c_FP`, `c_FN`, `c_REVIEW`.

An endpoint may not pair with itself. Canonical key creation sorts stable profile-row IDs. Duplicate keys inside or across populations, invalid labels/actions, invalid scores, and negative/nonfinite costs are rejected. Pair role eligibility and entity-disjoint assignment remain upstream contracts and are not inferred by this evaluator.

## Decisions and accounting

Actions are exactly MATCH, REVIEW, NO_MATCH. `TP`/`FP` are positive/negative candidates MATCHed; `FN` includes positive candidate NO_MATCH and every blocking-missed positive; `R+` is positive candidate REVIEW; `R-` is negative candidate REVIEW. Exact-tier false positives are included. Candidate TN means candidate rows labeled negative and NO_MATCHed; it does not include the unenumerated all-universe negatives.

Required identities: all positives = TP+FN+R+; candidate-covered positives + missed positives = total positives; exact/scored keys disjoint; no duplicate keys; and utility reconciles exactly.

## Metrics

Emit `automatic_recall = TP/(TP+FN+R+)`, `automatic_precision = TP/(TP+FP)`, `automatic_F1 = 2TP/(2TP+FP+FN+R+)`, candidate coverage separately, candidate-scope TN, and `U = c_FP*FP + c_FN*FN + c_REVIEW*(R+ + R-)`. An undefined zero denominator is returned as null and documented with scope; it is not silently set to zero. A compatibility `precision` alias may be emitted but `automatic_precision` is canonical.

## Isolation and limits

The evaluator can validate row accounting but cannot prove that upstream labels were sealed, candidate generation was label-free, the split was approved, or inputs have rightful use authorization. It must be called only after prediction/policy freeze for final TEST; the synthetic tests do not create an integrated lifecycle boundary. The same local operator retains filesystem access, so this is programmatic—not security-grade—sealing.
