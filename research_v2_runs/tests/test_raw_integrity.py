"""SYNTHETIC LFS integrity cases: tiny real content is not a pointer."""
from pathlib import Path
import hashlib
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify_run

def test_tiny_smudged_lfs_content_is_hashed_as_real_bytes(tmp_path):
    assert hasattr(verify_run,'working_lfs_hash'), 'tiny-LFS-content verifier missing'
    content=b'SYNTHETIC\n'*20
    path=tmp_path/'SYNTHETIC.csv'
    path.write_bytes(content)
    assert verify_run.working_lfs_hash(path)==hashlib.sha256(content).hexdigest()
    path.write_bytes(b'version https://git-lfs.github.com/spec/v1\noid sha256:'+b'0'*64+b'\nsize 200\n')
    assert verify_run.working_lfs_hash(path)=='0'*64
