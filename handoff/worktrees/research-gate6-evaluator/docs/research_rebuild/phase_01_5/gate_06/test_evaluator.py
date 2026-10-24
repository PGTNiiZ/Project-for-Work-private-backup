import unittest
from evaluator import evaluate


def row(a, b, y, role, action, score=None):
    d = {"a": a, "b": b, "label": y, "role": role, "action": action}
    if score is not None:
        d["score"] = score
    return d


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.exact = [row("a", "b", 1, "exact", "MATCH"), row("c", "d", 0, "exact", "MATCH")]
        self.scored = [row("e", "f", 1, "scored", "REVIEW", .8),
                       row("g", "h", 1, "scored", "NO_MATCH", .1),
                       row("i", "j", 0, "scored", "REVIEW", .5),
                       row("k", "l", 0, "scored", "NO_MATCH", .2)]
        self.misses = [row("m", "n", 1, "miss", "NO_MATCH")]

    def test_scopes_counts_metrics_and_cost_reconciliation(self):
        r = evaluate(self.exact, self.scored, self.misses, expected_positives=4)
        self.assertEqual((r["exact_n"], r["scored_n"], r["candidate_n"]), (2, 4, 6))
        c, w = r["candidate"], r["workflow"]
        self.assertEqual((c["TP"], c["FP"], c["FN"], c["R_plus"], c["R_minus"]), (1, 1, 1, 1, 1))
        self.assertEqual((w["TP"], w["FP"], w["FN"], w["R_plus"], w["R_minus"]), (1, 1, 2, 1, 1))
        self.assertEqual(w["positive_denominator"], 4)
        self.assertEqual(w["automatic_precision"], w["precision"])
        self.assertAlmostEqual(w["automatic_precision"], 0.5)
        self.assertAlmostEqual(w["U"], 4.2)
        self.assertEqual(w["U"], 2*w["FP"] + w["FN"] + .1*w["REVIEW"])
        self.assertEqual(w["U"]-c["U"], 1)
        self.assertEqual(r["independent_recompute"]["U"], w["U"])

    def test_positive_no_match_to_review_does_not_improve_automatic_metrics(self):
        base = evaluate([], [row("a", "b", 1, "scored", "MATCH", .9), row("c", "d", 1, "scored", "NO_MATCH", .2)], expected_positives=2)["candidate"]
        shifted = evaluate([], [row("a", "b", 1, "scored", "MATCH", .9), row("c", "d", 1, "scored", "REVIEW", .5)], expected_positives=2)["candidate"]
        self.assertEqual(base["automatic_recall"], shifted["automatic_recall"])
        self.assertEqual(base["automatic_F1"], shifted["automatic_F1"])
        self.assertGreater(shifted["conditional_recall"], base["conditional_recall"])

    def test_all_review(self):
        r = evaluate([], [row("a", "b", 1, "scored", "REVIEW", .5), row("c", "d", 0, "scored", "REVIEW", .5)])
        self.assertEqual((r["candidate"]["R_plus"], r["candidate"]["R_minus"], r["candidate"]["REVIEW"]), (1, 1, 2))
        self.assertEqual(r["candidate"]["candidate_coverage"], 0)

    def test_zero_positive_and_undefined_precision_are_null(self):
        m = evaluate([], [row("a", "b", 0, "scored", "NO_MATCH", .1)])
        self.assertIsNone(m["candidate"]["precision"])
        self.assertIsNone(m["candidate"]["automatic_recall"])
        self.assertIsNone(m["candidate"]["automatic_F1"])

    def test_exact_false_positive_is_counted(self):
        m = evaluate([row("a", "b", 0, "exact", "MATCH")], [])
        self.assertEqual(m["candidate"]["FP"], 1)

    def test_changed_costs(self):
        rows = [row("a", "b", 0, "scored", "MATCH", .9), row("c", "d", 1, "scored", "NO_MATCH", .1), row("e", "f", 0, "scored", "REVIEW", .5)]
        default = evaluate([], rows)["candidate"]
        changed = evaluate([], rows, costs=(5, 3, .2))["candidate"]
        self.assertEqual(default["U"], 3.1)
        self.assertEqual(changed["U"], 8.2)
        self.assertEqual(changed["cost_parameters"], {"FP": 5, "FN": 3, "REVIEW": .2})

    def test_reject_duplicate_key_including_reversed_endpoints(self):
        with self.assertRaisesRegex(ValueError, "duplicate canonical"):
            evaluate([], [row("a", "b", 1, "scored", "MATCH", .9), row("b", "a", 1, "scored", "MATCH", .9)])

    def test_reject_invalid_action(self):
        with self.assertRaisesRegex(ValueError, "invalid action"):
            evaluate([], [row("a", "b", 1, "scored", "MAYBE", .9)])

    def test_reject_scope_overlap_and_bad_costs(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            evaluate([row("a", "b", 1, "exact", "MATCH")], [row("b", "a", 1, "scored", "MATCH", .9)])
        with self.assertRaisesRegex(ValueError, "costs"):
            evaluate([], [], costs=(-1, 1, .1))

    def test_reject_positive_accounting_mismatch(self):
        with self.assertRaisesRegex(ValueError, "positive accounting"):
            evaluate([], [], expected_positives=1)


if __name__ == "__main__":
    unittest.main()
