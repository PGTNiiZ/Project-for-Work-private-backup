# Master Protocol Freeze Candidate — Phase 1.5

**Status: CANDIDATE FOR HUMAN SCIENTIFIC REVIEW — NOT FROZEN. `execution_authorized: false`.** This document consolidates verified technical contracts and open choices. It is not an approval, data-use authorization, ethics decision, or permission to begin Phase 2. It does not authorize training, optimization, or final TEST-label evaluation.

## 1. Study scope and claim boundary

Planned work is retrospective reanalysis of a previously explored cross-platform profile corpus, not external validation. Historical families (notebooks/neural models, multimodal, R0–R6, ICSEC V2/V2R1, GA variants) are not one controlled experiment. Do not combine their metrics or retroactively map their identifiers onto the new study.

Gates 1–3 are researcher-reported accepted; supporting decision records are NOT VERIFIED in inspected repository evidence. Gate 8 is PENDING HUMAN APPROVAL. This candidate cannot override those statuses.

## 2. Candidate experimental identities

Proposed new-study IDs from the Gate 4 contract:

- E1 — Logistic Regression on ordered Feature17.
- E2 — Gradient Boosting on the same ordered Feature17.
- E3 — Gradient Boosting on Feature17 plus `bert_cos` (Feature18).

These are new-study IDs only. Historical source artifacts identify GB-17 and GB-18, but inspected workbook evidence has no exact E2/E3 cells and no pair-keyed alias mapping. Do not claim historical E2=GB-17 or E3=GB-18 without a contemporaneous, authorized mapping record. The future-only Feature18 contract pins the local MiniLM revision and artifact hashes for a new run; historical embedding-to-model/text lineage remains open.

## 3. Candidate technical contracts

### Data and entities

- Use only a snapshot whose exact version/hash and eligibility rules are approved under Gate 1.
- Treat `entity_id` as the grouping key only after Gate 2 conflict disposition and Gate 3 label assumptions are documented.
- Technical split verification may run read-only against a clearly labeled candidate snapshot; it does not approve the mapping, authorize exclusions, or authorize use in an experiment. Use an approved snapshot/hash and disposition before execution.

### Entity split and label access

For five folds with held-out fold `i`: TEST=`i`, CALIBRATION=`(i+1) mod 5`, POLICY_VALIDATION=`(i+2) mod 5`, TRAIN=remaining two folds. Keep all profiles for an entity in the same role; exclude candidate pairs spanning roles. Fit transformations/models on TRAIN; calibration uses CALIBRATION; policy selection uses POLICY_VALIDATION. TEST labels remain sealed until a separately authorized final evaluation. The in-memory synthetic label boundary is not production security certification.

### Feature contract

Ordered Feature17 registry must match the copied, byte-identical source schema. Pair features must follow documented bounds, missingness, and symmetry. `bert_cos` is the sole proposed Feature18 addition. Hash feature-schema identity into each run manifest. Historical cached values are not accepted solely by matching names or row counts.

### Pair keys, accounting, evaluator

Use stable canonical unordered pair keys; reject duplicate/reversed duplicates. Keep exact-tier, scored-candidate, and blocking-missed scopes disjoint. Reconcile exact + scored rows to workflow and covered positives + blocking misses to the declared positive denominator. Positive REVIEW remains unresolved in automatic precision/recall/F1 and workflow accounting. Freeze denominators, action semantics, and utility coefficients scientifically before interpreting metrics/costs.

### Run manifest/cache

Use manifest v1 as the future technical candidate. Required compatibility identities: dataset hash, ordered feature-schema identity, pair-population identity, chunk size, model identity, source identity, split identity, configuration identity, environment/lock identity, and seed. The manifest stores state, run ID, pair count and chunk paths/hashes. COMPLETE finalization/cache validation require `artifact_root` and verify actual bytes, schema, full chunk coverage, duplicate keys and exact canonical pair-key sequence/order. Isolated byte tests pass; production caches remain untested and untouched; resume unsupported.

## 4. Protocol stages and governance

A–F are protocol stages, not experiment arms. Retain the Gate 9 draft's C0/C1 retrieval and P0–P5 policy-stage structure only after open choices are decided. Do not add arms such as Bloom or reinterpret A–F as models. The cross-gate wiring test is synthetic, while a separate read-only candidate-snapshot audit verifies the current split/routing and Feature17/18 pair-key alignments; neither is a production runner or uses an approved snapshot.

No data release, external sharing, or raw/pair-level publication is authorized here. Gate 8 privacy/publication requirements remain pending formal rights and ethics review.

## 5. Open scientific decisions before freeze

The scientific owner must disposition with rationale and record ID:

1. Historical E2/E3 alias treatment: obtain pair-keyed evidence or explicitly exclude those aliases from comparisons.
2. Feature18 provenance: adopt or reject the future-only pinned contract `gate_04/FEATURE18_CONTRACT_V1.json`; historical embedding revision/text/cache lineage and pair-keyed E2/E3 alias records remain unverified.
3. C1 retrieval/scorer configuration, fit scope, separation from model comparison.
4. Calibration and policy selection, including POLICY_VALIDATION reuse/adaptive-selection risk and selection-bias controls.
5. Exact-tier behavior and whether it is a common workflow scope or part of model comparison.
6. Minimum entity/profile/pair support per role and sparse-platform handling.
7. Cost coefficients and REVIEW semantics, provenance, sensitivity plan, primary objective.
8. Uncertainty estimation, multiplicity/comparison plan, outer split/seed schedule, reporting estimand.
9. Historical TEST-label exposure and a fresh sealed-label boundary for future final evaluation.
10. Final configuration, package/environment identity, and execution controls.

See `gate_09/PROTOCOL_OPEN_DECISIONS.md`; this candidate does not silently close any item.

## 6. Evidence and execution status

Sixty-one tests ran and passed in the locked Python 3.11 environment (Gate 4: 10; Gate 5: 10 including 2 real-data checks; Gate 6: 17; Gate 7: 24 including 5 byte-lifecycle tests). The cross-gate fixture uses synthetic labels/vectors; real snapshot/artifact checks are separate and read-only. `pytest` was unavailable and not installed. No model training, optimizer, new TEST-label evaluation, or Phase 2 experiment occurred.

Local project dependency files used to provision the temporary locked environment are untracked in primary; formal approval is NOT VERIFIED. Candidate files remain uncommitted in `/Users/thawaree.kha/research-phase15-integration`, branch `research/phase15-integration-review`, base SHA `1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b`.

## 7. Freeze and authorization fields

- Scientific owner decision: ______________________________
- Authorized approver and role: ______________________________
- Decision record ID and date: ______________________________
- Gate 8 data-use/ethics records reviewed: ______________________________
- Open decisions resolved / explicit exclusions: ______________________________
- Frozen protocol version/hash: ______________________________
- Execution authorization (separate explicit decision): **NOT GRANTED**

Historical preflight evidence records seven unauthorized/failed pre-final label-access attempts and one final read; the `PRE-FINAL TEST-LABEL READS` field is ambiguous against implementation counters distinguishing denied attempts from successful reads. Historical TEST-label exposure is NOT VERIFIED until source/log reconciliation; no inference of seven successful reads or zero successful reads is warranted.

Until an authorized owner completes and signs this record, Gate 9 remains NOT FROZEN and Phase 2 remains NO-GO.
