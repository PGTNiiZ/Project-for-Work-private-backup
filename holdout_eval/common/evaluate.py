"""ประเมินผล pipeline บน holdout พร้อม bootstrap CI

Input:
  --records  records.csv (schema กลาง) ใช้สร้าง gold
  --scores   scores.csv จาก pipeline ที่ freeze แล้ว คอลัมน์ left_id,right_id,score
             (คู่ candidate ทั้งหมดหลัง blocking ของ pipeline)
  --left / --right  ชื่อ source ฝั่งซ้าย/ขวา
  --manifest freeze_manifest.json (อ่าน threshold และเช็ก hash)

Recall คิดเทียบกับ gold ทั้งหมด รวมคู่ที่ blocking ตัดทิ้ง (นับเป็น FN)

ตัวอย่าง:
python -m common.evaluate --records tier1/out/records.csv --scores scores.csv \
    --left github --right bluesky --manifest freeze_manifest.json --out results_tier1.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from common.freeze import sha256
from common.schema import gold_pairs, read_records


DECISIONS = ("MATCH", "REVIEW", "NO_MATCH")


def has_decisions(scores: pd.DataFrame) -> bool:
    """True เมื่อ adapter ส่ง decision ที่ policy ที่ freeze แล้วตัดสินไว้ (เช่น B2/B3 ที่ใช้ name_sim band)"""
    if "decision" not in scores.columns:
        return False
    bad = set(scores["decision"].unique()) - set(DECISIONS)
    if bad:
        raise ValueError(f"decision ต้องเป็น {DECISIONS} เท่านั้น พบ {sorted(bad)}")
    return True


def predicted(scores: pd.DataFrame, threshold: float | None, include_possible: bool = False,
              possible_threshold: float | None = None) -> pd.Series:
    """mask ของคู่ที่ถือว่า merge: decision column ถ้ามี ไม่งั้นใช้ threshold บน score"""
    if has_decisions(scores):
        keep = ("MATCH", "REVIEW") if include_possible else ("MATCH",)
        return scores["decision"].isin(keep)
    thr = possible_threshold if include_possible else threshold
    if thr is None:
        raise ValueError("ไม่มี decision column จึงต้องระบุ threshold")
    return scores["score"] >= thr


def per_left_stats(scores: pd.DataFrame, gold: set, left_ids: list[str],
                   threshold: float | None, ks=(1, 10),
                   pred: pd.Series | None = None) -> pd.DataFrame:
    gold_by_left: dict[str, set] = {}
    for l, r in gold:
        gold_by_left.setdefault(l, set()).add(r)

    scores = scores.copy()
    scores["label"] = [(l, r) in gold for l, r in zip(scores.left_id, scores.right_id)]
    scores["pred"] = (pred.values if pred is not None
                      else predicted(scores, threshold).values)
    grouped = {k: g for k, g in scores.groupby("left_id")}

    rows = []
    for lid in left_ids:
        g = grouped.get(lid)
        golds = gold_by_left.get(lid, set())
        if g is None:
            tp = fp = 0
            ranked: list[str] = []
        else:
            tp = int((g.pred & g.label).sum())
            fp = int((g.pred & ~g.label).sum())
            ranked = g.sort_values("score", ascending=False).right_id.tolist()
        row = {"left_id": lid, "tp": tp, "fp": fp, "fn": len(golds) - tp,
               "has_gold": bool(golds)}
        for k in ks:
            row[f"hit@{k}"] = int(bool(golds & set(ranked[:k]))) if golds else 0
        rows.append(row)
    return pd.DataFrame(rows)


def summarize(stats: pd.DataFrame, ks=(1, 10)) -> dict:
    tp, fp, fn = stats.tp.sum(), stats.fp.sum(), stats.fn.sum()
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    out = {"precision": p, "recall": r, "f1": f1}
    with_gold = stats[stats.has_gold]
    for k in ks:
        out[f"hit@{k}"] = with_gold[f"hit@{k}"].mean() if len(with_gold) else 0.0
    return out


def bootstrap(stats: pd.DataFrame, n: int, ci: float, seed: int, ks=(1, 10)) -> dict:
    rng = np.random.default_rng(seed)
    idx = np.arange(len(stats))
    draws = [summarize(stats.iloc[rng.choice(idx, size=len(idx), replace=True)], ks)
             for _ in range(n)]
    lo, hi = (1 - ci) / 2, 1 - (1 - ci) / 2
    return {m: [float(np.quantile([d[m] for d in draws], lo)),
                float(np.quantile([d[m] for d in draws], hi))] for m in draws[0]}


def possible_block(scores: pd.DataFrame, gold: set, left_ids: list[str],
                   match_thr: float | None, possible_thr: float | None, n_boot: int,
                   seed: int) -> dict:
    """MATCH+POSSIBLE (score >= possible_thr นับเป็นการ merge) และ review rate

    review rate = สัดส่วนคู่ candidate ที่ score อยู่ใน [possible_thr, match_thr)
    ถ้ามี decision column: MATCH+POSSIBLE = MATCH หรือ REVIEW และ review rate = สัดส่วน REVIEW
    """
    if has_decisions(scores):
        pred = predicted(scores, None, include_possible=True)
        stats = per_left_stats(scores, gold, left_ids, None, pred=pred)
        in_review = scores["decision"] == "REVIEW"
        return {
            "possible_threshold": "frozen policy decisions (REVIEW = POSSIBLE_MATCH)",
            "point": summarize(stats),
            "ci95": bootstrap(stats, n_boot, 0.95, seed),
            "review_rate": float(in_review.mean()) if len(scores) else 0.0,
            "n_review": int(in_review.sum()),
        }
    if possible_thr > match_thr:
        raise ValueError("possible_threshold ต้อง <= match threshold")
    stats = per_left_stats(scores, gold, left_ids, possible_thr)
    in_review = (scores.score >= possible_thr) & (scores.score < match_thr)
    return {
        "possible_threshold": possible_thr,
        "point": summarize(stats),
        "ci95": bootstrap(stats, n_boot, 0.95, seed),
        "review_rate": float(in_review.mean()) if len(scores) else 0.0,
        "n_review": int(in_review.sum()),
    }


def check_manifest(manifest: dict) -> list[str]:
    warnings = []
    for path, digest in manifest.get("files", {}).items():
        if not Path(path).exists():
            warnings.append(f"หาไฟล์ที่ freeze ไว้ไม่เจอ: {path}")
        elif sha256(path) != digest:
            warnings.append(f"ไฟล์ถูกแก้หลัง freeze: {path}")
    return warnings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--left", required=True)
    ap.add_argument("--right", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--threshold", type=float, help="ใช้เมื่อไม่มี manifest เท่านั้น")
    ap.add_argument("--possible-threshold", type=float,
                    help="เกณฑ์ POSSIBLE_MATCH (secondary) ถ้าไม่ระบุจะอ่านจาก manifest")
    ap.add_argument("--strata", help="csv คอลัมน์ entity_id,flag(0/1) สำหรับแยก stratum")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()

    scores = pd.read_csv(args.scores, dtype={"left_id": str, "right_id": str})
    decision_mode = has_decisions(scores)
    manifest, warnings = {}, []
    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        threshold = manifest.get("threshold")
        warnings = check_manifest(manifest)
    elif args.threshold is not None or decision_mode:
        threshold = args.threshold
        warnings.append("ไม่ได้ใช้ manifest — ผลนี้ไม่นับเป็น confirmatory")
    else:
        raise SystemExit("ต้องระบุ --manifest หรือ --threshold")
    if threshold is None and not decision_mode:
        raise SystemExit("manifest ไม่มี threshold และ scores ไม่มี decision column")

    records = read_records(args.records)
    gold = gold_pairs(records, args.left, args.right)
    left_ids = records.loc[records.source == args.left, "record_id"].tolist()

    stats = per_left_stats(scores, gold, left_ids, threshold)
    point = summarize(stats)
    labels = [(l, r) in gold for l, r in zip(scores.left_id, scores.right_id)]
    point["pr_auc_candidates"] = (float(average_precision_score(labels, scores.score))
                                  if any(labels) else None)
    cand_gold = sum(labels)
    ci95 = bootstrap(stats, args.n_boot, 0.95, args.seed)
    result = {
        "threshold": threshold,
        "decision_source": "frozen policy decision column" if decision_mode else "score >= threshold",
        "n_left": len(left_ids),
        "n_gold_pairs": len(gold),
        "n_candidates": len(scores),
        "blocking_recall": cand_gold / len(gold) if gold else None,
        "point": point,
        "ci95": ci95,
        "decision_rule": manifest.get("decision_rule"),
        "warnings": warnings,
    }

    possible = args.possible_threshold
    if possible is None:
        possible = manifest.get("possible_threshold")
    if possible is not None or decision_mode:
        result["match_plus_possible"] = possible_block(
            scores, gold, left_ids, threshold, possible, args.n_boot, args.seed)

    ref, delta = manifest.get("reference_f1"), manifest.get("delta")
    if ref is not None and delta is not None:
        lo = ci95["f1"][0]
        result["decision"] = {
            "reference_f1": ref, "delta": delta, "f1_ci_lower": lo,
            "transfer_supported": bool(lo >= ref - delta),
            "f1_minus_reference": point["f1"] - ref,
            "f1_minus_reference_ci95": [ci95["f1"][0] - ref, ci95["f1"][1] - ref],
        }

    if args.strata:
        flags = pd.read_csv(args.strata, dtype=str).set_index("entity_id")["flag"]
        ent = records.set_index("record_id")["entity_id"]
        flagged = ent.loc[left_ids].map(flags).fillna("0") == "1"
        result["strata"] = {}
        for name, mask in (("flagged", flagged.values), ("unflagged", ~flagged.values)):
            sub = stats[mask]
            result["strata"][name] = {
                "n_left": int(mask.sum()),
                "point": summarize(sub) if len(sub) else None,
                "ci95": bootstrap(sub, args.n_boot, 0.95, args.seed) if len(sub) else None,
            }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    for w in warnings:
        print("คำเตือน:", w)
    print(json.dumps({"point": point, "ci95": result["ci95"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
