import json
from pathlib import Path

import pandas as pd
import pytest

from experiments.icsec_final.authoritative_run_v2.artifact_producers import (
    ArtifactProducerError,
    build_real_fixture,
    produce_scientific_input_artifacts,
    validate_input_artifacts,
)
from experiments.icsec_final.authoritative_run_v2.real_adapters import canonical_pair_key


def tiny_profiles():
    return pd.DataFrame({
        "profile_row_id": [1, 2, 3, 4, 5, 6, 7, 8],
        "user_folder": ["a", "a", "b", "b", "c", "c", "d", "d"],
        "platform": ["x", "y", "x", "y", "x", "y", "x", "y"],
    })


def tiny_routed():
    return pd.DataFrame({
        "profile_row_id_a": [1, 3, 5, 7],
        "profile_row_id_b": [2, 4, 6, 8],
        "pair_type": ["MODEL_SCORED", "MODEL_SCORED", "MODEL_SCORED", "AUTO_EXACT"],
        "pair_key": [canonical_pair_key(1, 2), canonical_pair_key(3, 4), canonical_pair_key(5, 6), canonical_pair_key(7, 8)],
        "role": ["TRAIN", "CALIBRATION", "POLICY_VALIDATION", "SEALED_TEST"],
    })


def manifest():
    return {"seed": 17, "roles": ["TRAIN", "CALIBRATION", "POLICY_VALIDATION", "SEALED_TEST"],
            "entity_role_hashes": {"TRAIN": [], "CALIBRATION": [], "POLICY_VALIDATION": [], "SEALED_TEST": []}}


def source_path(tmp_path):
    path = tmp_path / "source.csv"
    path.write_text("authoritative fixture\n")
    return path


def test_producer_separates_development_sealed_and_blocking_inputs(tmp_path):
    result = produce_scientific_input_artifacts(
        profiles=tiny_profiles(), routed_workflow=tiny_routed(), seed=17, output_root=tmp_path,
        source_path=source_path(tmp_path), split_manifest=manifest(),
    )
    development = pd.read_parquet(result["development_path"])
    sealed = pd.read_parquet(result["sealed_path"])
    misses = pd.read_parquet(result["blocking_miss_path"])
    assert set(development.columns) == {"pair_key", "actual", "role"}
    assert set(development.role) == {"TRAIN", "CALIBRATION", "POLICY_VALIDATION"}
    assert set(sealed.columns) == {"pair_key", "actual"}
    assert sealed.pair_key.tolist() == [canonical_pair_key(7, 8)]
    assert set(misses.columns) == {"pair_key", "pair_type"}
    assert result["disjointness"]["development_sealed_pair_overlap"] == 0
    assert result["NOT_MANUSCRIPT_EVIDENCE"] is True


def test_producer_rejects_noncanonical_routed_pair(tmp_path):
    cross = tiny_routed().assign(role="TRAIN")
    cross.loc[0, "profile_row_id_b"] = 4
    with pytest.raises(ArtifactProducerError, match="noncanonical"):
        produce_scientific_input_artifacts(tiny_profiles(), cross, 17, tmp_path, source_path(tmp_path), manifest())


def test_producer_rejects_global_blocking_invariant_mismatch(tmp_path):
    routed = tiny_routed().iloc[:3]
    with pytest.raises(ArtifactProducerError, match="blocking"):
        produce_scientific_input_artifacts(tiny_profiles(), routed, 17, tmp_path, source_path(tmp_path), manifest(), expected_global={"cross_platform_positives": 99})


def test_validation_rejects_wrong_role_label_and_sealed_overlap(tmp_path):
    result = produce_scientific_input_artifacts(tiny_profiles(), tiny_routed(), 17, tmp_path, source_path(tmp_path), manifest())
    development = pd.read_parquet(result["development_path"])
    development.loc[0, "role"] = "SEALED_TEST"
    development.to_parquet(result["development_path"], index=False)
    with pytest.raises(ArtifactProducerError, match="development"):
        validate_input_artifacts(result["metadata_path"])


def test_real_fixture_uses_role_specific_development_labels_and_blocking_misses(tmp_path):
    result = produce_scientific_input_artifacts(tiny_profiles(), tiny_routed(), 17, tmp_path, source_path(tmp_path), manifest())
    features = pd.DataFrame({"profile_row_id_a": [1, 3, 5], "profile_row_id_b": [2, 4, 6], **{f"f{i}": [0.1, 0.9, 0.5] for i in range(17)}})
    bert = pd.DataFrame({"profile_row_id_a": [1, 3, 5], "profile_row_id_b": [2, 4, 6], "bert_cos": [0.1, 0.9, 0.5]})
    fixture = build_real_fixture(result["metadata_path"], tiny_routed(), features, bert)
    assert fixture["sealed_label_path"] == str(result["sealed_path"].resolve())
    assert "SEALED_TEST" not in fixture["development_label_paths"]
    assert set(fixture["rows"].pair_type).issubset({"MODEL_SCORED", "AUTO_EXACT", "BLOCKING_MISS"})
