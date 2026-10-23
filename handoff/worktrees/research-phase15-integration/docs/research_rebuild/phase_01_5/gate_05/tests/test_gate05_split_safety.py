import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from split_safety import assign_folds, roles_for_fold, route_pairs

class Gate05SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.rows = [(f"e{i}", p) for i in range(30) for p in ("twitter", "instagram")]

    def test_fold_assignment_is_deterministic_and_entity_atomic(self):
        a = assign_folds(self.rows)
        self.assertEqual(a, assign_folds(reversed(self.rows)))
        self.assertEqual(set(a.values()), set(range(5)))

    def test_roles_follow_exact_rotating_five_fold_contract(self):
        fold_map = {f"e{i}": i for i in range(5)}
        roles = roles_for_fold(fold_map, 3)
        self.assertEqual(roles, {
            "e0": "POLICY_VALIDATION", "e1": "TRAIN", "e2": "TRAIN",
            "e3": "TEST", "e4": "CALIBRATION",
        })

    def test_cross_role_endpoint_drops_and_counts(self):
        roles = {"A":"TRAIN", "B":"TEST", "C":"TRAIN"}
        kept, counts = route_pairs([(1,2),(1,3)], {1:"A",2:"B",3:"C"}, roles)
        self.assertEqual(kept, [(1,3,"TRAIN")])
        self.assertEqual(counts, {"input_pairs":2,"same_role_pairs":1,"cross_role_dropped":1})

    def test_test_label_lifecycle_is_not_retrievable_before_final(self):
        # Synthetic capability boundary: labels are intentionally absent from
        # public inputs; evaluator receives them only after frozen predictions.
        public_pairs = [(1,2)]
        predictions = {pair: 0.25 for pair in public_pairs}
        self.assertNotIn("actual", predictions)
        labels = {(1,2): 1}
        with self.assertRaises(PermissionError):
            def read_labels(phase):
                if phase != "FINAL_EVALUATION": raise PermissionError
                return labels
            read_labels("POLICY_VALIDATION")
        self.assertEqual(read_labels("FINAL_EVALUATION")[(1,2)], 1)

if __name__ == "__main__": unittest.main()
