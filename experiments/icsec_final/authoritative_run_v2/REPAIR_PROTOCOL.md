# ICSEC 2026 authoritative_run_v2 repair protocol

Status: FROZEN DESIGN — pre-execution only
Historical `experiments/icsec_final/authoritative_run/` is read-only.

## 1. Defect and corrected feature

The historical `name_sim` cache was not a pure name similarity. It computed the maximum Jaro–Winkler similarity across four cross-field pairs only when a predecessor score was at least 0.5 and the row was not `AUTO_EXACT`; other rows were forced to zero. The predecessor artifact and its split/label lineage are not reproducible. This is a hidden learned dependency, experimental confound, and invalid construction relative to the declared feature.

v2 `name_sim` is the deterministic maximum of the four Jaro–Winkler similarities between normalized `userName` and `fullName` values on the two profiles. Empty values contribute no candidate and the result is 0.0 when no candidate exists. It reads no score, decision, model, label, split, or cache.

## 2. Label-isolation defect and architecture

v1 loaded `actual` into the candidate table and read it while calculating test constants before model fitting and policy selection. v2 keeps profile/features and labels in separate artifacts. TRAIN, CALIBRATION, and POLICY_VALIDATION receive only their own labels. SEALED_TEST labels are opened exactly by the final evaluator after all models, calibrators, policies, seeds, and configurations are frozen. Instrumentation denies any pre-final sealed-label request and records phase, resource, allow/deny, and source location. Required invariant: `PRE-FINAL TEST LABEL READS = 0`.

## 3. Controlled baselines

- B0: fixed simple policy; MATCH at p >= 0.98, REVIEW at 0.95 <= p < 0.98, otherwise NO_MATCH; no validation tuning.
- B1: same two-threshold simple policy family as B0; tune only `(t_match, t_review)` on POLICY_VALIDATION labels using deterministic Sobol points and the predeclared objective `2*FP + 1*FN + 0.1*REVIEW`.
- B2: four-parameter policy `[t_match, t_review, c_promote, c_demote]` with the B3 decision semantics and bounds; optimize with deterministic Sobol search on POLICY_VALIDATION only.
- B3: the same four-parameter policy class, objective, bounds, and validation rows as B2; optimize with the existing seeded GA.

B2→B3 is the optimizer comparison. No test label is available to any selection path.

## 4. Budget fairness

One evaluation means one candidate policy evaluated over the complete POLICY_VALIDATION scored-pair array. The realized GA count is instrumented, including initial population and every generation evaluation, duplicate vectors included. Sobol receives exactly that realized count per outer split. GA seeds are 101, 202, and 303 (one policy search per outer run unless the frozen implementation declares independent GA replicates); Sobol direction/seed and stopping rules are frozen before execution.

## 5. Provenance

Every v2 reproducible input, output, source/configuration file, model, calibrator, split manifest, cache, prediction, decision, and report receives SHA-256 capture. The chain is raw/transformed source → normalized profiles → candidates → corrected handcrafted features → MiniLM feature → splits → GB models → calibrators → B0/B1/B2/B3 policies → sealed predictions → final label join → decisions → metrics. The predecessor score and all v1 affected feature caches are excluded from v2 dependencies.

## 6. Rerun scope

A full new repeated outer experiment is required after repair, using outer seeds 101, 202, and 303, rebuilt pair-keyed candidates, regenerated corrected GB-17 and GB-18 features, pinned MiniLM revision, entity-disjoint roles, retrained GB models, recalibration, all four baselines, sealed final evaluation, independent metric recomputation, and closed provenance.

No scientific experiment is executed by freezing this protocol. Dry runs, if needed, are infrastructure checks only and are not manuscript evidence.

## 7. Suspended claims

Until v2 passes the audit and produces results, suspend: any GA-specific causal benefit claim; any claim that test labels were unavailable in the historical run; historical GB-17/GB-18 feature-ablation interpretation; any v1 performance result as authoritative v2 evidence; any claim of universal optimizer superiority, business benefit, deployment validation, consent, IRB approval, formal dataset license, or redistribution permission.
