# Gate 6 — verification report

Status: PRE-INTEGRATION WORKER REPORT (PARTIAL; superseded by the Lead integration implementation addendum below).

- Implementation: `evaluator.py`, stdlib-only; not imported from production/historical evaluators.
- Synthetic unittest command executed from this worktree: `python3.11 -m unittest discover -s docs/research_rebuild/phase_01_5/gate_06 -p test_evaluator.py -v` — 10 tests passed.
- Covered: positive NO_MATCH→REVIEW does not improve automatic recall/F1; missed positives included in workflow FN; exact-tier FP; all-REVIEW; zero-positive/undefined metrics as null; duplicate/reversed keys; invalid action; pair-scope overlap; costs; positive accounting; independent utility/count recomputation.
- The pre-integration Gate 6 worker did not read dataset, TEST labels, model, historical cache, or production evaluator.
- Still not verified: approved-snapshot adapter integration, historical role provenance, endpoints for blocking misses, full workflow denominator through the new adapter/evaluator, or real historical evaluator compatibility.
- Head is unchanged at base commit `1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b`; uncommitted isolated changes only. No Phase 2 work.

## Lead integration implementation addendum

`pair_adapter.py` now adapts versioned canonical V2 hashed keys only with explicit endpoint IDs or a unique explicit mapping; it recomputes the key, checks both endpoint entities/roles, preserves exact/scored/blocking-missed scopes, and handles positive/negative REVIEW. Adapter tests cover valid, missing, duplicate, ambiguous, mismatched, role-conflict, and review cases. Real read-only rejoin maps 193,692 historical exact/scored keys to explicit candidate endpoint rows; all 1,034 blocking misses lack endpoint rows, and the historical split-role manifest is NOT VERIFIED. No historical evaluator replay or new TEST evaluation was executed. Gate 6 is PASS only for the future A–F evaluator interface; historical all-scope compatibility remains PARTIAL.
