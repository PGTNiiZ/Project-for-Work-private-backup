# Gate 7 — cache validation specification

A cache candidate is rejected unless the run compatibility key matches exactly on all fields: dataset identity/hash, schema/feature identity, pair-population identity, chunk size, model/calibrator identity, source/config identity, and entity split manifest identity. A mismatch is a cache miss; never warn-and-continue.

Chunks declare a zero-based unique index, exact half-open `[start, stop)` pair-row interval, expected row count and canonical pair keys. Acceptance requires contiguous ordered coverage of `[0, pair_count)`, exact expected number of chunks (including the short final chunk), no gaps/overlap, correct row count, no duplicate canonical pair keys within/across chunks, and keys disjoint from other tiers where applicable. Validate all chunks before publishing/using the aggregate.

A partial or failed run is never a complete cache. The current contract does not permit resume; restart fresh. Existing production score loaders and historical caches are not compatible merely because filenames/row counts match. Do not import historical probabilities without explicit approved lineage and exact key/model/schema validation.

Tests in `tests/test_run_manifest.py` use synthetic chunks and temporary directories. They verify deterministic serialization, create-only writes, invalidation after each individual compatibility-key change, chunk gaps/overlaps, duplicate chunk and pair keys, missing chunks, incorrect counts, and a valid short final chunk.
