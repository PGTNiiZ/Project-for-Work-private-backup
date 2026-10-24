# authoritative_run_v2 execution protocol

This directory contains the frozen repair implementation and pre-execution protocol. Do not run the scientific outer seeds until all preflight checks pass. Never write to `experiments/icsec_final/authoritative_run/`.

1. Hash the raw/transformed input snapshot and code/configuration before loading labels.
2. Rebuild candidate and exact/blocking-miss pair-key manifests from the normalized input. No predecessor `match_decisions` artifact is an input.
3. Regenerate corrected handcrafted features. The affected v1 caches `experiments/scored_pairs_enriched.parquet` and `experiments/pair_features17.parquet` are invalid for v2. Regenerate `pair_bert_cos` unless its keys, profile hash, and pinned MiniLM revision are independently verified; default is regenerate.
4. Keep labels in a separate sealed input. Public pair/features frames must omit `actual`, `label`, `ground_truth`, and entity identifiers.
5. Assign entity-disjoint TRAIN, CALIBRATION, POLICY_VALIDATION, and SEALED_TEST roles. Verify zero overlap before fitting.
6. Fit GB and calibration only on TRAIN and CALIBRATION. Produce frozen probabilities without opening sealed labels.
7. Select B1/B2/B3 only on POLICY_VALIDATION labels. B0 is fixed. Record objective evaluations and optimizer metadata. Ties retain the first candidate in deterministic generation order; GA trial ties use the smallest seed.
8. Freeze all artifacts and configurations. Only then open sealed labels in the final evaluator and join by pair key.
9. Independently recompute decisions/metrics from row-level outputs, then capture the final SHA-256 manifest.

Required seeds: 101, 202, 303. Required pre-final invariant: `PRE-FINAL TEST LABEL READS = 0`. Dry-run output, if created, must be under `dry_run/` and marked `NOT MANUSCRIPT EVIDENCE`.
