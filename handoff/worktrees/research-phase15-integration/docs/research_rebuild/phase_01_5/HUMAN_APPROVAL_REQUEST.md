# Phase 1.5 — Human Approval and Scientific Decision Request

No approval is granted by this document. Gate 8 remains PENDING HUMAN APPROVAL; Gate 9 remains NOT FROZEN; Phase 2 remains NO-GO.

For each item, provide an authoritative decision record, responsible owner/role, date, version/hash and explicit scope. If an approval exists but its record is unavailable, mark it researcher-reported / documentary evidence NOT VERIFIED; do not treat this request as revocation.

## A. Dataset snapshot and exclusions (Gate 1)

- Confirm canonical source and exact normalized snapshot path/version/hash. V2 provenance names candidate `data_for_project/normalized_profiles_with_profile_id.csv`, SHA-256 `17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1`, 36,807 rows; it is not approved by this audit. Related upstream `merged_profiles.csv` is a distinct file/hash and must not be conflated.
- Approve eligibility/exclusions, including the 3 rows with missing `user_folder`, and any platform/profile filters; confirm counts and hash after disposition.
- State retention, access, and permitted use period.

## B. Entity mapping conflicts (Gate 2)

- Decide canonical entity key, duplicate/conflict rules, and disposition for ambiguous mappings. Candidate audit finds 121 rows participating in duplicate `(platform,userName)` values; this is a conflict-review signal, not an automatic data error.
- Provide signed mapping/conflict manifest and hash; do not infer identity from usernames alone.

## C. Ground-truth label authority (Gate 3)

- Identify label source/owner and authority, positive/negative definitions, adjudication method, known uncertainty, and allowable use.
- Confirm whether same-platform positives belong in the scientific denominator or are excluded; identify the approved cross-platform estimand.
- Provide signed assumptions and version/hash.

## D. Data-use/reuse rights (Gate 8)

- Data owner/legal contact: document source license, platform/API terms, reuse/derivative rights, consent or lawful secondary-use basis, redistribution constraints, and any restrictions on derived embeddings/features.
- No publication or external release of rows, embeddings, usernames, profiles, or linkable pair data is authorized by the technical candidate.

## E. Privacy and publication restrictions (Gate 8)

- Approve minimization, access controls, retention/deletion, pseudonymization, risk review, and allowed public artifacts (code/config/hashes/aggregates only unless specifically approved).
- Specify disclosure review and restrictions on tables, failure examples, and supplementary files.

## F. Ethics / IRB (Gate 8)

- Provide institutional ethics/IRB approval with protocol ID and scope, or a written determination of exemption/not-human-subjects status from the authorized institutional office. Researcher/agent self-assessment is insufficient.

## G. Scientific Protocol A–F sign-off (Gate 9)

Review `MASTER_PROTOCOL_FREEZE_CANDIDATE.md`, `gate_09/EXPERIMENT_CONFIG_V1.json`, and `gate_09/PROTOCOL_OPEN_DECISIONS.md`. Record decisions for:

1. Snapshot, exclusions, entity/label assumptions, and historical TEST-label exposure.
2. Five-fold assignment seed 20261010, stratification signature, role rotation, minimum support, and label-access boundary.
3. C0/C1 retrieval: top-k {10,20,50}, primary 20, candidate/target-platform scope; whether C1 scorer is refit and how retrieval effects are isolated.
4. New arms E1=LR-17, E2=GB-17, E3=GB-18; preserve historical E2/E3 aliases as unresolved. The future-only Feature18 contract is pinned in `gate_04/FEATURE18_CONTRACT_V1.json`; decide whether to adopt it for A–F. Historical embedding-to-model/text lineage remains NOT VERIFIED and is not retroactively certified by this contract.
5. Calibration choices (isotonic/sigmoid), selection metric/role and adaptive POLICY_VALIDATION reuse; define selection-bias controls.
6. P0–P5 definitions and exact-tier treatment; cost matrix/scenarios, REVIEW semantics, objective and rationale.
7. Five optimizer seeds (101,202,303,404,505), 2,048 objective calls per method/seed/fold/scenario and checkpoints (128,512,2048); confirm search-space comparability and total planned budget (1,382,400 calls), not executed.
8. Primary contrast, estimand, paired statistical unit, uncertainty method/replicates/confidence level, multiplicity, practical margin, per-fold reporting and compute/storage ceilings.
9. Historical TEST-label exposure: V2 preflight records seven failed unauthorized access attempts, one final read, and an ambiguously named `PRE-FINAL TEST-LABEL READS: 7` field. Reconcile raw audit evidence and implementation counters before claiming the number of successful reads.
10. Retrospective reanalysis limitations and prohibited external/generalization claims.

## Record fields (to be completed by authorized owners)

- Dataset owner / snapshot decision ID / date / hash: ____________________
- Entity mapping decision ID / date / hash: ____________________
- Label authority decision ID / date / hash: ____________________
- Data-use/reuse approval ID / owner / scope: ____________________
- Privacy/publication decision ID / date: ____________________
- Ethics/IRB approval or exemption ID / issuing office: ____________________
- Scientific owner / A–F decision record ID / protocol version and hash: ____________________
- Separate execution authorization (must be explicit; not implied by protocol approval): ____________________

Until those records are reviewed, this package is a technical closure candidate only; it does not authorize training, optimization, TEST evaluation or Phase 2.
