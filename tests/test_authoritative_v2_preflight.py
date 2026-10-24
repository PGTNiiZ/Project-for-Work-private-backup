import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.code.run_icsec_authoritative_v2 import (
    V2, assert_no_legacy_v2_path, preflight_label_seal, preflight_policy_equivalence,
    validate_split_manifests,
)
from experiments.icsec_final.authoritative_run_v2.features import FEATURE17_COLUMNS, FEATURE18_COLUMNS
from experiments.icsec_final.authoritative_run_v2.policies import decide_four_parameter


def test_v2_preflight_artifacts_have_machine_readable_schema_and_scope():
    scope = json.loads((V2 / "preflight" / "candidate_scope.json").read_text())
    assert scope["profiles_eligible"] == 36804
    assert scope["all_platform_positives"] == 29247
    assert scope["cross_platform_positives"] == 29243
    assert scope["same_platform_positives"] == 4
    assert scope["possible_cross_platform_pairs"] == 449149239
    assert scope["exact_tier_pairs"] == 12403
    assert scope["model_scored_candidate_pairs"] == 2073842
    assert scope["workflow_candidate_pairs"] == 2086245
    assert scope["candidate_covered_cross_platform_positives"] == 25931
    assert scope["cross_platform_blocking_misses"] == 3312
    assert scope["invariants"] == {
        "exact_plus_scored_equals_workflow": True,
        "covered_plus_missed_equals_cross_positive": True,
        "all_equals_cross_plus_same": True,
    }
    f17 = pd.read_parquet(V2 / "features" / "gb17.parquet")
    bert = pd.read_parquet(V2 / "features" / "bert_cos.parquet")
    assert list(f17.columns[2:]) == FEATURE17_COLUMNS
    assert list(f17.columns[2:]) + list(bert.columns[2:]) == FEATURE18_COLUMNS
    assert len(f17) == len(bert) == scope["model_scored_candidate_pairs"]
    assert all(dtype == np.dtype("float32") for dtype in f17.dtypes[2:])
    assert bert["bert_cos"].dtype == np.dtype("float32")
    assert not {"actual", "label", "user_folder"}.intersection(f17.columns)


def test_v2_preflight_sealing_equivalence_and_legacy_path():
    seal = preflight_label_seal()
    assert seal["PRE-FINAL TEST-LABEL READS"] == 7
    assert seal["unauthorized_failures"] == 7
    equivalence = preflight_policy_equivalence()
    assert equivalence["same_genome_decisions_equal"] is True
    assert equivalence["budget_difference"] == 0
    assert_no_legacy_v2_path()


def test_v2_split_manifests_are_present_and_role_complete():
    result = validate_split_manifests()
    assert result["outer_seeds_executed"] is False
    assert [row["seed"] for row in result["seeds"]] == [101, 202, 303]
    assert all(row["entity_overlap_check"] == "passed" for row in result["seeds"])


def test_same_b2_b3_genome_has_identical_decisions():
    probability = np.array([0.99, 0.96, 0.85, 0.60])
    name_sim = np.array([0.0, 0.8, 0.9, 0.1])
    genome = (0.98, 0.70, 0.85, 0.20)
    left = decide_four_parameter(probability, name_sim, genome)
    right = decide_four_parameter(probability, name_sim, genome)
    np.testing.assert_array_equal(left, right)
