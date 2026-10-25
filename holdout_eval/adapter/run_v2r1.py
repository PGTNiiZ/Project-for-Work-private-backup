"""Adapter: ให้คะแนน holdout records.csv ด้วย pipeline ICSEC authoritative_run_v2r1 ที่ freeze แล้ว

ใช้โค้ดของ V2R1 โดยตรง (ไม่ redesign):
  candidate generation  src/identity_resolution/workflows/full_candidate.py
                        (exact tier: username / external URL ตรงกัน → AUTO_EXACT = MATCH;
                         blocking keys: username_prefix3, fullname_prefix3, external_domain)
  features              experiments/icsec_final/authoritative_run_v2/features.py (17 handcrafted)
                        + bert_cos (all-MiniLM-L6-v2 @ revision ที่ freeze, text = fullName + bio + location)
  model / calibrator    authoritative_run_v2r1/scientific_outputs/outer_<seed>/models/GB-1{7,8}_*.pkl
  policy                authoritative_run_v2r1/scientific_outputs/outer_<seed>/policies.json
                        (B0/B1 = two-threshold; B2/B3 = four-parameter with name_sim band)

ไม่ใช้ label ของ holdout ใด ๆ — อ่านเฉพาะ username/full_name/bio/location/external_url/source

ตัวอย่าง (รันจากโฟลเดอร์ holdout_eval):
python -m adapter.run_v2r1 --records data/tier1/records.csv --left github --right bluesky \
    --seed 101 --method B3 --drop-external-url --out data/tier1/scores_B3_101_nourl.csv
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from experiments.icsec_final.authoritative_run_v2.features import (  # noqa: E402
    FEATURE17_COLUMNS, FEATURE18_COLUMNS, build_handcrafted_features,
)
from experiments.icsec_final.authoritative_run_v2.policies import (  # noqa: E402
    b0_decide, decide_four_parameter,
)
from identity_resolution.workflows import full_candidate as fc  # noqa: E402

V2R1_OUT = REPO / "experiments" / "icsec_final" / "authoritative_run_v2r1" / "scientific_outputs"
MINILM_ID = "sentence-transformers/all-MiniLM-L6-v2"
MINILM_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"  # v2r1_manifest.json#minilm
METHODS = ("GB17_B0", "B0", "B1", "B2", "B3")
SEEDS = (101, 202, 303)
CODE = {0: "NO_MATCH", 1: "REVIEW", 2: "MATCH"}


def clean_url(url: str) -> str:
    """ประมาณการ externalUrl_clean ของ LinkSocial (ใช้เฉพาะเงื่อนไข LEAKAGE CEILING)"""
    u = fc.lower_text(url)
    if not u or u == "nan":
        return ""
    u = u.split("://", 1)[-1]
    u = u.removeprefix("www.")
    return u.rstrip("/")


def url_domain(url: str) -> str:
    u = clean_url(url)
    if not u:
        return ""
    return urlparse("https://" + u).netloc.lower()


def to_profiles(records: pd.DataFrame, drop_external_url: bool) -> pd.DataFrame:
    """records (schema กลาง) → ตารางโปรไฟล์แบบที่ full_candidate/features ใช้"""
    df = pd.DataFrame({
        "profile_row_id": np.arange(len(records), dtype="int64"),
        "record_id": records["record_id"].values,
        "platform": records["source"].map(fc.lower_text).values,
        "userName": records["username"].values,
        "fullName": records["full_name"].values,
        "bio": records["bio"].values,
        "location": records["location"].values,
    })
    urls = pd.Series([""] * len(records)) if drop_external_url else records["external_url"].reset_index(drop=True)
    df["externalUrl_clean"] = urls.map(clean_url).values
    df["external_domain"] = urls.map(url_domain).map(
        lambda x: "" if (not x or x in fc.GENERIC_EXTERNAL_DOMAINS) else x).values
    # เหมือน full_candidate.load_profiles
    df["userName_norm"] = df["userName"].map(fc.lower_text)
    df["fullName_norm"] = df["fullName"].map(fc.lower_text)
    df["bio_norm"] = df["bio"].map(fc.lower_text)
    df["username_prefix3"] = df["userName"].map(fc.prefix3)
    df["fullname_prefix3"] = df["fullName"].map(fc.prefix3)
    return df


def unpack(key: int) -> tuple[int, int]:
    return key >> 32, key & 0xFFFFFFFF


def minilm_cos(profiles: pd.DataFrame, pairs: pd.DataFrame) -> np.ndarray:
    from sentence_transformers import SentenceTransformer
    texts = (profiles["fullName"].fillna("").astype(str).str.strip() + " "
             + profiles["bio"].fillna("").astype(str).str.strip() + " "
             + profiles["location"].fillna("").astype(str).str.strip()).str.strip().replace("", "[empty]")
    model = SentenceTransformer(MINILM_ID, revision=MINILM_REVISION, local_files_only=True)
    emb = model.encode(texts.tolist(), normalize_embeddings=True, convert_to_numpy=True,
                       show_progress_bar=False).astype("float32")
    a = pairs["profile_row_id_a"].to_numpy(int)
    b = pairs["profile_row_id_b"].to_numpy(int)
    return np.einsum("ij,ij->i", emb[a], emb[b]).astype("float32")


def load_frozen(seed: int, method: str):
    out = V2R1_OUT / f"outer_{seed}"
    name = "GB-17" if method == "GB17_B0" else "GB-18"
    with (out / "models" / f"{name}_model.pkl").open("rb") as f:
        model = pickle.load(f)
    with (out / "models" / f"{name}_calibrator.pkl").open("rb") as f:
        calibrator = pickle.load(f)
    params = json.loads((out / "policies.json").read_text())["parameters"]
    policy = params["B0"] if method == "GB17_B0" else params[method]
    return name, model, calibrator, tuple(float(x) for x in policy)


def availability(records: pd.DataFrame, left: str, right: str, drop_url: bool) -> dict:
    """aggregate เท่านั้น: สัดส่วนช่องที่ไม่ว่างต่อ source"""
    out = {}
    for src in (left, right):
        sub = records[records.source == src]
        out[src] = {c: round(float((sub[c].str.len() > 0).mean()), 4) if len(sub) else None
                    for c in ("username", "full_name", "bio", "location", "external_url", "profile_pic_url")}
    mismatch = []
    for c, feats in (("location", "location_jaro/location_exact/both_have_location"),
                     ("bio", "bio_jaccard/bio_len_ratio/both_have_bio"),
                     ("full_name", "fullname_*")):
        for src in (left, right):
            if out[src][c] == 0.0:
                mismatch.append(f"{c} empty for every {src} record -> {feats} carry no signal")
    if drop_url:
        mismatch.append("external_url dropped on both sides (PRIMARY): external-URL exact tier and "
                        "external_domain blocking key inactive")
    mismatch.append("profile images not used by GB-17/GB-18 (no image feature in V2R1)")
    return {"non_empty_fraction": out, "feature_availability_mismatch": mismatch}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--left", required=True)
    ap.add_argument("--right", required=True)
    ap.add_argument("--seed", type=int, choices=SEEDS, required=True)
    ap.add_argument("--method", choices=METHODS, required=True)
    ap.add_argument("--drop-external-url", action="store_true",
                    help="PRIMARY: ลบ external_url ทั้งสองฝั่ง (gold สร้างจาก GitHub social link)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    records = pd.read_csv(args.records, dtype=str, keep_default_na=False)
    records = records[records.source.isin([args.left, args.right])].reset_index(drop=True)
    profiles = to_profiles(records, args.drop_external_url)

    exact, exact_breakdown = fc.build_exact_match_pairs(profiles)
    scored, block_breakdown = fc.build_candidate_pairs(profiles, exact)

    name, model, calibrator, policy = load_frozen(args.seed, args.method)
    rows = []
    if scored:
        pairs = pd.DataFrame([unpack(k) for k in sorted(scored)],
                             columns=["profile_row_id_a", "profile_row_id_b"])
        feats = build_handcrafted_features(pairs, profiles)
        feats["bert_cos"] = minilm_cos(profiles, feats)
        cols = FEATURE17_COLUMNS if name == "GB-17" else FEATURE18_COLUMNS
        x = feats[cols].to_numpy(np.float32)
        p = calibrator.predict(model.predict_proba(x)[:, 1])
        if args.method in ("B2", "B3"):
            d = decide_four_parameter(p, feats["name_sim"].to_numpy(), policy)
        else:
            d = b0_decide(p, policy)
        for a, b, prob, dec, ns in zip(feats.profile_row_id_a, feats.profile_row_id_b, p, d,
                                       feats.name_sim):
            rows.append((int(a), int(b), float(prob), CODE[int(dec)], "MODEL_SCORED", float(ns)))
    for k in sorted(exact):
        a, b = unpack(k)
        rows.append((a, b, 1.0, "MATCH", "AUTO_EXACT", np.nan))

    src = profiles.set_index("profile_row_id")["platform"]
    rid = profiles.set_index("profile_row_id")["record_id"]
    left = fc.lower_text(args.left)
    out_rows = []
    for a, b, prob, dec, ptype, ns in rows:
        la, lb = (a, b) if src[a] == left else (b, a)
        out_rows.append({"left_id": rid[la], "right_id": rid[lb], "score": prob,
                         "decision": dec, "pair_type": ptype, "name_sim": ns})
    scores = pd.DataFrame(out_rows, columns=["left_id", "right_id", "score", "decision",
                                             "pair_type", "name_sim"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.out, index=False)

    meta = {
        "pipeline": "authoritative_run_v2r1", "seed": args.seed, "method": args.method,
        "model": name, "policy": policy, "condition": "PRIMARY (no external_url)" if args.drop_external_url
        else "LEAKAGE CEILING (with external_url)",
        "n_records": int(len(records)), "n_candidates": int(len(scores)),
        "exact_tier_breakdown": exact_breakdown, "blocking_key_breakdown": block_breakdown,
        "decision_counts": scores["decision"].value_counts().to_dict(),
        **availability(records, args.left, args.right, args.drop_external_url),
    }
    Path(args.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({k: meta[k] for k in ("method", "seed", "condition", "n_candidates",
                                           "decision_counts")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
