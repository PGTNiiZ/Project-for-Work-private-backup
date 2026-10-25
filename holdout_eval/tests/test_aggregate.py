import numpy as np
import pandas as pd
import pytest

from common.aggregate import block, joint_bootstrap, seed_stats

GOLD = {("l1", "r1"), ("l2", "r2"), ("l3", "r3")}
LEFT = ["l1", "l2", "l3", "l4"]


def scores(decisions):
    return pd.DataFrame({"left_id": ["l1", "l2", "l4"], "right_id": ["r1", "r2", "r7"],
                         "score": [0.99, 0.8, 0.7], "decision": decisions})


def test_mean_over_seeds_and_blocked_gold_is_fn():
    per = {101: seed_stats(scores(["MATCH", "MATCH", "NO_MATCH"]), GOLD, LEFT)["match"],
           202: seed_stats(scores(["MATCH", "REVIEW", "NO_MATCH"]), GOLD, LEFT)["match"]}
    out = block(per, n_boot=50, boot_seed=1)
    # seed 101: tp2 fp0 fn1 → F1 0.8 ; seed 202: tp1 fp0 fn2 → F1 0.5
    assert out["per_seed"]["101"]["f1"] == pytest.approx(0.8)
    assert out["per_seed"]["202"]["f1"] == pytest.approx(0.5)
    assert out["mean_f1"] == pytest.approx(0.65)
    lo, hi = out["mean_f1_ci95"]
    assert 0.0 <= lo <= hi <= 1.0


def test_joint_bootstrap_uses_same_resample_for_all_seeds():
    s = seed_stats(scores(["MATCH", "MATCH", "NO_MATCH"]), GOLD, LEFT)["match"]
    a = joint_bootstrap([s, s], n=30, seed=7)
    b = joint_bootstrap([s], n=30, seed=7)
    assert np.allclose(a, b)  # identical seeds → mean equals the single-seed draw


def test_requires_decision_column():
    with pytest.raises(SystemExit):
        seed_stats(scores(["MATCH", "MATCH", "NO_MATCH"]).drop(columns="decision"), GOLD, LEFT)
