# Gate 07 — deterministic run isolation and cache contract

## Scope and source observations

This gate defines run identity, immutable outputs, and safe reuse; it does not launch a model or modify any project artifact/cache. The existing `exp_lib.build_cache(force=False)` trusts one fixed parquet path if it exists, and `force=True` writes there (`exp_lib.py:72-104`). That is not a compatibility check and is overwrite-prone. The shared experiment protocol uses entity-aware splits and drops cross-role pairs (`experiments/walkthroughs/00_shared_protocol/00_shared_protocol.ipynb`). The chunked feature implementation uses explicit `[pair_start, pair_stop)` ranges and advances by `chunk_size` (`train_data/stage9_features_pipeline_chunked.py:530-556`); a run must therefore record exact chunk boundaries and prove coverage, not merely count completed files.

## Manifest

`run_manifest.py` defines a single v1 contract shared by schema validation, writer, reader and cache validator. Canonical JSON uses UTF-8, sorted keys, compact separators, no NaN/Infinity. The manifest contains `manifest_schema`, `compatibility`, `pair_count`, deterministic `run_id`, `state`, and `artifacts`. The compatibility key requires dataset hash, ordered feature/schema identity, pair-population identity, chunk size, model identity, source identity, entity-split identity, configuration identity, environment/lock identity, and explicit seed. These are caller-supplied opaque identities; paths alone are insufficient. `CREATED`/`RUNNING`/`FAILED` cannot be accepted as a cache. `COMPLETE` is produced only by `finalize_manifest` after exact chunk coverage and artifact metadata validation. Writers are create-only (`O_EXCL`); readers fail closed on schema or run-ID mismatch.

## Cache and chunk acceptance

A cache is reusable only when every compatibility field compares exactly, the manifest state is COMPLETE, its artifacts match the chunk descriptors, and flattened canonical pair keys equal the expected keys in order. A single mismatch is a cache miss. Each chunk declares a unique index, exact half-open row interval, nonempty canonical pair keys, artifact path, and SHA-256 metadata; validation requires contiguous coverage from zero through the declared population, no gaps/overlaps/duplicates, and the expected short final chunk. `validate_cache` rejects stale populations and artifact-list drift. Manifest validation checks metadata only: this candidate does not read historical cache files or verify artifact bytes on disk.

An interrupted run is **partial**, never a valid complete cache. It may retain immutable chunk outputs under that run's unique directory; restart uses only explicitly validated chunks with the same complete compatibility key and cannot silently mix runs. No resume is authorized by this gate: default stance is restart from scratch under a fresh run ID. A future resume feature requires a separate reviewed protocol and atomic per-chunk completion metadata. Do not write into existing run directories or touch real artifacts/caches during preflight/tests.

## Verification

Run `python3.11 -m unittest discover -s docs/research_rebuild/phase_01_5/gate_07/tests -v`. Tests are synthetic, use temporary directories only, and do not invoke models or read scientific artifacts.
