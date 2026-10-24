# Gate 4 verification report

## Result

- Feature registry encodes exactly 17 ordered columns matching authoritative `FEATURE17_COLUMNS` as read in primary worktree `features.py` (primary tree remained read-only).
- Formula, normalization, range, missing-value behavior and pair symmetry are specified in `FEATURE_SPEC_V1.md`; no feature has a learned score/label input. The unconditional cross-field `name_sim` is explicitly distinguished from the historical score-gated variant.
- `bert_cos` is documented as the one scalar addition in Feature 18. Phase 1 records cache replay outcomes and embedding dimensions; this Gate did not access caches, labels, or run training. Exact encoder/tokenizer revision provenance remains open.
- Under the requested Gate 9 method labels, E1 is Logistic Regression + 17 features; E2 is Gradient Boosting + the same 17; E3 is Gradient Boosting + those 17 plus `bert_cos`. The proposed feature schemas for E2 and E3 therefore differ by exactly one column. This schema-level assertion is not an artifact/cache replay.

## Checks run

- Parsed `FEATURE_REGISTRY.json`; asserted 17 entries and exact ordered-name alignment. Lead AST comparison against primary source `FEATURE17_COLUMNS` passed. E1/E2/E3 schema assertion (17 / 17 / 18; E...[truncated]

## Evidence caveats

Phase 1 `dataset_v2_feature_verification.json` reports 2,073,842 rows and zero mismatches for each of the 17 corrected GB features; `dataset_candidate_accounting.json` reports legacy and authoritative-v2 MiniLM cosine replay evidence. Those figures are quoted as prior audit evidence, not Gate 4 reproduction. Data-level E2/E3 cache pairing, exact pair-key alignment and a separate E2/E3 difference remain unverified.

## Scope / status

Only `docs/research_rebuild/phase_01_5/gate_04/` and `tests/test_feature17_synthetic.py` were written in the isolated worktree. No commit. Base/HEAD: `1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b`; branch `research/phase15-feature-spec`.
