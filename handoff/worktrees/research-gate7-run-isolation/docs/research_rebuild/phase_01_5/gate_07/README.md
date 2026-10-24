# Gate 07 — deterministic run isolation and cache contract

## Scope and source observations

This gate defines run identity, immutable outputs, and safe reuse; it does not launch a model or modify any project artifact/cache. The existing `exp_lib.build_cache(force=False)` trusts one fixed parquet path if it exists, and `force=True` writes there (`exp_lib.py:72-104`). That is not a compatibility check and is overwrite-prone. The shared experiment protocol uses entity-aware splits and drops cross-role pairs (`experiments/walkthroughs/00_shared_protocol/00_shared_protocol.ipynb`). The chunked feature implementation uses explicit `[pair_start, pair_stop)` ranges and advances by `chunk_size` (`train_data/stage9_features_pipeline_chunked.py:530-556`); a run must therefore record exact chunk boundaries and prove coverage, not merely count completed files.

## Manifest

`run_manifest.py` is a standalone, stdlib-only contract. Canonical JSON uses UTF-8, sorted keys, compact separators, no NaN/Infinity, and SHA-256 over those exact bytes. A manifest has schema version and run ID plus **all** compatibility dimensions: dataset identity, schema identity, pair-population identity, chunk size, model identity, source identity, and split identity. Identities are nonempty opaque strings/hashes supplied by the caller; do not derive them from mutable paths alone. Include input hashes/configuration in the corresponding identity upstream. Run IDs are deterministic from the compatibility key. Output publication is create-only (`O_EXCL`); an existing target is an error, never force-replaced.

## Cache and chunk acceptance

A cache can be reused only when every compatibility field compares exactly. A single-field mismatch is a cache miss, not a warning. Each chunk declares a unique nonnegative index and exact half-open row interval; validation requires contiguous indices/intervals from zero through the declared pair population, no overlap/gap, and expected row count per chunk (including the shorter final chunk). Duplicate chunk indices, duplicate pair keys within/across chunks, malformed or out-of-range rows, and count/coverage mismatches reject the cache. Validate the complete candidate before accepting it.

An interrupted run is **partial**, never a valid complete cache. It may retain immutable chunk outputs under that run's unique directory; restart uses only explicitly validated chunks with the same complete compatibility key and cannot silently mix runs. No resume is authorized by this gate: default stance is restart from scratch under a fresh run ID. A future resume feature requires a separate reviewed protocol and atomic per-chunk completion metadata. Do not write into existing run directories or touch real artifacts/caches during preflight/tests.

## Verification

Run `python3.11 -m unittest discover -s docs/research_rebuild/phase_01_5/gate_07/tests -v`. Tests are synthetic, use temporary directories only, and do not invoke models or read scientific artifacts.
