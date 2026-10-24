import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments.icsec_final.authoritative_run_v2.final_runner import (
    FINAL_BUDGET,
    FinalRunnerError,
    FinalSealedEvaluationRunner,
    deterministic_sample_indices,
    make_synthetic_fixture,
)


def run_fixture(tmp_path: Path):
    fixture = make_synthetic_fixture()
    runner = FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16)
    return runner, runner.run()


def test_complete_synthetic_runner_is_not_manuscript_evidence(tmp_path):
    runner, result = run_fixture(tmp_path)
    assert result["NOT_MANUSCRIPT_EVIDENCE"] is True
    assert result["PRE-FINAL TEST LABEL READS"] == 0
    assert result["independent_metrics_match"] is True
    assert result["fairness"]["passed"] is True
    prediction = pd.read_parquet(tmp_path / "sealed_predictions" / "predictions.parquet")
    assert set(prediction.model_policy) == {"GB17_B0", "B0", "B1", "B2", "B3"}
    assert (tmp_path / "SHA256SUMS.txt").is_file()
    assert runner.phase == "complete"


def test_real_lazy_label_artifact_runs_only_at_final_boundary(tmp_path):
    from experiments.icsec_final.authoritative_run_v2.real_adapters import canonical_pair_key
    fixture = make_synthetic_fixture()
    keys = [canonical_pair_key(i * 2 + 1, i * 2 + 2) for i in range(len(fixture["rows"]))]
    old_keys = fixture["rows"]["pair_key"].tolist()
    fixture["rows"] = fixture["rows"].assign(pair_key=keys)
    lookup = dict(zip(old_keys, keys))
    label_path = tmp_path / "real_sealed_labels.parquet"
    pd.DataFrame({"pair_key": [lookup[key] for key in fixture["sealed_labels"]], "actual": list(fixture["sealed_labels"].values())}).to_parquet(label_path)
    fixture["sealed_label_path"] = label_path
    blocking_path = tmp_path / "blocking_misses.parquet"
    missed_keys = fixture["rows"].loc[fixture["rows"].pair_type == "BLOCKING_MISS", "pair_key"]
    pd.DataFrame({"pair_key": missed_keys, "pair_type": "BLOCKING_MISS"}).to_parquet(blocking_path, index=False)
    fixture["blocking_miss_path"] = blocking_path
    fixture.pop("sealed_labels")
    runner = FinalSealedEvaluationRunner(fixture, tmp_path / "run", seed=17, budget=16)
    result = runner.run()
    assert result["PRE-FINAL TEST LABEL READS"] == 0
    assert runner.sealer.file_reads == 5


def test_final_budget_is_not_the_dry_run_budget():
    assert FINAL_BUDGET == 12000


def test_training_uses_frozen_three_to_one_negative_sampling():
    labels = np.array([1, 1] + [0] * 10, dtype=np.int8)
    first = deterministic_sample_indices(labels, ratio=3.0, seed=101)
    second = deterministic_sample_indices(labels, ratio=3.0, seed=101)
    np.testing.assert_array_equal(first, second)
    sampled = labels[first]
    assert int((sampled == 1).sum()) == 2
    assert int((sampled == 0).sum()) == 6


def test_runner_rejects_pre_final_test_label_access(tmp_path):
    fixture = make_synthetic_fixture()
    runner = FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16)
    with pytest.raises(FinalRunnerError, match="sealed labels"):
        runner.sealed_labels(["p0"], phase="TRAIN")


def test_runner_rejects_overlapping_entities(tmp_path):
    fixture = make_synthetic_fixture()
    fixture["roles"]["CALIBRATION"].add(next(iter(fixture["roles"]["TRAIN"])))
    with pytest.raises(FinalRunnerError, match="overlap"):
        FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16).validate_roles()


def test_runner_rejects_legacy_name_similarity_marker(tmp_path):
    fixture = make_synthetic_fixture()
    fixture["legacy_name_sim_reachable"] = True
    with pytest.raises(FinalRunnerError, match="legacy"):
        FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16).validate_inputs()


def test_runner_rejects_wrong_gb17_feature_count(tmp_path):
    fixture = make_synthetic_fixture()
    fixture["features17"] = fixture["features17"].drop(columns="name_sim")
    with pytest.raises(FinalRunnerError, match="GB-17"):
        FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16).validate_inputs()


def test_runner_rejects_unexpected_gb18_feature(tmp_path):
    fixture = make_synthetic_fixture()
    fixture["bert"] = fixture["bert"].assign(unexpected=0.0)
    with pytest.raises(FinalRunnerError, match="GB-18"):
        FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16).validate_inputs()


def test_runner_rejects_unfair_policy_configuration(tmp_path):
    fixture = make_synthetic_fixture()
    fixture["policy_override"] = {"B3": {"class": "different"}}
    runner = FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16)
    runner.validate_inputs()
    runner.validate_roles()
    runner.train_and_calibrate()
    runner.select_policies()
    with pytest.raises(FinalRunnerError, match="fairness"):
        runner.assert_fairness()


def test_runner_rejects_budget_not_matching_protocol(tmp_path):
    fixture = make_synthetic_fixture()
    with pytest.raises(FinalRunnerError, match="budget"):
        FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=15)


def test_runner_detects_policy_change_after_freeze(tmp_path):
    fixture = make_synthetic_fixture()
    runner = FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16)
    runner.validate_inputs(); runner.validate_roles(); runner.train_and_calibrate()
    runner.select_policies(); runner.assert_fairness(); runner.freeze_pre_test()
    runner.policies["B0"] = (0.99, 0.95)
    with pytest.raises(FinalRunnerError, match="freeze"):
        runner.generate_sealed_predictions()


def test_independent_recomputation_detects_tampered_row_decisions(tmp_path):
    runner, _ = run_fixture(tmp_path)
    path = tmp_path / "decisions" / "B0_workflow.parquet"
    frame = pd.read_parquet(path)
    frame.loc[0, "decision"] = 2 - int(frame.loc[0, "decision"])
    frame.to_parquet(path, index=False)
    with pytest.raises(FinalRunnerError, match="independent"):
        runner.independent_recompute()


def test_provenance_fails_when_required_input_missing(tmp_path):
    fixture = make_synthetic_fixture()
    runner = FinalSealedEvaluationRunner(fixture, tmp_path, seed=17, budget=16)
    runner.required_inputs.pop()
    with pytest.raises(FinalRunnerError, match="provenance"):
        runner.capture_provenance()


def test_hash_verification_detects_tampering(tmp_path):
    runner, _ = run_fixture(tmp_path)
    path = tmp_path / "summary.json"
    path.write_text(json.dumps({"tampered": True}))
    with pytest.raises(FinalRunnerError, match="hash"):
        runner.verify_hashes()
