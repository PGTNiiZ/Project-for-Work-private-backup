# V2R1 — Integrity-Repaired Verification Rerun Protocol

## Versioning
- `authoritative_run_v2`  = pre-integrity-repair authoritative run. Preserved
  unchanged as the historical package. Its protocol documents are FROZEN
  (hashes sealed in `scientific_inputs/frozen_protocol_hashes.json`) and are
  superseded, where corrected below, by this document.
- `authoritative_run_v2r1` = integrity-repaired verification rerun. If it
  passes, it is the ONLY numerical source for the paper.

## Scientific freeze (unchanged from v2)
Dataset scope, candidate generation and candidate pairs, the 17 handcrafted
features, the frozen MiniLM `bert_cos` cache (by SHA-256), Gradient Boosting
configuration (300 / 0.05 / 6 / rs=42), 3:1 deterministic negative sampling,
isotonic calibration on CALIBRATION only, outer seeds 101/202/303,
entity-role manifests, B0–B3 definitions and search domains, the utility
objective U = 2·FP + FN + 0.1·REVIEW, optimizer seeds, GA behavior, the
12,000 objective-call budget, the Sobol sequences, and all metric formulas
are IDENTICAL to v2. v2r1 consumes v2's frozen input artifacts verbatim,
verified by SHA-256.

## Integrity repairs (the only changes)
1. **Sealed-label access by construction.** Pre-final validation inspects
   sealed-label artifacts via SHA-256, parquet footer schema, row count, and
   a pair-key-only column read. The ground-truth `actual` column is NEVER
   materialized before FINAL_EVALUATION. The single allowed API remains
   `LazySealedLabelStore.read(phase="FINAL_EVALUATION")`.
2. **Precise invariant, process-wide instrumentation.** The invariant is
   `SEALED_TEST LABEL VALUES MATERIALIZED BEFORE FINAL_EVALUATION == 0`
   (not "zero file-byte reads"; hashing and footer inspection do read bytes
   and are audited as non-materializing events). A process-wide guard patches
   `pandas.read_parquet` and `pyarrow.parquet.read_table`; any pre-final
   materialization attempt raises. Audit counts are derived from runtime
   events, never hard-coded.
3. **Pre-label prediction freeze.** Order enforced: frozen model → frozen
   calibrator → frozen policy → label-free SEALED_TEST predictions →
   canonicalize → SHA-256 → PRE-LABEL FREEZE MANIFEST
   (`pre_label_prediction_freeze.json`: hash, row count, safe pair-key hash,
   model/policy identifiers, timestamp) → verify → FINAL_EVALUATION.
   Final evaluation refuses to begin without the manifest, and the artifact
   is re-hashed after evaluation (`prediction_immutability.json`); pre/post
   hashes must match. The independent deterministic-replay check is retained.
4. **Lifecycle.** artifact preparation → seal → scientific runner starts →
   no test-label-value materialization → predictions frozen → final label
   reveal. The sealed-label producer is a controlled preparation step, not
   part of training or policy selection.
5. **Fresh provenance.** `provenance/v2r1_manifest.json` records git commit /
   dirty / untracked status, dataset SHA, candidate/feature/MiniLM-cache/
   split/label/blocking-miss hashes, and current source hashes for the
   runner, producers, policies, and this protocol. No stale v2 source hashes
   are carried forward.

## GA / optimizer documentation corrections (behavior unchanged)
- The v2 `BASELINE_PROTOCOL.md` line "60 × 40 = 12,000" is arithmetically
  wrong. Actual implementation: population size 60, budget-driven execution,
  200 evaluated populations, 60 × 200 = 12,000 realized objective calls.
- Actual search bounds (both B2 and B3, with repair clipping t_review ≤
  t_match and c_demote ≤ c_promote):
  t_match ∈ [0.90, 0.999], t_review ∈ [0.50, 0.90],
  c_promote ∈ [0.50, 1.00], c_demote ∈ [0.00, 0.60].
- GA duplicate evaluations are RETAINED by design (no caching/dedup). The
  budget equalizes realized objective calls, not unique vectors. v2r1
  reports both objective calls and unique evaluated vectors per seed.
- Decision boundary semantics (exact operators): MATCH if p ≥ t_match;
  NO_MATCH if p < t_review; in the band t_review ≤ p < t_match, MATCH if
  name_sim ≥ c_promote, NO_MATCH if name_sim < c_demote, else REVIEW.
  B0/B1: MATCH if p ≥ t_match; REVIEW if p ≥ t_review; else NO_MATCH.

## Contrast labeling (domains preserved; no post-hoc redesign)
- B0 → B1: validation selection within the simple-policy domain.
- B1 → B2: transition from the tuned simple policy to the declared expanded
  four-parameter policy/search domain. NOTE: B1 and B2 are NOT strictly
  nested (B1 allows t_review up to 0.999; B2/B3 cap it at 0.90).
- B2 → B3: clean optimizer comparison under identical policy class, bounds,
  objective, validation data, and 12,000 objective-call budget.

## Metric definition (frozen; renamed for accuracy)
The main metric is **decision recall** = TP / (TP + FN), where FN counts
positive NO_MATCH decisions plus blocking-missed positives; positive REVIEW
cases are deferred and excluded from the denominator. This definition is
preserved unchanged from v2 for comparability. It is not conventional
end-to-end binary recall. Blocking-missed positives are never passed through
the classifier; they enter workflow evaluation directly as FN.

## MiniLM provenance
The frozen `features/bert_cos.parquet` cache is retained by SHA-256 and is
not regenerated. The encoder revision is recorded in
`provenance/v2r1_manifest.json` if recoverable from the local HuggingFace
cache; otherwise it is explicitly marked unresolved. The feature values are
unchanged either way.
