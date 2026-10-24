# Gate 7 — run artifact contract

A run is a unique immutable directory `artifacts/experiments/rebuild_v1/<run_id>/`. Create-only semantics: refuse any existing path; never overwrite or glob across runs. The manifest is canonical JSON (UTF-8, sorted keys, compact separators, no NaN/Infinity) with SHA-256 over its exact bytes. The run ID derives deterministically from canonical compatibility fields and declared pair count.

Required compatibility identities: dataset/input hash; input/schema version; candidate pair-population identity; exact chunk size; model/scorer/calibrator identity; source revision/code/config identity; entity split manifest hash. A cache is reusable only when all fields match exactly. File paths alone are not identities. Include exact environment/lockfile identity and feature schema ID in the extended artifact inventory.

Each run records run state (CREATED/RUNNING/COMPLETE/FAILED), expected pair/chunk counts, immutable artifact hashes, configuration, split hash, feature schema, model/calibrator, optimizer seed/cost scenario where applicable, and parent/source lineage. Only a fully validated COMPLETE run can be reported. Partial outputs remain partial and cannot be silently included in result tables.

Resume is unsupported by this contract. Restart under a new run ID; any future resume implementation needs a separately reviewed atomic chunk protocol. No historical scores/cache are silently reused.
