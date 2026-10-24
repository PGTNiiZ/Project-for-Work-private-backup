"""Integrity-repaired verification rerun (v2r1) of the authoritative v2 experiment.

v2   = pre-integrity-repair authoritative run (historical, preserved).
v2r1 = integrity-repaired verification rerun using the identical frozen
       scientific design (features, models, sampling, calibration, splits,
       policies, bounds, budgets, seeds, metrics).

Repairs are limited to implementation-integrity guarantees:
1. sealed-test label VALUES are never materialized before FINAL_EVALUATION
   (label-free preflight validation + process-wide runtime guard);
2. sealed-test predictions are cryptographically hashed/frozen BEFORE any
   label access, and immutability is re-verified after evaluation.
"""
