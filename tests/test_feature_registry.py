import json
import tempfile
import unittest
from pathlib import Path

from experiments.code.exp_name_similarity_ablation import _write_status
from identity_resolution.stages.feature_registry import group_for_feature, resolve_feature_set


class FeatureRegistryTests(unittest.TestCase):
    def test_named_experiment_enables_expected_group(self):
        self.assertEqual(resolve_feature_set("N4").extra_groups, ("name_handle",))

    def test_n6_accepts_only_registered_experiment_groups(self):
        feature_set = resolve_feature_set("N6", ("name_char_ngram", "name_cross_field"))
        self.assertEqual(feature_set.extra_groups, ("name_char_ngram", "name_cross_field"))
        with self.assertRaises(ValueError):
            resolve_feature_set("N6", ("not_a_group",))

    def test_feature_grouping_keeps_base_and_experiment_features_distinct(self):
        self.assertEqual(group_for_feature("username_jaro"), "name_existing")
        self.assertEqual(group_for_feature("name_handle_exact"), "name_handle")
        self.assertEqual(group_for_feature("image_phash_sim"), "image")

    def test_status_writer_records_a_run_and_shared_event(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "N1"
            _write_status(run_dir, "TRAINING", "fitting models")
            status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
            event = json.loads((run_dir.parent / "task_events.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(status["run_id"], "N1")
        self.assertEqual(event["state"], "TRAINING")
        self.assertIsInstance(status["pid"], int)
        self.assertIsNone(status["progress"])


if __name__ == "__main__":
    unittest.main()