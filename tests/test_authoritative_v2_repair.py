import numpy as np
import pytest

from experiments.icsec_final.authoritative_run_v2.features import corrected_name_sim
from experiments.icsec_final.authoritative_run_v2.label_sealing import (
    LabelAccessError,
    SealedLabels,
)
from experiments.icsec_final.authoritative_run_v2.pipeline import (
    PublicPairData,
    V2EvaluationBoundary,
)
from experiments.icsec_final.authoritative_run_v2.policies import (
    B0_FIXED,
    b0_decide,
    b1_search,
    b2_sobol_search,
    b3_ga_search,
    decide_four_parameter,
)


def test_corrected_name_sim_is_deterministic_and_uncensored():
    values = corrected_name_sim(["alice"], ["Alice Smith"], ["alicia"], ["Alice Smith"])
    assert values == corrected_name_sim(["alice"], ["Alice Smith"], ["alicia"], ["Alice Smith"])
    assert values[0] == 1.0


def test_corrected_name_sim_has_deterministic_missing_behavior():
    assert corrected_name_sim([None], [""], ["bob"], [None]) == [0.0]


def test_name_sim_signature_has_no_predecessor_or_label_argument():
    assert corrected_name_sim.__code__.co_argcount == 4
    assert "score" not in corrected_name_sim.__code__.co_varnames
    assert "actual" not in corrected_name_sim.__code__.co_varnames


def test_sealed_labels_are_denied_before_final_evaluation():
    labels = SealedLabels({"pair-1": 1})
    with pytest.raises(LabelAccessError):
        labels.join(["pair-1"], phase="policy_validation")
    assert labels.audit[-1]["allowed"] is False


def test_public_pre_final_data_rejects_label_and_entity_columns():
    with pytest.raises(ValueError):
        PublicPairData(({"pair_key": "pair-1", "actual": 1},))


def test_boundary_opens_labels_only_after_phase_freeze():
    boundary = V2EvaluationBoundary(
        PublicPairData(({"pair_key": "pair-1", "score": 0.9},)),
        SealedLabels({"pair-1": 1}),
    )
    with pytest.raises(RuntimeError):
        boundary.final_join(["pair-1"])
    boundary.set_phase("final_evaluation")
    assert boundary.final_join(["pair-1"])[0]["actual"] == 1


def test_b0_uses_fixed_protocol_thresholds():
    assert B0_FIXED == (0.98, 0.95)
    assert list(b0_decide(np.array([0.99, 0.96, 0.94]))) == [2, 1, 0]


def test_b1_b2_b3_have_same_four_parameter_semantics():
    prob = np.array([0.99, 0.96, 0.85, 0.60])
    nsim = np.array([0.0, 0.8, 0.9, 0.1])
    genome = (0.98, 0.70, 0.85, 0.20)
    expected = decide_four_parameter(prob, nsim, genome)
    assert list(expected) == [2, 1, 2, 0]
    assert b1_search.__name__ == "b1_search"
    assert b2_sobol_search.__name__ == "b2_sobol_search"
    assert b3_ga_search.__name__ == "b3_ga_search"


def test_b2_and_b3_report_equal_realized_budget():
    prob = np.array([0.99, 0.96, 0.85, 0.60])
    nsim = np.array([0.0, 0.8, 0.9, 0.1])
    _, b2_meta = b2_sobol_search(prob, nsim, np.array([1, 1, 0, 0]), budget=16)
    _, b3_meta = b3_ga_search(prob, nsim, np.array([1, 1, 0, 0]), budget=16)
    assert b2_meta["realized_evaluations"] == b3_meta["realized_evaluations"] == 16
