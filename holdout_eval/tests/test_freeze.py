import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run_freeze(repo: Path, tmp: Path):
    f = tmp / "model.bin"
    f.write_bytes(b"synthetic")
    return subprocess.run([sys.executable, "-m", "common.freeze", "--repo", str(repo), "--files", str(f),
                           "--threshold", "0.5", "--decision-rule", "synthetic", "--out",
                           str(tmp / "m.json")], cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    for args in (["init", "-q"], ["config", "user.email", "t@example.invalid"], ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(r), *args], check=True)
    (r / "a.txt").write_text("x")
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-qm", "init"], check=True)
    return r


def test_freeze_fails_on_dirty_tree(repo, tmp_path):
    (repo / "untracked.txt").write_text("dirty")
    res = run_freeze(repo, tmp_path)
    assert res.returncode != 0
    assert not (tmp_path / "m.json").exists()


def test_freeze_succeeds_on_clean_tree(repo, tmp_path):
    res = run_freeze(repo, tmp_path)
    assert res.returncode == 0, res.stderr
    assert (tmp_path / "m.json").exists()
