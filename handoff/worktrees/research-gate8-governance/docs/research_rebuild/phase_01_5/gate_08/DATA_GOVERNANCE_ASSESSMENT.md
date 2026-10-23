# Gate 8 — Data Governance Assessment

**Decision: PENDING HUMAN APPROVAL. Scientific execution is BLOCKED pending documentary authorization and explicit owner approval.** This is an assessment of repository evidence, not legal advice or an ethics determination.

## Verified repository facts

- The governance note for authoritative run v2 describes the local input as a transformed derivative of the public LinkSocial `Dataset-LinkSocial` repository. It reports attribution and counts in that repository's README, but does not establish a machine-readable reuse license or redistribution permission (`experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md:3–5`).
- That note explicitly says public hosting is not treated as permission to redistribute personal data and excludes raw profiles, direct/linkable identifiers, and pair-level feature/prediction/decision/error rows from release absent authorization (`.../DATA_GOVERNANCE.md:7–14`).
- The Phase 1 limitations assessment reports that raw provenance, platform Terms-of-Service compliance, consent/notification, and ethics/IRB documentation were not verified; it says governance NOT VERIFIED blocks public raw/pair-row release and authorization claims (`docs/research_rebuild/phase_01/05_DATA_AND_EXPERIMENT_LIMITATIONS.md:68–74`).
- The Phase 1 readiness gate marks data-governance limitations NOT VERIFIED and says internal scientific runs require owner confirmation of rights and explicit authorization (`docs/research_rebuild/phase_01/06_PHASE_1_READINESS_GATE.md:22–24,38–41`).
- Phase 1 inventory records multiple transformed snapshots and missing raw/ground-truth artifacts; these are repository lineage findings, not proof of collection authority (`docs/research_rebuild/phase_01/01_DATASET_AND_FEATURE_LINEAGE.md:13–33,202–208`).

## Not established by repository evidence

No documentary evidence was verified here for: applicable license terms; permission to use, modify, or redistribute the source or derivatives; platform ToS compliance at collection/use; consent, notice, or other valid basis; collection methodology and provenance; data-use agreement; ethics committee/IRB determination or approval; institutional authorization; or rights in images/embeddings. Absence of evidence in the inspected repository is not a finding that authorization is impossible or that a violation occurred.

## Decisions required from humans

The data owner and institutional research lead must identify the authoritative source/version, permitted purpose, authorized users and environment, retention/deletion terms, and whether proposed retrospective analysis is within scope. Qualified legal/privacy and ethics authorities must determine applicable rights, ToS, privacy, and review requirements. The authorized decision-maker must document an explicit go/no-go for scientific execution. Do not infer any of these decisions from public availability, hashes, attribution, prior use, or successful code execution.

## Controls pending approval

- Status remains **PENDING HUMAN APPROVAL** until documentary authorization and explicit approval are recorded.
- No data contact, transfer, upload, external service use, new model/scientific execution, or publication is authorized by this assessment.
- Preserve no-raw-publication safeguards: exclude raw/profile text, usernames, bios, locations, URLs/images, linkable IDs, pair rows, and row-level features/predictions/decisions/errors from public outputs unless a separate documented review expressly authorizes a narrowly defined release.
- Until clearance, limit documentation to non-identifying repository facts and avoid claims of consent, license, ToS compliance, IRB, or data-use authorization.
