import pandas as pd
import pytest

from common.evaluate import per_left_stats, possible_block, summarize

GOLD = {("l1", "r1"), ("l2", "r2"), ("l3", "r3")}  # l3/r3 is blocked out
SCORES = pd.DataFrame({
    "left_id": ["l1", "l1", "l2", "l2", "l4"],
    "right_id": ["r1", "r9", "r2", "r8", "r7"],
    "score": [0.95, 0.80, 0.75, 0.10, 0.72],
})
LEFT = ["l1", "l2", "l3", "l4"]


def test_match_only_counts_blocked_gold_as_fn():
    p = summarize(per_left_stats(SCORES, GOLD, LEFT, 0.90))
    # tp: l1-r1; fp: none; fn: l2-r2 (below thr) + l3-r3 (blocked out)
    assert p["precision"] == 1.0
    assert p["recall"] == pytest.approx(1 / 3)


def test_match_plus_possible_and_review_rate():
    out = possible_block(SCORES, GOLD, LEFT, 0.90, 0.70, n_boot=20, seed=1)
    p = out["point"]
    # score >= 0.70: tp l1-r1, l2-r2; fp l1-r9, l4-r7
    assert p["precision"] == pytest.approx(0.5)
    assert p["recall"] == pytest.approx(2 / 3)
    # review band [0.70, 0.90): 0.80, 0.75, 0.72 of 5 candidates
    assert out["n_review"] == 3
    assert out["review_rate"] == pytest.approx(0.6)


def test_possible_above_match_rejected():
    with pytest.raises(ValueError):
        possible_block(SCORES, GOLD, LEFT, 0.70, 0.90, n_boot=5, seed=1)
