# Gate 4 verification report

## Result

- Feature registry encodes exactly 17 ordered columns matching authoritative `FEATURE17_COLUMNS` as read in primary worktree `features.py` (primary tree remained read-only).
- Formula, normalization, range, missing-value behavior and pair symmetry are specified in `FEATURE_SPEC_V1.md`; no feature has a learned score/label input. The unconditional cross-field `name_sim` is explicitly distinguished from the historical score-gated variant.
- `bert_cos` is documented as the one scalar addition in Feature 18. The pre-integration worker cited Phase 1 cache replay outcomes/dimensions but did not access caches or labels or run training; exact historical encoder/tokenizer provenance remained open.
- The pre-integration worker's E1/E2/E3 schema assertion (17 / 17 / 18; E3=E2+`bert_cos`) was schema-level only; the Lead addendum below records the later persisted-artifact ordering checks.

## Checks run

- Parsed `FEATURE_REGISTRY.json`; asserted 17 entries and exact ordered-name alignment. Lead AST comparison against primary source `FEATURE17_COLUMNS` passed. E1/E2/E3 schema assertion (17 / 17 / 18; E...[truncated]

## Evidence caveats

Phase 1 `dataset_v2_feature_verification.json` reports 2,073,842 rows and zero mismatches for each corrected GB feature; `dataset_candidate_accounting.json` reports earlier MiniLM replay evidence. These are prior audit records. Historical E2/E3 aliases remain unresolved, but the Lead integration addendum separately verifies the current Feature17/`bert_cos` pair ordering and a 16-row independent cosine sample.

## Scope / status

Only `docs/research_rebuild/phase_01_5/gate_04/` and `tests/test_feature17_synthetic.py` were written in the isolated worktree. No commit. Base/HEAD: `1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b`; branch `research/phase15-feature-spec`.

## Lead integration implementation addendum

The earlier worker report describes the pre-integration state. In the integration worktree, a future-only Feature18 contract is now implemented in `feature18_contract.py` and `FEATURE18_CONTRACT_V1.json`; six contract tests pass. A read-only real-artifact audit verified local MiniLM revision and weight/tokenizer byte hashes, profile-ID order, and persisted Feature17/18 pair ordering; `../gate_05/REAL_SNAPSHOT_VERIFICATION.json` is the evidence. Historical text serialization and embedding-to-model revision binding remain NOT VERIFIED. No model was run, weights downloaded/replaced, or embeddings regenerated.
