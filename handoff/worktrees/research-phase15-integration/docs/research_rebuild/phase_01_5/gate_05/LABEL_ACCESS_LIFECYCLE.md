# Gate 5 — TEST label-access lifecycle

1. The split builder emits an entity role manifest and pair-key routing/aggregate counts without exposing outcome columns to candidate generation or feature extraction.
2. TRAIN labels are available to the scorer fit and calibration labels to the calibrator fit only; POLICY_VALIDATION labels are exposed only to predeclared development selection functions.
3. TEST label records are stored separately from development frames. Model, calibrator, selected policies, configuration, source and label-free pair-keyed predictions are frozen and hashed before final evaluation.
4. A narrow final evaluator accepts the frozen prediction manifest, validates one-to-one canonical pair keys and reads TEST labels in an explicit FINAL_EVALUATION phase only. Every allowed/denied request is audited; a prior read attempt invalidates the evaluation. No label column is serialized into candidate/features/prediction artifacts.
5. Independently recompute aggregates from keyed decision rows and reconcile all-positive, exact, scored, miss and REVIEW accounting.

The in-memory lifecycle test in `tests/test_gate05_split_safety.py` is only a synthetic example; it is not integrated with the project's file-backed `SealedLabels`/`LazySealedLabelStore` adapters. Programmatic phase guards do not prevent the same operator from reading local files or memory. Independent access control, credential separation and custodian-blinded evaluation would be needed for a stronger security claim. The explored historical corpus cannot become an external holdout by renaming the role TEST.
