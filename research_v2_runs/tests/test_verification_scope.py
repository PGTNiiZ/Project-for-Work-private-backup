"""SYNTHETIC commit-scope and technical-address classification."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify_run

def test_known_concurrent_commit_is_separate_from_owned_writes():
    assert hasattr(verify_run,'owned_commit_scope')
    records={'SYNTHETIC_foreign':['holdout_eval/synthetic.py'],'SYNTHETIC_owned':['research_v2_runs/synthetic.py']}
    assert verify_run.owned_commit_scope(records,{'SYNTHETIC_foreign'})['owned_outside_count']==0
    records['SYNTHETIC_unapproved']=['outside_synthetic.py']
    assert verify_run.owned_commit_scope(records,{'SYNTHETIC_foreign'})['owned_outside_count']==1

def test_only_known_software_service_address_is_nonprofile_candidate():
    assert hasattr(verify_run,'technical_service_email')
    assert verify_run.technical_service_email('noreply@anthropic.com')
    assert not verify_run.technical_service_email('SYNTHETIC_contact@invalid.example')
