import unittest
import json

import numpy as np
import pandas as pd

from experiments.code.run_full_feature_aware_ga_pipeline import apply_frozen_policy, freeze_policy
from experiments.code.run_one_stage_weighted_ga_experiment import policy_matrices
from experiments.code.run_feature_aware_ga_pipeline import (
    ONE_STAGE_POLICY_FEATURES,
    clip_one_stage_genome,
    decisions,
    decision_metrics,
    feature_group,
    one_stage_decisions,
    one_stage_policy_score,
    optimize_one_stage_policy,
)


class FeatureAwareGATests(unittest.TestCase):
    def test_feature_group_maps_identity_features_to_name(self):
        self.assertEqual(feature_group("username_token_sort"), "name")
        self.assertEqual(feature_group("fullname_jaro"), "name")
        self.assertEqual(feature_group("bio_tfidf_cosine"), "bio")

    def test_missing_evidence_stays_review_in_the_review_band(self):
        genome = np.array([0.90, 0.50, 0.80, 0.30])
        result = decisions(
            np.array([0.70, 0.70, 0.70]),
            np.array([0.95, 0.10, 0.95]),
            np.array([1, 1, 0]),
            genome,
        )
        np.testing.assert_array_equal(result, np.array([2, 0, 1], dtype=np.int8))

    def test_decision_cost_uses_the_declared_business_weights(self):
        decision = np.array([2, 0, 1, 2], dtype=np.int8)
        labels = np.array([0, 1, 0, 1], dtype=np.int8)
        values = decision_metrics(decision, labels)
        self.assertEqual(values["fp"], 1)
        self.assertEqual(values["fn"], 1)
        self.assertEqual(values["review"], 1)
        self.assertAlmostEqual(values["cost"], 3.1)

    def test_full_runner_freezes_lower_validation_cost_before_test(self):
        selector = {"guard": "bio", "genome": json.dumps([0.90, 0.50, 0.80, 0.30]), "validation_cost": 10.0}
        weighted = {
            "active_groups": ["name", "bio"],
            "thresholds": [0.90, 0.50, 0.80, 0.30],
            "weights": {"name": 0.5, "bio": 0.5},
            "validation_metrics": {"cost": 11.0},
        }
        policy = freeze_policy(selector, weighted)
        self.assertEqual(policy["policy"], "selector:bio")
        self.assertNotIn("test_metrics", policy)

    def test_full_runner_applies_selector_with_availability_mask(self):
        cache = pd.DataFrame({
            "probability": [0.70, 0.70, 0.70, 0.95],
            "bio_score": [0.95, 0.10, 0.95, 0.00],
            "bio_available": [1, 1, 0, 0],
        })
        policy = {"policy": "selector:bio", "guard": "bio", "thresholds": [0.90, 0.50, 0.80, 0.30]}
        result = apply_frozen_policy(cache, policy)
        np.testing.assert_array_equal(result, np.array([2, 0, 1, 2], dtype=np.int8))

    def test_one_stage_genome_has_two_thresholds_and_eight_normalized_weights(self):
        active = np.array([1, 1, 1, 1, 0, 1, 1, 1], dtype=bool)
        genome = clip_one_stage_genome(
            np.array([1.20, 0.80, 1.0, -1.0, 2.0, 0.0, 5.0, 3.0, 0.0, 4.0]),
            active,
        )
        self.assertEqual(len(genome), 2 + len(ONE_STAGE_POLICY_FEATURES))
        self.assertEqual(genome[0], 0.999)
        self.assertEqual(genome[1], 0.8)
        self.assertEqual(genome[2 + 4], 0.0)
        self.assertTrue((genome[2:] >= 0.0).all())
        self.assertAlmostEqual(float(genome[2:].sum()), 1.0)

    def test_one_stage_score_renormalizes_when_evidence_is_missing(self):
        scores = np.array([
            [0.8, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.8, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ])
        masks = np.array([
            [1, 1, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0],
        ])
        weights = np.array([0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        np.testing.assert_allclose(one_stage_policy_score(scores, masks, weights), [0.5, 0.8])

    def test_one_stage_decision_uses_only_final_two_thresholds(self):
        scores = np.zeros((3, len(ONE_STAGE_POLICY_FEATURES)))
        scores[:, 0] = [0.90, 0.70, 0.49]
        masks = np.zeros_like(scores)
        masks[:, 0] = 1.0
        genome = np.array([0.90, 0.50, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        np.testing.assert_array_equal(
            one_stage_decisions(scores, masks, genome),
            np.array([2, 1, 0], dtype=np.int8),
        )

    def test_one_stage_policy_keeps_all_missing_rows_in_review(self):
        scores = np.ones((1, len(ONE_STAGE_POLICY_FEATURES)))
        masks = np.zeros_like(scores)
        genome = np.array([0.90, 0.50, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125])
        np.testing.assert_array_equal(one_stage_decisions(scores, masks, genome), [1])

    def test_one_stage_optimizer_is_deterministic_and_zeros_inactive_features(self):
        scores = np.zeros((6, len(ONE_STAGE_POLICY_FEATURES)))
        scores[:, 0] = [0.95, 0.85, 0.65, 0.45, 0.25, 0.05]
        masks = np.zeros_like(scores)
        masks[:, 0] = 1.0
        labels = np.array([1, 1, 1, 0, 0, 0], dtype=np.int8)
        active = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=bool)
        first, first_history = optimize_one_stage_policy(
            scores,
            masks,
            labels,
            123,
            active_mask=active,
            population_size=12,
            generations=6,
            elite_size=3,
        )
        second, second_history = optimize_one_stage_policy(
            scores,
            masks,
            labels,
            123,
            active_mask=active,
            population_size=12,
            generations=6,
            elite_size=3,
        )
        np.testing.assert_allclose(first, second)
        np.testing.assert_array_equal(first[2:], active.astype(float))
        self.assertEqual(first_history, second_history)

    def test_one_stage_policy_zeros_features_below_coverage_gate(self):
        cache = pd.DataFrame({"probability": [0.9, 0.8, 0.2, 0.1]})
        for feature in ONE_STAGE_POLICY_FEATURES[1:]:
            cache[f"{feature}_score"] = [0.9, 0.8, 0.2, 0.1]
            cache[f"{feature}_available"] = 1
        cache["location_available"] = 0
        cache["social_available"] = [1, 0, 0, 0]
        labels = np.array([1, 1, 0, 0], dtype=np.int8)
        _, _, active = policy_matrices(
            cache,
            labels,
            min_coverage=0.50,
            min_positive_support=1,
        )
        self.assertTrue(active[0])
        self.assertFalse(active[ONE_STAGE_POLICY_FEATURES.index("location")])
        self.assertFalse(active[ONE_STAGE_POLICY_FEATURES.index("social")])
        self.assertTrue(active[ONE_STAGE_POLICY_FEATURES.index("image")])
        # Disabling support gates must not make an unobserved weight learnable.
        _, _, ungated = policy_matrices(
            cache, labels, min_coverage=0.0, min_positive_support=0,
        )
        self.assertFalse(ungated[ONE_STAGE_POLICY_FEATURES.index("location")])
        self.assertTrue(ungated[ONE_STAGE_POLICY_FEATURES.index("social")])


if __name__ == "__main__":
    unittest.main()
