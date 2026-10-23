"""
Stage 5: Evaluation Harness — validation-selected threshold + test metrics

ผลิตตารางวัดผลที่ซ้ำได้ ใช้เป็นเครื่องวัดของทุก phase ถัดไป
- slice ตาม name similarity: EASY (name>=0.5) / MID (0.3-0.5) / HARD (name<0.3 & bio<0.3)
- per-platform-pair (canonical, unordered)
- overall P/R/F1/AP + FN breakdown

ใช้เป็น library ได้ (import ฟังก์ชัน) หรือรันตรงเพื่อ dump baseline
Input : pub_multi/data/train_all.parquet
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_score, recall_score, f1_score

from identity_resolution.settings import PATHS

TA = PATHS.root / "pub_multi" / "data" / "train_all.parquet"
OUTPUT_DIR = PATHS.evaluation_artifacts
NAME_COLS = ["username_jaro", "fullname_jaro", "username_token_sort", "fullname_token_sort"]
BIO_COLS = ["bio_tfidf_cosine", "bio_sbert_cosine"]


def load(path=TA):
    return pd.read_parquet(path)


def add_derived(df):
    df = df.copy()
    df["name_max"] = df[NAME_COLS].fillna(0).max(axis=1)
    df["bio_max"] = df[BIO_COLS].fillna(0).max(axis=1)
    # canonical unordered platform-pair
    df["plat_pair"] = df.apply(
        lambda r: " x ".join(sorted([str(r["platform_a"]), str(r["platform_b"])])), axis=1)
    return df


def slice_of(df):
    s = pd.Series("EASY", index=df.index)
    s[df["name_max"] < 0.5] = "MID"
    s[(df["name_max"] < 0.3) & (df["bio_max"] < 0.3)] = "HARD"
    return s


def metrics_at(y, score, thr):
    pred = (score >= thr).astype(int)
    return dict(
        precision=round(precision_score(y, pred, zero_division=0), 4),
        recall=round(recall_score(y, pred, zero_division=0), 4),
        f1=round(f1_score(y, pred, zero_division=0), 4),
        FN=int(((pred == 0) & (y == 1)).sum()),
        FP=int(((pred == 1) & (y == 0)).sum()),
    )


def threshold_sweep(df, *, split="val", score_col="probability", grid=None):
    selected = df[df["split_name"] == split]
    if selected.empty:
        raise ValueError(f"No rows found for split={split!r}")
    if grid is None:
        grid = np.round(np.arange(0.05, 0.951, 0.01), 2)
    rows = []
    labels = selected["label"].to_numpy()
    scores = selected[score_col].to_numpy()
    for threshold in grid:
        metrics = metrics_at(labels, scores, float(threshold))
        rows.append({"threshold": float(threshold), **metrics})
    return pd.DataFrame(rows)


def select_threshold(df, *, split="val", score_col="probability"):
    sweep = threshold_sweep(df, split=split, score_col=score_col)
    best = sweep.sort_values(["f1", "precision"], ascending=False).iloc[0]
    return float(best["threshold"]), sweep


def full_report(df, score_col="probability", thr=0.35, split="test"):
    d = add_derived(df)
    d = d[d.split_name == split].copy()
    d["slice"] = slice_of(d)
    y = d.label.values
    score = d[score_col].values
    rep = {"split": split, "threshold": thr, "n": int(len(d)),
           "n_pos": int((y == 1).sum()),
           "test_ap": round(float(average_precision_score(y, score)), 4),
           "overall": metrics_at(y, score, thr)}
    # per slice (recall over positives in slice)
    rep["by_slice"] = {}
    for sl in ["EASY", "MID", "HARD"]:
        m = d["slice"] == sl
        pos = m & (d.label == 1)
        if pos.sum() == 0:
            continue
        pred = (score[pos.values] >= thr).astype(int)
        rep["by_slice"][sl] = {"n_pos": int(pos.sum()),
                               "recall": round(float(pred.mean()), 4),
                               "FN": int((pred == 0).sum())}
    # per platform-pair
    rep["by_platform_pair"] = {}
    for pp, g in d.groupby("plat_pair"):
        yg = g.label.values
        sg = g[score_col].values
        pos = int((yg == 1).sum())
        if pos == 0:
            continue
        mm = metrics_at(yg, sg, thr)
        mm["n_pos"] = pos
        rep["by_platform_pair"][pp] = mm
    return rep


def print_report(rep, tag=""):
    o = rep["overall"]
    print(f"\n===== {tag}  (thr={rep['threshold']}) =====")
    print(f"AP={rep['test_ap']}  P={o['precision']}  R={o['recall']}  F1={o['f1']}  FN={o['FN']}  FP={o['FP']}")
    print("  by slice:")
    for sl, m in rep["by_slice"].items():
        print(f"    {sl:5s} n_pos={m['n_pos']:4d}  recall={m['recall']:.3f}  FN={m['FN']}")
    print("  by platform-pair:")
    for pp, m in rep["by_platform_pair"].items():
        print(f"    {pp:26s} n_pos={m['n_pos']:4d}  P={m['precision']:.3f} R={m['recall']:.3f} FN={m['FN']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 5: validation-selected model evaluation")
    parser.add_argument("--data", default=str(TA))
    parser.add_argument("--output", default=str(OUTPUT_DIR / "current_model_evaluation.json"))
    args = parser.parse_args()
    df = load(args.data)
    threshold, sweep = select_threshold(df)
    rep = full_report(df, "probability", threshold, "test")
    validation_row = sweep[sweep["threshold"] == threshold].iloc[0]
    validation_best = {key: float(validation_row[key]) for key in validation_row.index}
    result = {
        "data_path": str(args.data),
        "selection_rule": "maximize validation F1; precision breaks ties",
        "validation_best": validation_best,
        "test": rep,
    }
    print_report(rep, "Final test (threshold selected on validation)")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {output_path}")


if __name__ == "__main__":
    main()
