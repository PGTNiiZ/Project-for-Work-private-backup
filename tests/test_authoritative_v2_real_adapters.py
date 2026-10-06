import json
from pathlib import Path

import pandas as pd
import pytest

from experiments.icsec_final.authoritative_run_v2.real_adapters import (
    AdapterError,
    LazySealedLabelStore,
    assert_label_free_artifacts,
    build_entity_role_map,
    canonical_pair_key,
    route_pairs,
    safe_final_join,
)


def manifest():
    return {"seed": 17, "roles": ["TRAIN", "CALIBRATION", "POLICY_VALIDATION", "SEALED_TEST"],
            "entity_role_hashes": {"TRAIN": ["a"], "CALIBRATION": ["b"], "POLICY_VALIDATION": ["c"], "SEALED_TEST": ["d"]}}


def profiles():
    return pd.DataFrame({"profile_row_id": [1, 2, 3, 4, 5, 6], "user_folder": ["a", "b", "c", "d", "a", "d"]})


def test_routes_real_candidate_schema_and_drops_cross_role_pairs():
    pair = pd.DataFrame({"profile_row_id_a": [1, 1, 4], "profile_row_id_b": [5, 2, 6], "pair_type": ["MODEL_SCORED"] * 3})
    routed, report = route_pairs(pair, profiles(), build_entity_role_map(profiles(), manifest(), entity_hash=lambda x: x))
    assert routed.role.tolist() == ["TRAIN", "SEALED_TEST"]
    assert report["cross_role_dropped"] == 1
    assert routed.pair_key.is_unique


def test_unknown_entity_conflict_and_cross_role_leakage_fail_closed():
    with pytest.raises(AdapterError, match="unknown"):
        build_entity_role_map(pd.DataFrame({"profile_row_id": [1], "user_folder": ["x"]}), manifest(), entity_hash=lambda x: x)
    bad = manifest(); bad["entity_role_hashes"]["CALIBRATION"].append("a")
    with pytest.raises(AdapterError, match="conflicting"):
        build_entity_role_map(profiles(), bad, entity_hash=lambda x: x)
    pairs = pd.DataFrame({"profile_row_id_a": [1], "profile_row_id_b": [2], "pair_type": ["MODEL_SCORED"]})
    routed, _ = route_pairs(pairs, profiles(), build_entity_role_map(profiles(), manifest(), entity_hash=lambda x: x))
    assert routed.empty


def test_lazy_real_labels_reject_pre_final_and_prediction_labels(tmp_path):
    path = tmp_path / "labels.parquet"
    pd.DataFrame({"pair_key": [canonical_pair_key(1, 2)], "actual": [1]}).to_parquet(path)
    store = LazySealedLabelStore(path)
    with pytest.raises(AdapterError, match="FINAL_EVALUATION"):
        store.read([canonical_pair_key(1, 2)], phase="TRAIN")
    prediction = pd.DataFrame({"pair_key": [canonical_pair_key(1, 2)], "decision": [2], "actual": [1]})
    with pytest.raises(AdapterError, match="label"):
        safe_final_join(prediction, store, phase="FINAL_EVALUATION")


def test_safe_final_join_is_keyed_unique_complete_and_order_independent(tmp_path):
    keys = [canonical_pair_key(1, 2), canonical_pair_key(3, 4)]
    path = tmp_path / "labels.parquet"
    pd.DataFrame({"pair_key": keys[::-1], "actual": [0, 1]}).to_parquet(path)
    prediction = pd.DataFrame({"pair_key": keys, "decision": [2, 0]})
    result = safe_final_join(prediction, LazySealedLabelStore(path), phase="FINAL_EVALUATION")
    assert result.actual.tolist() == [1, 0]
    with pytest.raises(AdapterError):
        safe_final_join(prediction.iloc[[0, 0]], LazySealedLabelStore(path), phase="FINAL_EVALUATION")
    missing = pd.DataFrame({"pair_key": [canonical_pair_key(5, 6)], "decision": [2]})
    with pytest.raises(AdapterError, match="missing"):
        safe_final_join(missing, LazySealedLabelStore(path), phase="FINAL_EVALUATION")
    pd.DataFrame({"pair_key": [keys[0], keys[0]], "actual": [1, 1]}).to_parquet(path)
    with pytest.raises(AdapterError, match="duplicate"):
        safe_final_join(prediction, LazySealedLabelStore(path), phase="FINAL_EVALUATION")


def test_hidden_test_label_cache_path_is_rejected(tmp_path):
    path = tmp_path / "candidate.parquet"
    pd.DataFrame({"pair_key": [canonical_pair_key(1, 2)], "actual": [1]}).to_parquet(path)
    with pytest.raises(AdapterError, match="hidden test-label"):
        assert_label_free_artifacts([path])


def test_canonical_key_rejects_noncanonical_pair_input():
    assert canonical_pair_key(2, 1) == canonical_pair_key(1, 2)
    with pytest.raises(AdapterError, match="same"):
        canonical_pair_key(1, 1)
