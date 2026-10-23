# Feature 18 lineage: `bert_cos`

## Evidence-backed chain

- Schema declaration: `FEATURE18_COLUMNS = FEATURE17_COLUMNS + ["bert_cos"]` in authoritative `features.py`; thus GB-18 adds one scalar column to corrected GB-17.
- Phase 1 `dataset_candidate_accounting.json` records existing embedding artifact `experiments/profile_embeddings_minilm.npy` (36,807 × 384) and ID array (36,807 IDs, no duplicates). Vector norms are reported within 0.9999998212–1.0000001192. Three IDs are outside the eligible population; all eligible endpoints have embeddings.
- Phase 1 records legacy `experiments/pair_bert_cos.parquet`: 2,073,842 rows, no missing embedding endpoints, replay mismatch 0 / maximum difference 0. The authoritative-v2 `features/bert_cos.parquet` has 2,073,842 rows, no missing endpoints, cosine out-of-range 0, and max absolute difference 6.556510925292969e-7 versus replay from the existing legacy embeddings.
- Phase 1 narrative describes intended text composition as `fullName + space + bio + space + location`, stripped, empty mapped to `[empty]`, encoded to normalized vectors, then dot product. It cites historical `experiments/code/exp_r2_bert_feature.py` and v2 runner source. This is documented lineage, not newly replayed here.

## Unresolved / must not infer

The embedding filenames, vector dimensionality and cosine agreement do not establish exact model repository revision/commit, weight hash, tokenizer revision/version, library versions, historical preprocessing implementation, encoding batch/options, or producer chronology. Do not invent a MiniLM revision or claim full encoder reproducibility. Phase 1 explicitly says encoder provenance is incomplete. The similarity column is a scalar cosine feature; it is not 384 feature columns. Regeneration would require a separately frozen and recorded encoder/tokenization/input contract.

This Gate did not open the embedding or pair-feature caches and did not inspect labels. Existing cache checks above are reported Phase 1 evidence only, not reproduced by Gate 4.
