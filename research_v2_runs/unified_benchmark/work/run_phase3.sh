#!/bin/zsh
# Phase 3 (after report v1): rows for the deferred learners. Frozen plan unchanged.
cd "$(dirname $0)/.."
export OMP_NUM_THREADS=2 UB_THREADS=2 PYTHONWARNINGS=ignore
PY=../.venv/bin/python
for r in L1_model_ExtraTrees L1_model_AdaBoost; do $PY harness.py row $r >> work/row-$r.log 2>&1; echo "[$(date +%H:%M:%S)] row-$r exit=$?" >> work/run_phase3.log; done
while kill -0 76625 2>/dev/null; do sleep 60; done
if [ -f metrics/job_J_sparse_FLEX35_RF.json ]; then $PY harness.py row L1_model_RF >> work/row-L1_model_RF.log 2>&1; echo "[$(date +%H:%M:%S)] row-L1_model_RF exit=$?" >> work/run_phase3.log; else echo "[$(date +%H:%M:%S)] RF job ended without output" >> work/run_phase3.log; fi
echo "PHASE3 DONE" >> work/run_phase3.log
