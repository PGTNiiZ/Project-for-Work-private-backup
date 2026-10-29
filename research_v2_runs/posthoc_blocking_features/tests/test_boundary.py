"""SYNTHETIC dev-only access boundary."""
from pathlib import Path
import importlib.util
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_locked_fold_is_rejected_before_io():
    spec=importlib.util.find_spec('common')
    assert spec is not None,'dev-only module missing'
    import common
    for fold in [-1,4,5,'4',None]:
        with pytest.raises(PermissionError): common.load_fold(fold)
