# Gate 5 — entity-aware split protocol (proposal)

Status: deterministic synthetic reference implemented; real snapshot assignment NOT RUN. This is not Phase 2 authorization.

## Identity and assignment

- `profile_row_id`: unique profile-row key; profile identifiers are not entity identifiers.
- `entity_id`: accepted mapping from `user_folder`; all rows for one entity are assigned together.
- `pair_key`: canonical unordered identity of two distinct profile rows.
- Platform-pattern stratum: sorted unique set of platform values present for an entity.
- Seed: `20261010`; five outer folds numbered 0–4. Within each platform-pattern stratum, sort entity keys, deterministically shuffle using the frozen seed and stratum signature, then assign round-robin to folds 0–4. This is approximate stratification; rare strata and profile/entity size imbalance remain.

For outer fold i: TEST=i; CALIBRATION=(i+1) mod 5; POLICY_VALIDATION=(i+2) mod 5; TRAIN=the remaining two folds. These are disjoint entity sets. Do not further repartition a fold by profile or pair. A real manifest requires an accepted Gate 1–3 mapping and must record snapshot/assignment code hashes and aggregate counts; do not publish entity IDs.

## Pair routing and accounting

Resolve both endpoints through `profile_row_id -> entity_id -> role`. Retain a pair only if both endpoints have the same role. Otherwise exclude and count as cross-role; never assign by the first endpoint. Reject unknown endpoints, self-pairs, duplicate canonical keys and conflicting entity mapping. Require `input_unique_pairs = retained_same_role_pairs + cross_role_dropped_pairs` for each source and pair type. Generate candidates without labels; join labels only in the isolated label-generation/evaluation boundary.

Fit corpus-derived preprocessing on TRAIN only; transform other roles without refit. Fit probability calibration on CALIBRATION, select scorer/policy only under a predeclared POLICY_VALIDATION rule, and freeze before TEST predictions. Pairwise fixed formulas may transform any role only if label-free and without corpus-fitted state.

## Threat boundary

Programmatic label lifecycle guards are not independent custody or security-grade blinding. The same operator with filesystem access may still inspect TEST labels, and this corpus has historical exposure. Report the new analysis as retrospective reanalysis, not an unseen corpus/external validation.
