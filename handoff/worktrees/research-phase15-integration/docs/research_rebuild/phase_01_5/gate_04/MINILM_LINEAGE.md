# Feature 18 lineage: `bert_cos`

## Evidence-backed chain

- Schema declaration: `FEATURE18_COLUMNS = FEATURE17_COLUMNS + ["bert_cos"]` in authoritative `features.py`; thus GB-18 adds one scalar column to corrected GB-17.
- Phase 1 `dataset_candidate_accounting.json` records existing embedding artifact `experiments/profile_embeddings_minilm.npy` (36,807 × 384) and ID array (36,807 IDs, no duplicates). Vector norms are reported within 0.9999998212–1.0000001192. Three IDs are outside the eligible population; all eligible endpoints have embeddings.
- Phase 1 records legacy `experiments/pair_bert_cos.parquet`: 2,073,842 rows, no missing embedding endpoints, replay mismatch 0 / maximum difference 0. The authoritative-v2 `features/bert_cos.parquet` has 2,073,842 rows, no missing endpoints, cosine out-of-range 0, and max absolute difference 6.556510925292969e-7 versus replay from the existing legacy embeddings.
- Phase 1 narrative describes intended text composition as `fullName + space + bio + space + location`, stripped, empty mapped to `[empty]`, encoded to normalized vectors, then dot product. It cites historical `experiments/code/exp_r2_bert_feature.py` and v2 runner source. This is documented lineage, not newly replayed here.

## Unresolved / must not infer

Historical artifact names, vector dimensions and cosine agreement do not establish which revision, weight/tokenizer hashes, library versions, preprocessing, or encoding options generated those embeddings. Do not infer the historical producer from a currently cached model. The similarity column is a scalar cosine feature; it is not 384 feature columns. The future contract is separately versioned and does not retroactively certify historical values.

The pre-integration worker report did not open the embedding or pair-feature caches or inspect labels. The Lead integration addendum below records the later read-only artifact audit.

## Lead integration implementation addendum — local artifacts vs historical lineage

Read-only local cache inspection found model `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; `model.safetensors` SHA-256 `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`; tokenizer bundle SHA-256 `78a3daa92dcec076e80baaa628a6553bcbd0b431a214eb02d72c8b5672e69e09`. The local model config confirms Transformer→mean-token Pooling→Normalize, 384 dimensions and max length 256. Persisted profile embedding IDs exactly match candidate snapshot `profile_row_id` order, and Feature17/`bert_cos` pair endpoint ordering matches for all 2,073,842 rows; 16 stored cosines match recomputed embedding dot products. Detailed byte hashes are in `../gate_05/REAL_SNAPSHOT_VERIFICATION.json`.

This verifies current local artifact identity and alignment only; it does not bind historical embedding bytes to this revision or prove their exact original input serialization. `FEATURE18_CONTRACT_V1.json` defines a future-only composition and pinned contract; no embedding generation or weight download/replacement occurred.
