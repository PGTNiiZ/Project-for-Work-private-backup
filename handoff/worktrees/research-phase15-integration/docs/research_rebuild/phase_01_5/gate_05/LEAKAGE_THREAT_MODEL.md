# Gate 5 — leakage threat model

| Threat | Control | Synthetic check | Residual risk / disposition |
|---|---|---|---|
| Same entity appears in multiple roles | Assign folds to entity_id; profiles inherit fold; validate disjoint role entity sets | Deterministic entity assignment test | Actual mapping and manifest not run; Gate 1–3 approval records missing in inspected docs |
| Pair endpoints route by only one side | Resolve both profile_row_id endpoints to entity and role; reject/drop cross-role pairs | Synthetic cross-role routing test | Real pair counts not computed |
| Candidate/feature code sees labels | Separate generation and label access contracts; reject label-bearing candidate/feature inputs | Not implemented as whole-pipeline executable guard | Must be integrated and adversarially tested |
| Learned preprocessing uses non-TRAIN rows | Fit vocabulary/IDF/scalers/imputers only on TRAIN; transform other roles | Not tested against production preprocessing adapters | All-role TF-IDF was a historical risk; integration remains required |
| Calibration/policy selection touches TEST | Calibration-only fit; POLICY_VALIDATION-only selection; frozen predictions before final label join | In-memory synthetic lifecycle fixture only | Same operator/file access can bypass a programmatic guard |
| Historical exploration makes TEST effectively known | Explicitly classify study as retrospective reanalysis | Documentation check | Cannot be repaired with a new seed; no external validation claim |
| Small/rare platform strata poorly balanced | Record counts and empty/small strata per fold | Synthetic assignment determinism only | Stratification by platform-pattern does not guarantee covariate or entity-size balance |
| Mapping ambiguity/missing entities mislabels pairs | Fail closed for unknown/conflicting endpoint mapping; do not label unknowns negative | Not run on project data | Accepted mapping/disposition record required |

This is a programmatic research-integrity threat model, not a claim of adversarial security or independent TEST custody.
