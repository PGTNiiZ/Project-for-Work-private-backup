"""รวมผลสาม outer seed (101/202/303) ของ method เดียว และใช้ decision rule ที่ pre-register ไว้

Primary metric = ค่าเฉลี่ย F1 (MATCH-only, end-to-end: gold ที่ blocking ตัดทิ้ง = FN) ของสาม seed
CI 95% = bootstrap ระดับ left entity โดยใช้ resample ชุดเดียวกันกับทุก seed ในแต่ละรอบ
reference_f1 / delta อ่านจาก freeze_manifest.json (resolved.decision_rule) — ไม่รับจาก command line

ตัวอย่าง:
python -m common.aggregate --records data/tier1/records.csv --left github --right bluesky \
    --manifest freeze_manifest.json --method B3 --condition PRIMARY \
    --scores 101=data/tier1/scores_B3_101_nourl.csv 202=... 303=... \
    --strata data/tier1/strata.csv --out results/tier1_B3_primary.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from common.evaluate import (check_manifest, has_decisions, per_left_stats, predicted,
                             summarize)
from common.schema import gold_pairs, read_records


def _f1(tp: np.ndarray, fp: np.ndarray, fn: np.ndarray) -> np.ndarray:
    denom = 2 * tp + fp + fn
    return np.where(denom > 0, 2 * tp / np.where(denom > 0, denom, 1), 0.0)


def seed_stats(scores: pd.DataFrame, gold: set, left_ids: list[str]) -> dict[str, pd.DataFrame]:
    if not has_decisions(scores):
        raise SystemExit("aggregate ต้องการ decision column จาก adapter (policy ที่ freeze แล้ว)")
    match = per_left_stats(scores, gold, left_ids, None, pred=predicted(scores, None))
    mp = per_left_stats(scores, gold, left_ids, None,
                        pred=predicted(scores, None, include_possible=True))
    return {"match": match, "match_plus_possible": mp}


def joint_bootstrap(per_seed: list[pd.DataFrame], n: int, seed: int) -> np.ndarray:
    """คืน array ของค่าเฉลี่ย F1 ข้าม seed ในแต่ละรอบ bootstrap"""
    rng = np.random.default_rng(seed)
    arrays = [(s.tp.to_numpy(), s.fp.to_numpy(), s.fn.to_numpy()) for s in per_seed]
    m = len(per_seed[0])
    out = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, m, size=m)
        out[i] = np.mean([_f1(tp[idx].sum(), fp[idx].sum(), fn[idx].sum()) for tp, fp, fn in arrays])
    return out


def block(per_seed: dict[int, pd.DataFrame], n_boot: int, boot_seed: int) -> dict:
    seeds = sorted(per_seed)
    points = {s: summarize(per_seed[s]) for s in seeds}
    draws = joint_bootstrap([per_seed[s] for s in seeds], n_boot, boot_seed)
    mean_f1 = float(np.mean([points[s]["f1"] for s in seeds]))
    return {"per_seed": {str(s): points[s] for s in seeds},
            "mean_f1": mean_f1,
            "mean_f1_ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
            "mean_precision": float(np.mean([points[s]["precision"] for s in seeds])),
            "mean_recall": float(np.mean([points[s]["recall"] for s in seeds]))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--left", required=True)
    ap.add_argument("--right", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--method", required=True)
    ap.add_argument("--condition", required=True, choices=["PRIMARY", "LEAKAGE_CEILING"])
    ap.add_argument("--scores", nargs="+", required=True, help="seed=path สำหรับทุก seed")
    ap.add_argument("--strata", help="csv entity_id,flag (scrubbed=1) — รายงานเป็น secondary")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--boot-seed", type=int, default=20261026)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    warnings = check_manifest(manifest)
    rule = (manifest.get("resolved") or {}).get("decision_rule") or {}
    paths = dict(item.split("=", 1) for item in args.scores)
    seeds = sorted(int(s) for s in paths)
    expected = sorted(int(s) for s in (manifest.get("resolved") or {}).get("seeds", seeds))
    if seeds != expected:
        warnings.append(f"seeds {seeds} ไม่ตรงกับ manifest {expected}")

    records = read_records(args.records)
    gold = gold_pairs(records, args.left, args.right)
    left_ids = records.loc[records.source == args.left, "record_id"].tolist()

    match, mp, review = {}, {}, {}
    for s in seeds:
        scores = pd.read_csv(paths[str(s)], dtype={"left_id": str, "right_id": str})
        st = seed_stats(scores, gold, left_ids)
        match[s], mp[s] = st["match"], st["match_plus_possible"]
        review[s] = float((scores.decision == "REVIEW").mean()) if len(scores) else 0.0

    result = {
        "method": args.method, "condition": args.condition,
        "label": "PRIMARY (external_url dropped both sides)" if args.condition == "PRIMARY"
                 else "LEAKAGE CEILING (with external_url) — secondary, not confirmatory",
        "n_left": len(left_ids), "n_gold_pairs": len(gold),
        "match_only": block(match, args.n_boot, args.boot_seed),
        "match_plus_possible": block(mp, args.n_boot, args.boot_seed),
        "review_rate": {"per_seed": {str(s): review[s] for s in seeds},
                        "mean": float(np.mean(list(review.values())))},
        "warnings": warnings,
    }

    ref, delta = rule.get("linksocial_f1"), rule.get("delta")
    if ref is not None and delta is not None:
        lo, hi = result["match_only"]["mean_f1_ci95"]
        result["decision"] = {
            "applies": args.condition == "PRIMARY" and args.method == rule.get("primary_method"),
            "linksocial_f1": ref, "delta": delta, "threshold": ref - delta,
            "holdout_mean_f1": result["match_only"]["mean_f1"], "holdout_f1_ci95_lower": lo,
            "transfer_supported": bool(lo >= ref - delta),
            "holdout_minus_linksocial": result["match_only"]["mean_f1"] - ref,
            "holdout_minus_linksocial_ci95": [lo - ref, hi - ref],
            "note": "CI reflects holdout sampling only; LinkSocial reference treated as fixed",
        }
        ref_dec = rule.get("linksocial_f_dec_secondary")
        if ref_dec is not None:
            result["decision_sensitivity_f_dec"] = {
                "label": "SECONDARY sensitivity: reference = FINAL_RESULTS decision-conditional F1 "
                         "(REVIEW positives excluded); not the pre-registered decision",
                "linksocial_f1": ref_dec, "threshold": ref_dec - delta,
                "transfer_supported": bool(lo >= ref_dec - delta),
                "holdout_minus_linksocial": result["match_only"]["mean_f1"] - ref_dec,
                "holdout_minus_linksocial_ci95": [lo - ref_dec, hi - ref_dec],
            }

    if args.strata:
        flags = pd.read_csv(args.strata, dtype=str).set_index("entity_id")["flag"]
        ent = records.set_index("record_id")["entity_id"]
        flagged = (ent.loc[left_ids].map(flags).fillna("0") == "1").to_numpy()
        result["strata_secondary"] = {}
        for name, mask in (("scrubbed", flagged), ("not_scrubbed", ~flagged)):
            if mask.sum() == 0:
                result["strata_secondary"][name] = {"n_left": 0}
                continue
            sub = {s: match[s][mask].reset_index(drop=True) for s in seeds}
            result["strata_secondary"][name] = {"n_left": int(mask.sum()),
                                                **block(sub, args.n_boot, args.boot_seed)}

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for w in warnings:
        print("คำเตือน:", w)
    print(json.dumps({k: result[k] for k in ("method", "condition", "match_only")}, ensure_ascii=False,
                     indent=2))
    if "decision" in result:
        print(json.dumps(result["decision"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
