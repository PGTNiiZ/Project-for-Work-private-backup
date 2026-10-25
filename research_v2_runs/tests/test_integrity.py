"""SYNTHETIC integrity boundary tests; no project profile inputs."""
from pathlib import Path
import importlib.util
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def load_integrity():
    if importlib.util.find_spec('integrity') is None:
        pytest.fail('sealed evaluation integrity boundary is not implemented')
    import integrity
    return integrity

def test_test_resource_unavailable_without_final(tmp_path):
    m = load_integrity()
    resource = tmp_path/'sealed.json'
    resource.write_text('["SYNTHETIC"]')
    with pytest.raises(PermissionError):
        m.guarded_read(resource, final=False, config_id='SYNTHETIC', lock=None, access_log=tmp_path/'access.jsonl')
    assert not (tmp_path/'access.jsonl').exists()


def test_committed_final_authorization_is_single_use_and_tamper_evident(tmp_path):
    import subprocess
    import hashlib
    m = load_integrity()
    resource = tmp_path/'sealed.json'
    resource.write_text('["SYNTHETIC"]')
    doc = tmp_path/'FINAL_CONFIGS.md'
    doc.write_text('SYNTHETIC frozen configuration')
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    subprocess.run(['git','-C',str(tmp_path),'add','FINAL_CONFIGS.md'],check=True)
    subprocess.run(['git','-C',str(tmp_path),'-c','user.name=Synthetic fixture','-c','user.email=fixture@localhost','commit','-qm','SYNTHETIC lock'],check=True)
    lock={'root':str(tmp_path),'document':'FINAL_CONFIGS.md','document_sha256':hashlib.sha256(doc.read_bytes()).hexdigest(),'configs':{'SYNTHETIC':{'artifact_hashes':{}}},'resource_hashes':{'sealed.json':hashlib.sha256(resource.read_bytes()).hexdigest()}}
    log = tmp_path/'access.jsonl'
    assert m.guarded_read(resource,final=True,config_id='SYNTHETIC',lock=lock,access_log=log) == b'["SYNTHETIC"]'
    with pytest.raises(PermissionError):
        m.guarded_read(resource,final=True,config_id='SYNTHETIC',lock=lock,access_log=log)
    with pytest.raises(PermissionError):
        m.guarded_read(resource,final=True,config_id='UNDECLARED',lock=lock,access_log=log)
    doc.write_text('SYNTHETIC changed lock')
    with pytest.raises(PermissionError):
        m.guarded_read(resource,final=True,config_id='SYNTHETIC',lock=lock,access_log=log)
