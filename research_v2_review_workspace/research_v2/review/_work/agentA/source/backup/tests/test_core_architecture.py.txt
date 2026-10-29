import ast
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from identity_resolution.cli import STAGES, usage
from identity_resolution.core.decisioning import ThresholdPolicy
from identity_resolution.core.entities import UnionFind, choose_canonical_name
from identity_resolution.core.pairs import pair_key, unpack_pair_key
from identity_resolution.settings import PATHS
from identity_resolution.stages import STAGE_ORDER
from identity_resolution.workflows.crm import build_match_decisions


class ThresholdPolicyTests(unittest.TestCase):
    def test_boundaries_and_metadata(self):
        policy = ThresholdPolicy(match_threshold=0.98, review_threshold=0.95)
        decisions = policy.decide([0.99, 0.98, 0.97, 0.95, 0.94])
        self.assertEqual(
            decisions.tolist(),
            ["MATCH", "MATCH", "REVIEW", "REVIEW", "NO_MATCH"],
        )
        self.assertEqual(
            policy.decision_sources(decisions).tolist(),
            ["AUTO_HIGH", "AUTO_HIGH", "AUTO_REVIEW", "AUTO_REVIEW", "AUTO_LOW"],
        )

    def test_invalid_threshold_order_is_rejected(self):
        with self.assertRaises(ValueError):
            ThresholdPolicy(match_threshold=0.90, review_threshold=0.95)


class DomainPrimitiveTests(unittest.TestCase):
    def test_pair_key_is_unordered_and_reversible(self):
        key = pair_key(12, 3)
        self.assertEqual(key, pair_key(3, 12))
        self.assertEqual(unpack_pair_key(key), (3, 12))

    def test_union_find_and_canonical_name(self):
        groups = UnionFind()
        groups.union(9, 2)
        groups.union(2, 5)
        self.assertEqual(groups.find(9), groups.find(5))
        self.assertEqual(choose_canonical_name(["", "Ann", "Ann", "Anna"]), "Ann")


class CRMWorkflowBoundaryTests(unittest.TestCase):
    def test_crm_workflow_uses_core_threshold_policy(self):
        scored = pd.DataFrame(
            {
                "profile_row_id_a": [1, 2, 3],
                "profile_row_id_b": [11, 12, 13],
                "probability": [0.99, 0.96, 0.20],
                "label": [1, 1, 0],
                "pair_type": ["candidate"] * 3,
                "split_name": ["test"] * 3,
            }
        )
        result = build_match_decisions(scored, 0.98, 0.95)
        self.assertEqual(result["decision"].tolist(), ["MATCH", "REVIEW", "NO_MATCH"])
        self.assertEqual(result["review_status"].tolist(), ["APPROVED", "PENDING", "SKIPPED"])
        self.assertTrue(np.all(result["decision_id"].str.len() > 0))


class DependencyDirectionTests(unittest.TestCase):
    def test_lifecycle_order_and_central_paths(self):
        self.assertEqual(
            STAGE_ORDER,
            ("prepare", "pairs", "features", "train", "evaluate", "predict", "resolve"),
        )
        self.assertTrue(PATHS.profiles.exists())
        self.assertEqual(PATHS.production_model_run.name, "image_context_r075_h20_s42")
        self.assertEqual(set(STAGE_ORDER), {name for name in STAGES if name != "train-neural"})
        self.assertIn("identity-ml <stage>", usage())

    def test_core_does_not_depend_on_workflows_or_legacy_scripts(self):
        core_dir = Path(__file__).resolve().parents[1] / "src" / "identity_resolution" / "core"
        forbidden = ("identity_resolution.workflows", "train_data", "experiments", "pub_multi")
        for path in core_dir.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            self.assertFalse(
                any(name.startswith(forbidden) for name in imports),
                f"{path} violates the core dependency boundary: {imports}",
            )


if __name__ == "__main__":
    unittest.main()
