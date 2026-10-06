# ICSEC 2026 authoritative v2 final pre-execution gate

Status: engineering inputs wired and verified. No final seed, final model, scientific metric, sealed result, manuscript, or historical authoritative artifact was executed or modified.

## Input architecture

Development labels are produced per seed at `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_{101,202,303}/development_labels/labels.parquet`. They contain only `pair_key`, `actual`, and `role`, with roles restricted to TRAIN, CALIBRATION, and POLICY_VALIDATION. The runner filters the common artifact through explicit role-specific interfaces and rejects foreign role labels.

Physically separate sealed artifacts are at `scientific_inputs/outer_{seed}/sealed_test_labels/labels.parquet`. They contain only safe canonical pair keys and `actual` for SEALED_TEST same-role candidate pairs. `LazySealedLabelStore` is the sole real-file reader and permits reads only in FINAL_EVALUATION. Pre-final denial occurs before file open.

Global blocking misses are reproduced from the authoritative profile input and global candidate universe at `scientific_inputs/outer_{seed}/blocking_misses/positive_pairs.parquet`; same-role routes are stored separately in `same_role_routes.parquet`. They use only safe keys and `BLOCKING_MISS`. Workflow evaluation appends these as positive NO_MATCH rows only after scored-candidate predictions; they are never classifier inputs.

## Verified global scope

The regenerated producer fail-closed against: 36,804 eligible profiles; 29,247 all-platform positives; 29,243 cross-platform positives; 4 same-platform positives; 449,149,239 possible cross-platform pairs; 12,403 exact-tier pairs; 2,073,842 model-scored pairs; 2,086,245 workflow candidates; 25,931 covered positives; 3,312 blocking misses; 88.6742% retrieval recall; and 99.5355% candidate-space reduction.

## Per-seed products

Seed 101: development 548,490 rows; sealed 193,692 rows.
Seed 202: development 565,651 rows; sealed 197,531 rows.
Seed 303: development 538,735 rows; sealed 203,731 rows.

Each `input_artifact_manifest.json` captures authoritative-source and producer SHA-256, split-manifest SHA-256, output paths/hashes/row counts/scopes, environment, blocking invariant, and disjointness. `scientific_inputs/frozen_protocol_hashes.json` locks all six frozen protocols.

## Access and scope boundaries

TRAIN may consume TRAIN labels only; CALIBRATION may consume CALIBRATION labels only; POLICY_VALIDATION may consume POLICY_VALIDATION labels only. SEALED_TEST labels are inaccessible until FINAL_EVALUATION. Development/sealed pair intersection is asserted empty and real router role assignments assert entity disjointness. Decision outputs declare EXACT_TIER, MODEL_SCORED, or WORKFLOW; workflow rows include blocking misses, and independently recomputed workflow metrics use the workflow artifact.

## Frozen configurations and command

B0 remains fixed. B1 remains simple-policy Sobol selection. B2 remains four-parameter Sobol at 12,000 objective evaluations. B3 remains the same four-parameter seeded GA at 12,000 realized objective evaluations. Protocol hashes are frozen.

Future scientific command:

`uv run python3.11 experiments/code/run_icsec_authoritative_v2.py --mode scientific-final --outer-seeds 101 202 303 --authorize-final-scientific-run`

The command is fail-closed without `--authorize-final-scientific-run`; an un-authorized invocation was verified to terminate before execution. Before authorized execution it validates protocol locks, real label artifacts and hashes, label-free public artifacts, all required seeds, and the 12,000 B2/B3 budget.

## Tests

Targeted v2, producer, adapter, and final-runner suite: 38 passed.
Full repository suite: 83 passed.

Remaining blockers: none for engineering wiring. Dataset-license, redistribution, and ethics questions recorded in DATA_GOVERNANCE.md remain research-governance limitations, not a runner-input blocker.
