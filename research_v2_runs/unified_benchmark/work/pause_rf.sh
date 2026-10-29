#!/bin/bash
cd "$(dirname "$0")/.."
until [ "$(grep -c 'fold 1 done' work/job-J_sparse_FLEX35_RF.log)" -ge 1 ]; do sleep 20; done
kill -STOP 76625 && echo "{\"event\":\"PAUSED\",\"job\":\"J_sparse_FLEX35_RF\",\"pid\":76625,\"after\":\"fold 1 done\",\"utc\":\"$(date -u +%FT%TZ)\"}" >> ledger/runs.jsonl
