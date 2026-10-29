"""SYNTHETIC failure-ledger acceptance test."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_failed_run_appends_sanitized_terminal_record(tmp_path):
    if importlib.util.find_spec('runtime') is None:
        pytest.fail('append-only failure ledger missing')
    from runtime import append_event,terminal_record
    log=tmp_path/'runs.jsonl'
    start={'run_id':'SYNTHETIC','exp_id':'D0-2','status':'STARTED'}
    append_event(log,start)
    end=terminal_record(start,status='FAILED',error=ValueError('SYNTHETIC hidden value'))
    append_event(log,end)
    entries=[json.loads(x) for x in log.read_text().splitlines()]
    assert len(entries)==2 and entries[-1]['status']=='FAILED'
    assert entries[-1]['exception_type']=='ValueError'
    assert 'hidden value' not in log.read_text()


def test_post_final_retuning_is_rejected_but_aggregate_reporting_is_allowed(tmp_path):
    import runtime
    assert hasattr(runtime,'deny_post_test_tuning'), 'post-final retuning boundary missing'
    log=tmp_path/'ledger/test_access.jsonl'
    log.parent.mkdir()
    log.write_text('{"event":"AUTHORIZED_FINAL_OPEN"}\n')
    with pytest.raises(PermissionError):
        runtime.deny_post_test_tuning(tmp_path,'hyperparameter_search')
    with pytest.raises(PermissionError):
        runtime.deny_post_test_tuning(tmp_path,'policy_optimization')
    runtime.deny_post_test_tuning(tmp_path,'aggregate_statistics')


def test_existing_run_key_cannot_overwrite_past_results(tmp_path):
    import runtime
    assert hasattr(runtime,'assert_unused_run_key'), 'immutable run-key guard missing'
    log=tmp_path/'runs.jsonl'
    log.write_text('{"run_id":"SYNTHETIC","status":"DONE"}\n')
    before=log.read_bytes()
    with pytest.raises(FileExistsError):
        runtime.assert_unused_run_key(log,'SYNTHETIC')
    assert log.read_bytes()==before
    runtime.assert_unused_run_key(log,'SYNTHETIC_RETRY1')
