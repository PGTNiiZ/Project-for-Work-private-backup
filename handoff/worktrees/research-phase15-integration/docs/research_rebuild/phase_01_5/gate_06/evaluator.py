"""Standalone, data-agnostic three-action pair evaluator (no production imports)."""
from __future__ import annotations
from collections import Counter
from math import isfinite

ACTIONS = {"MATCH", "REVIEW", "NO_MATCH"}
ROLES = {"exact", "scored"}


def canonical_key(a: str, b: str) -> tuple[str, str]:
    if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
        raise ValueError("endpoints must be non-empty strings")
    if a == b:
        raise ValueError("self-pairs are invalid")
    return tuple(sorted((a, b)))


def _validate(rows, role: str, *, misses=False):
    seen = set()
    for row in rows:
        key = canonical_key(row["a"], row["b"])
        if key in seen:
            raise ValueError(f"duplicate canonical pair key: {key}")
        seen.add(key)
        y = row["label"]
        if y not in (0, 1) or isinstance(y, bool):
            raise ValueError("label must be integer 0 or 1")
        if misses:
            if y != 1:
                raise ValueError("blocking misses must be positive")
            continue
        if row.get("role") != role:
            raise ValueError(f"row role must be {role}")
        if row.get("action") not in ACTIONS:
            raise ValueError(f"invalid action: {row.get('action')}")
        if role == "scored" and ("score" not in row or not isfinite(float(row["score"])) or not 0 <= float(row["score"]) <= 1):
            raise ValueError("scored rows require finite score in [0,1]")
    return seen


def evaluate(exact, scored, misses=(), *, costs=(2.0, 1.0, 0.1), expected_positives=None):
    """Return metrics for candidate and workflow scopes. Undefined ratios are None."""
    exact, scored, misses = list(exact), list(scored), list(misses)
    ekeys = _validate(exact, "exact")
    skeys = _validate(scored, "scored")
    mkeys = _validate(misses, "", misses=True)
    if ekeys & skeys or ekeys & mkeys or skeys & mkeys:
        raise ValueError("exact/scored/miss pair-key scopes overlap")
    if len(costs) != 3 or any(not isfinite(float(c)) or c < 0 for c in costs):
        raise ValueError("costs must be three finite non-negative values (FP,FN,REVIEW)")
    rows = exact + scored

    def counts(rs, add_misses=False):
        c = Counter()
        for r in rs:
            c[(r["label"], r["action"])] += 1
        tp = c[1, "MATCH"]
        fp = c[0, "MATCH"]
        fn = c[1, "NO_MATCH"] + (len(misses) if add_misses else 0)
        rp, rn = c[1, "REVIEW"], c[0, "REVIEW"]
        tn = c[0, "NO_MATCH"]
        pos = tp + fn + rp
        if expected_positives is not None and add_misses and pos != expected_positives:
            raise ValueError(f"positive accounting mismatch: {pos} != {expected_positives}")
        div = lambda n, d: n / d if d else None
        review = rp + rn
        precision = div(tp, tp + fp)
        conditional_recall = div(tp, tp + (fn - (len(misses) if add_misses else 0)))
        conditional_fn = c[1, "NO_MATCH"]
        conditional_recall = div(tp, tp + conditional_fn)
        conditional_f1 = div(2 * tp, 2 * tp + fp + conditional_fn)
        auto_recall = div(tp, pos)
        auto_f1 = div(2 * tp, 2 * tp + fp + fn + rp)
        coverage = div(len(rs) - review, len(rs))
        cost = costs[0] * fp + costs[1] * fn + costs[2] * review
        return {"n": len(rs), "positive_denominator": pos, "TP": tp, "FP": fp, "FN": fn,
                "R_plus": rp, "R_minus": rn, "REVIEW": review, "TN_candidate": tn,
                "automatic_precision": precision, "precision": precision, "conditional_recall": conditional_recall,
                "conditional_F1": conditional_f1, "automatic_recall": auto_recall,
                "automatic_F1": auto_f1, "candidate_coverage": coverage,
                "cost_parameters": {"FP": costs[0], "FN": costs[1], "REVIEW": costs[2]},
                "U": cost}

    candidate = counts(rows)
    workflow = counts(rows, add_misses=True)
    if expected_positives is not None and candidate["positive_denominator"] + len(misses) != expected_positives:
        raise ValueError("candidate positives + blocking misses != expected positives")
    # Independent recomputation from row-level label/action pairs, not summary counts.
    recomputed = _independent(rows, len(misses), costs)
    for k in ("TP", "FP", "FN", "R_plus", "R_minus", "REVIEW", "TN_candidate", "U"):
        if workflow[k] != recomputed[k]:
            raise AssertionError(f"independent recomputation mismatch for {k}")
    return {"exact_n": len(exact), "scored_n": len(scored), "candidate_n": len(rows),
            "blocking_misses": len(misses), "candidate": candidate, "workflow": workflow,
            "independent_recompute": recomputed}


def _independent(rows, misses, costs):
    # Deliberately separate accumulator and formulas from evaluate.counts.
    tp = fp = fn = rp = rn = tn = 0
    for r in rows:
        y, a = r["label"], r["action"]
        if a == "MATCH":
            tp += y
            fp += 1 - y
        elif a == "REVIEW":
            rp += y
            rn += 1 - y
        else:
            fn += y
            tn += 1 - y
    fn += misses
    return {"TP": tp, "FP": fp, "FN": fn, "R_plus": rp, "R_minus": rn,
            "REVIEW": rp + rn, "TN_candidate": tn,
            "U": costs[0] * fp + costs[1] * fn + costs[2] * (rp + rn)}
