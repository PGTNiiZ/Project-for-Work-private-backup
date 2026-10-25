"""End-to-end adapter run on SYNTHETIC records only (no real profiles)."""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]

SYNTH = pd.DataFrame([  # SYNTHETIC — invented names
    ("github:1", "github", "e1", "zorblax", "Zor Blax", "builds tiny robots", "https://zorblax.example", "", "Nowhere"),
    ("bluesky:1", "bluesky", "e1", "zorblax", "Zor Blax", "tiny robots builder", "https://zorblax.example", "", ""),
    ("github:2", "github", "e2", "quimtrel", "Quim Trel", "coffee and maps", "", "", "Testville"),
    ("bluesky:2", "bluesky", "e2", "quimtrel_maps", "Quim Trel", "maps, coffee", "", "", ""),
    ("github:3", "github", "e3", "vandoplix", "Vando Plix", "", "https://vando.example", "", ""),
    ("bluesky:3", "bluesky", "e3", "pv_other", "Someone Else", "", "https://vando.example", "", ""),
], columns=["record_id", "source", "entity_id", "username", "full_name", "bio", "external_url",
            "profile_pic_url", "location"])


@pytest.mark.parametrize("method", ["B3", "B1"])
@pytest.mark.parametrize("drop", [True, False])
def test_adapter_runs_and_respects_drop_external_url(tmp_path, method, drop):
    rec = tmp_path / "records.csv"
    SYNTH.to_csv(rec, index=False)
    out = tmp_path / "scores.csv"
    cmd = [sys.executable, "-m", "adapter.run_v2r1", "--records", str(rec), "--left", "github",
           "--right", "bluesky", "--seed", "101", "--method", method, "--out", str(out)]
    if drop:
        cmd.append("--drop-external-url")
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-2000:]
    s = pd.read_csv(out, dtype=str)
    assert set(s.columns) >= {"left_id", "right_id", "score", "decision", "pair_type"}
    assert s.left_id.str.startswith("github:").all() and s.right_id.str.startswith("bluesky:").all()
    assert set(s.decision) <= {"MATCH", "REVIEW", "NO_MATCH"}
    exact = s[s.pair_type == "AUTO_EXACT"]
    # identical username → exact tier MATCH in both conditions
    assert ((exact.left_id == "github:1") & (exact.right_id == "bluesky:1")).any()
    url_only = (exact.left_id == "github:3") & (exact.right_id == "bluesky:3")
    assert url_only.any() != drop  # external-URL exact tier only exists WITH url (leakage ceiling)
    meta = json.loads(out.with_suffix(".meta.json").read_text())
    assert meta["condition"].startswith("PRIMARY") == drop
