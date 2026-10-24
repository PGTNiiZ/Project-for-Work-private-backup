# Gate 8 — Privacy and Publication Policy (Draft)

**Status: DRAFT — PENDING HUMAN APPROVAL.** This is a conservative publication boundary, not a legal determination or authorization to process or publish data.

## 1. Scope and default

Applies to research rebuild records, data extracts, intermediate artifacts, model outputs, reports, notebooks, figures, code packages, and supplementary materials. Until documented rights, applicable ethics/privacy review, and explicit owner approval are established, do not expand data access or run new scientific experiments. Do not contact source platforms/individuals or upload, transfer, or submit data to external services as part of this draft.

## 2. Prohibited public or external release by default

Do not include or transmit:

- raw or transformed profile rows containing names, usernames, biographies, location, URLs, platform account details, or other personal/profile text;
- images, image URLs, captions, embeddings, or image-derived records;
- raw or hashed entity/profile identifiers, pair keys, linkable pseudonyms, or mappings;
- pair-level features, labels, scores, predictions, decisions, review outcomes, error rows, or examples derived from identifiable profiles;
- small-cell or otherwise identifying aggregates, reconstructed examples, or workbook/notebook excerpts that expose such content.

Hashing, normalization, aggregation, public upstream availability, or inclusion in a prior artifact does not by itself make material anonymous or authorized for release.

## 3. Conditional candidate outputs

Code, configuration, environment/package metadata, non-identifying manifests and hashes, aggregate metrics, and broad aggregate error categories may be considered only after (a) applicable code/data rights review, (b) privacy/disclosure review for re-identification and differencing risks, and (c) explicit owner and institutional approval. Apply suppression or coarsening where needed; do not publish counts or slices that expose individuals or enable linkage. This paragraph is not approval to publish any particular artifact.

## 4. Access, storage, retention, and security decisions

Before any approved analysis, the data owner and institutional authority must specify authorized personnel, approved storage and compute environment, access controls, purpose limitation, retention period, deletion procedure, incident escalation, and whether external services are prohibited. These decisions are currently **NOT VERIFIED** in the inspected repository. This draft does not authorize changing storage, copying data, or retaining new derivatives.

## 5. Review and release workflow

1. Identify exact source snapshots and artifacts, with hashes/schema and provenance where available, without exposing raw records in the review package.
2. Obtain documentary evidence covering the proposed purpose and operations; have qualified legal/privacy and ethics authorities determine applicable requirements. Do not infer consent, ToS compliance, license, IRB status, or data-use authorization.
3. Obtain written data-owner and research-lead approval for the specific analysis, environment, users, retention, and outputs. Resolve any institutional review requirement before execution.
4. Review every output for raw fields, direct/linkable identifiers, pair-level leakage, small-cell disclosure, and third-party license obligations. Keep review artifacts non-identifying.
5. Record the reviewer, date, scope, conditions, and final decision. Any change in source, purpose, recipients, method, or output requires renewed review.

Until steps above are documented, disposition is **PENDING HUMAN APPROVAL** and public release is blocked. Preserve no-raw-publication safeguards regardless of whether code or aggregate research findings are later approved for release.
