#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
identity_resolution_pipeline.py
================================
ไฟล์เดียวสำหรับรันการทดลองทั้งหมดของโครงงาน
"การศึกษาทดลองเชิงควบคุมเพื่อปรับปรุงนโยบายการตัดสินใจในการเชื่อมโยงตัวตนข้ามแพลตฟอร์ม"
ตามโปรโตคอล Research V2 และวงจร CRISP-DM ตั้งแต่นำเข้าข้อมูลจนถึง deploy

ขั้นตอน (ตรงกับหัวข้อในเล่ม)
  0. Setup              ค่าตั้ง, seed, โฟลเดอร์ผลลัพธ์
  1. Data ingestion     อ่าน LinkSocial (CSV ที่รวมแล้ว หรือโฟลเดอร์ JSON) หรือข้อมูลจำลอง (--demo)
  2. Data understanding EDA + รูป
  3. Data preparation   ปรับมาตรฐาน, ป้ายกำกับจาก user_folder, แบ่ง 5 fold แยกตามบุคคล
  4. Blocking (H5)      B0 / sparse TF-IDF / dense / hybrid union / hybrid RRF ที่งบเท่ากัน
  5. Features           F-LEX 35, F-SEM 6, fusion 41 (TF-IDF ฟิตบน fold ฝึกเท่านั้น)
  6. Modeling (H1-H3)   กฎที่จูนแล้ว, LR, GBDT (TPE), single-group, ablation, learning curve
  7. Calibration        Platt vs isotonic เลือกด้วย Brier แบบ cross-fit
  8. Decision policies  11 นโยบาย (fixed, val-F1, closed-cost, R0, stage18, Chow, three-way,
                        กฎ 4 พารามิเตอร์ค้นด้วย random/Sobol/TPE/GA ที่งบเท่ากัน) (H4)
  9. Freeze             บันทึก artifact + SHA-256 ก่อนเปิดชุดทดสอบ
 10. Final evaluation   เปิด fold ทดสอบครั้งเดียว, bootstrap ระดับบุคคล + Holm + TOST, factorial 2x2x2
 11. Visualization      รูปเปรียบเทียบทั้งหมดใน <out>/figures
 12. Deploy            บันเดิลโมเดล + คลาส IdentityResolver + REST API (stdlib) + CLI predict

วิธีใช้
  # ทดลองเร็วด้วยข้อมูลจำลอง (ไม่ต้องมีข้อมูลจริง)
  python identity_resolution_pipeline.py run --demo --out runs/demo --quick

  # ข้อมูลจริง: CSV ที่รวมโปรไฟล์แล้ว (เช่น merged_profiles.csv)
  python identity_resolution_pipeline.py run --data data/merged_profiles.csv --out runs/v2

  # ค่าตามโปรโตคอลในเล่ม (ช้า: GBDT 200 ค่าตั้ง, bootstrap 10,000, นโยบาย 2,048 x 10 seed)
  python identity_resolution_pipeline.py run --data data/merged_profiles.csv --out runs/v2_full --paper

  # deploy
  python identity_resolution_pipeline.py predict --bundle runs/v2/deploy/bundle.joblib --input new.csv --output decisions.csv
  python identity_resolution_pipeline.py serve   --bundle runs/v2/deploy/bundle.joblib --port 8000

ไลบรารี
  จำเป็น : numpy pandas scipy scikit-learn matplotlib joblib
  แนะนำ  : rapidfuzz (เร็วขึ้นมาก), optuna (TPE จริง; ถ้าไม่มีจะใช้ random search แทนและบันทึกไว้)
  ทางเลือก: sentence-transformers (MiniLM สำหรับ F-SEM, dense blocking, hybrid; ถ้าไม่มีจะข้าม H3/H5)

หมายเหตุสำคัญ
  * ทุกผลบน LinkSocial เป็น EXPLORATORY (ข้อมูลเคยถูกใช้มาก่อน ไม่ผ่าน G5)
  * ต้นทุน 2:1:0.1 (รวมผิด:พลาด:ส่งตรวจ) เป็นสมมติฐาน
  * ไฟล์นี้เขียนใหม่ให้ทำซ้ำโปรโตคอล V2 ในไฟล์เดียว ตัวเลขอาจต่างจากรันต้นฉบับเล็กน้อย
    (เช่น ขอบเขต search space ของ GBDT/GA, กฎ stage18 ที่เป็นการประมาณ) ให้ใช้ตัวเลขในเล่มจากรันต้นฉบับ
"""

# %% ======================================================================
# 0. SETUP
# =========================================================================
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
import warnings
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import qmc
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

try:  # string similarity (fast path)
    from rapidfuzz.distance import JaroWinkler as _RF_JW
    from rapidfuzz.distance import Levenshtein as _RF_LEV

    HAS_RAPIDFUZZ = True
except Exception:  # pragma: no cover
    HAS_RAPIDFUZZ = False

try:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except Exception:  # pragma: no cover
    HAS_OPTUNA = False

FIELDS = ["username", "fullname", "bio", "location", "links"]
LEX_MEASURES = ["exact", "jw", "nlev", "jacc", "tfidf", "both", "onemiss"]
PLATFORMS = ["twitter", "googleplus", "instagram"]
LOG = []


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.append(line)


@dataclass
class Config:
    out: str = "runs/demo"
    data: str | None = None
    demo: bool = False
    seed: int = 42
    n_folds: int = 5
    test_fold: int = 4
    # costs: false merge : missed pair : review (ASSUMPTION)
    c_fp: float = 2.0
    c_fn: float = 1.0
    c_r: float = 0.1
    # blocking
    b0_max_block: int = 400
    knn_k: int = 50
    # modeling
    gbdt_trials: int = 30
    model_seeds: tuple = (11, 23, 42, 71, 101)
    rule_draws: int = 300
    run_ablations: bool = True
    run_learning_curve: bool = True
    # semantic
    use_semantic: bool = True
    st_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # policies
    policy_budget: int = 512
    policy_seeds: tuple = (0, 1, 2)
    ga_pop: int = 32
    # statistics
    bootstrap_B: int = 1000
    sesoi: dict = field(default_factory=lambda: {"H1": 0.02, "H2": 0.02, "H3": 0.01, "H4": 0.05, "H5": 0.02})
    # deploy
    deploy_knn_k: int = 20


def set_seed(seed: int) -> np.random.Generator:
    np.random.seed(seed)
    return np.random.default_rng(seed)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# %% ======================================================================
# 1. DATA INGESTION
# =========================================================================
COLUMN_ALIASES = {
    "username": ["username", "userName", "user_name", "handle"],
    "fullname": ["fullname", "fullName", "full_name", "name", "displayName"],
    "bio": ["bio", "description", "about"],
    "location": ["location", "loc"],
    "externalurl": ["externalUrl", "externalurl", "url", "website", "links"],
    "platform": ["platform", "site"],
    "user_folder": ["user_folder", "entity", "entity_id", "userFolder"],
}


def _pick(df: pd.DataFrame, key: str):
    lower = {c.lower(): c for c in df.columns}
    for a in COLUMN_ALIASES[key]:
        if a in df.columns:
            return df[a]
        if a.lower() in lower:
            return df[lower[a.lower()]]
    return pd.Series([""] * len(df), index=df.index)


def _platform_from_text(s: str) -> str:
    s = str(s).lower()
    if "twitter" in s or s in {"tw", "x"}:
        return "twitter"
    if "insta" in s or s == "ig":
        return "instagram"
    if "google" in s or "gplus" in s or "plus" in s or s == "g+":
        return "googleplus"
    return s


def load_csv(path: str) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    df = pd.DataFrame({
        "username": _pick(raw, "username"),
        "fullname": _pick(raw, "fullname"),
        "bio": _pick(raw, "bio"),
        "location": _pick(raw, "location"),
        "externalurl": _pick(raw, "externalurl"),
        "platform": _pick(raw, "platform").map(_platform_from_text),
        "user_folder": _pick(raw, "user_folder"),
    })
    return df


def load_json_dir(path: str, user_level: int = 1) -> pd.DataFrame:
    """อ่านทุกไฟล์ .json ใต้โฟลเดอร์ แพลตฟอร์มอนุมานจากชื่อ path, user_folder = ชื่อโฟลเดอร์ระดับ user_level เหนือไฟล์"""
    rows = []
    for p in Path(path).rglob("*.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        objs = obj if isinstance(obj, list) else [obj]
        plat = _platform_from_text(str(p))
        user = p.parents[user_level - 1].name if len(p.parents) >= user_level else ""
        for o in objs:
            if not isinstance(o, dict):
                continue
            rows.append({
                "username": o.get("userName", o.get("username", "")) or "",
                "fullname": o.get("fullName", o.get("fullname", o.get("name", ""))) or "",
                "bio": o.get("bio", o.get("description", "")) or "",
                "location": o.get("location", "") or "",
                "externalurl": o.get("externalUrl", o.get("url", "")) or "",
                "platform": plat,
                "user_folder": user,
            })
    return pd.DataFrame(rows)


def make_demo(n_entities: int = 900, seed: int = 7) -> pd.DataFrame:
    """ข้อมูลจำลองที่มีโครงสร้างคล้าย LinkSocial (สำหรับทดสอบว่าโค้ดรันได้เท่านั้น)"""
    rng = np.random.default_rng(seed)
    first = ["john", "maria", "somchai", "anna", "david", "lucas", "emma", "noah", "olivia", "liam", "mia",
             "ava", "ethan", "sophia", "mason", "isabella", "logan", "chloe", "james", "nina", "kanya", "arthit"]
    last = ["smith", "garcia", "wong", "lee", "brown", "silva", "jones", "miller", "davis", "kim", "tan",
            "nguyen", "chen", "lopez", "martin", "clark", "hall", "young", "king", "wright", "srisuk", "boonmee"]
    topics = ["designer", "photographer", "developer", "travel lover", "coffee addict", "musician", "runner",
              "teacher", "student", "foodie", "gamer", "writer", "data scientist", "artist", "entrepreneur"]
    cities = ["new york", "bangkok", "london", "paris", "san francisco", "tokyo", "berlin", "sydney", ""]
    domains = ["github.com", "medium.com", "linkedin.com/in", "behance.net", "about.me", "youtube.com"]
    rows = []
    for e in range(n_entities):
        f, l = rng.choice(first), rng.choice(last)
        base = rng.choice([f + l, f + "_" + l, f[0] + l, f + l[:3], f + str(rng.integers(1, 99))])
        topic, city = rng.choice(topics), rng.choice(cities)
        site = f"{rng.choice(domains)}/{base}" if rng.random() < 0.45 else ""
        k = rng.choice([1, 2, 2, 3, 3])
        plats = rng.choice(PLATFORMS, size=k, replace=False)
        for p in plats:
            u = base
            r = rng.random()
            if r < 0.25:
                u = base + str(rng.integers(0, 9))
            elif r < 0.35:
                u = rng.choice(first) + rng.choice(last)  # changed handle
            fn = f"{f} {l}" if rng.random() > 0.15 else (f if rng.random() < 0.5 else "")
            bio = f"{topic} from {city}" if rng.random() < 0.6 else (rng.choice(topics) if rng.random() < 0.5 else "")
            loc = city if rng.random() < 0.5 else ""
            url = site if rng.random() < 0.7 else ""
            rows.append({"username": u, "fullname": fn.title(), "bio": bio, "location": loc,
                         "externalurl": url, "platform": p, "user_folder": f"u{e:05d}"})
    df = pd.DataFrame(rows)
    df.loc[rng.choice(len(df), 3, replace=False), "user_folder"] = ""  # mimic 3 quarantined rows
    return df


# %% ======================================================================
# 3. DATA PREPARATION (normalization, labels, entity-disjoint folds)
# =========================================================================
URL_RE = re.compile(r"(https?://\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|io|me|co|tv|ly)\S*)", re.I)
_KEEP_PUNCT = set("@#./:-_")


def _strip_symbols(s: str) -> str:
    # keep letters, combining marks (Thai vowels/tone marks), digits and whitespace; drop emoji/symbols
    return "".join(c if (unicodedata.category(c)[0] in "LMN" or c.isspace() or c in _KEEP_PUNCT) else " " for c in s)


def norm_text(s: str) -> str:
    s = str(s or "").lower().strip()
    s = _strip_symbols(s)
    return re.sub(r"\s+", " ", s).strip()


def norm_username(s: str) -> str:
    s = norm_text(s).lstrip("@")
    s = re.sub(r"([._\-])\1+", r"\1", s)
    return s.replace(" ", "")


def norm_url(s: str) -> str:
    s = str(s or "").lower().strip()
    s = re.sub(r"^https?:/*", "", s)
    s = re.sub(r"^www\.", "", s)
    s = s.split("?")[0].split("#")[0].rstrip("/")
    return s


def prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    stats = {"input_rows": int(len(df))}
    df = df.copy()
    for c in ["username", "fullname", "bio", "location", "externalurl", "platform", "user_folder"]:
        df[c] = df[c].fillna("").astype(str)
    df["platform"] = df["platform"].map(_platform_from_text)
    bad = (df["user_folder"].str.strip() == "")
    stats["quarantined_rows"] = int(bad.sum())
    df = df[~bad].reset_index(drop=True)
    df["username"] = df["username"].map(norm_username)
    df["fullname"] = df["fullname"].map(norm_text)
    df["bio_raw"] = df["bio"]
    df["bio"] = df["bio"].map(lambda s: norm_text(URL_RE.sub(" ", str(s))))
    df["location"] = df["location"].map(norm_text)
    bio_urls = df["bio_raw"].map(lambda s: " ".join(norm_url(u) for u in URL_RE.findall(str(s))))
    df["links"] = (df["externalurl"].map(norm_url) + " " + bio_urls).str.strip()
    df["domain"] = df["links"].map(lambda s: s.split("/")[0] if s else "")
    df["pid"] = np.arange(len(df))
    df["entity"] = pd.factorize(df["user_folder"])[0]
    stats["eligible_rows"] = int(len(df))
    stats["distinct_entities"] = int(df["entity"].nunique())
    stats["max_group_size"] = int(df.groupby("entity").size().max())
    stats["platform_counts"] = df["platform"].value_counts().to_dict()
    return df, stats


def assign_folds(df: pd.DataFrame, k: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ents = np.arange(df["entity"].max() + 1)
    rng.shuffle(ents)
    fold_of = np.empty(len(ents), dtype=int)
    fold_of[ents] = np.arange(len(ents)) % k
    df = df.copy()
    df["fold"] = fold_of[df["entity"].values]
    return df


def pair_key(a, b, n):
    a, b = np.minimum(a, b), np.maximum(a, b)
    return a.astype(np.int64) * n + b.astype(np.int64)


def ground_truth(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, g in df.groupby("entity"):
        if len(g) < 2:
            continue
        p = g["pid"].values
        pl = g["platform"].values
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                if pl[i] != pl[j]:
                    rows.append((min(p[i], p[j]), max(p[i], p[j])))
    gt = pd.DataFrame(rows, columns=["a", "b"])
    gt["fold"] = df["fold"].values[gt["a"].values]
    gt["entity"] = df["entity"].values[gt["a"].values]
    return gt


def n_cross_pairs(dff: pd.DataFrame) -> int:
    c = dff["platform"].value_counts().values
    return int((c.sum() ** 2 - (c ** 2).sum()) // 2)


# %% ======================================================================
# 4. BLOCKING
# =========================================================================
def profile_text(df: pd.DataFrame) -> pd.Series:
    return (df["username"] + " " + df["fullname"] + " " + df["bio"] + " " + df["location"] + " " + df["links"]).str.strip()


def block_b0(dff: pd.DataFrame, max_block: int) -> np.ndarray:
    """B0: คีย์ 3 อักษรแรกของ username / fullname และโดเมนลิงก์ (คู่ข้ามแพลตฟอร์ม)"""
    keys = defaultdict(list)
    for pid, u, f, d, pl in dff[["pid", "username", "fullname", "domain", "platform"]].itertuples(index=False):
        if len(u) >= 3:
            keys["u:" + u[:3]].append((pid, pl))
        if len(f) >= 3:
            keys["f:" + f.replace(" ", "")[:3]].append((pid, pl))
        if d and d not in {"twitter.com", "instagram.com", "facebook.com", "plus.google.com"}:
            keys["d:" + d].append((pid, pl))
    out = set()
    for members in keys.values():
        if len(members) < 2 or len(members) > max_block:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if members[i][1] != members[j][1]:
                    a, b = members[i][0], members[j][0]
                    out.add((min(a, b), max(a, b)))
    if not out:
        return np.zeros((0, 2), dtype=np.int64)
    return np.array(sorted(out), dtype=np.int64)


def knn_scored_pairs(dff: pd.DataFrame, X, k: int) -> pd.DataFrame:
    """คู่ข้ามแพลตฟอร์มจากเพื่อนบ้านใกล้ที่สุด k ตัวทั้งสองทิศ พร้อมคะแนน cosine"""
    recs = []
    pids = dff["pid"].values
    plats = dff["platform"].values
    for i, p in enumerate(PLATFORMS):
        for q in PLATFORMS[i + 1:]:
            ip, iq = np.where(plats == p)[0], np.where(plats == q)[0]
            if len(ip) == 0 or len(iq) == 0:
                continue
            S = X[ip] @ X[iq].T
            S = S.toarray() if sparse.issparse(S) else np.asarray(S)
            kk = min(k, S.shape[1])
            top_r = np.argpartition(-S, kk - 1, axis=1)[:, :kk]
            rr = np.repeat(np.arange(S.shape[0]), kk)
            cc = top_r.ravel()
            kk2 = min(k, S.shape[0])
            top_c = np.argpartition(-S, kk2 - 1, axis=0)[:kk2, :]
            rr2 = top_c.ravel()
            cc2 = np.tile(np.arange(S.shape[1]), kk2)
            r_all = np.concatenate([rr, rr2])
            c_all = np.concatenate([cc, cc2])
            a, b = pids[ip[r_all]], pids[iq[c_all]]
            recs.append(pd.DataFrame({"a": np.minimum(a, b), "b": np.maximum(a, b), "score": S[r_all, c_all]}))
    if not recs:
        return pd.DataFrame(columns=["a", "b", "score"])
    out = pd.concat(recs).drop_duplicates(["a", "b"])
    return out.sort_values("score", ascending=False, kind="mergesort").reset_index(drop=True)


def take_budget(ranked: pd.DataFrame, budget: int) -> np.ndarray:
    return ranked[["a", "b"]].values[:budget].astype(np.int64)


def rrf(r1: pd.DataFrame, r2: pd.DataFrame, k: int = 60) -> pd.DataFrame:
    a = r1[["a", "b"]].copy()
    a["s"] = 1.0 / (k + np.arange(1, len(a) + 1))
    b = r2[["a", "b"]].copy()
    b["s"] = 1.0 / (k + np.arange(1, len(b) + 1))
    m = pd.concat([a, b]).groupby(["a", "b"], as_index=False)["s"].sum()
    return m.sort_values("s", ascending=False, kind="mergesort").rename(columns={"s": "score"}).reset_index(drop=True)


def union_lists(r1: pd.DataFrame, r2: pd.DataFrame) -> pd.DataFrame:
    """union แบบสลับกันจากสองรายการ (ผลัดกันหยิบ) ตัดซ้ำ"""
    n = max(len(r1), len(r2))
    a = r1[["a", "b"]].copy(); a["o"] = np.arange(len(a)) * 2
    b = r2[["a", "b"]].copy(); b["o"] = np.arange(len(b)) * 2 + 1
    m = pd.concat([a, b]).sort_values("o").drop_duplicates(["a", "b"])
    return m.rename(columns={"o": "score"}).reset_index(drop=True)


class Embedder:
    """MiniLM แบบตรึง (sentence-transformers) ถ้าไม่มีไลบรารีจะ unavailable"""

    def __init__(self, name: str, enabled: bool):
        self.ok = False
        self.name = name
        if not enabled:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(name)
            self.ok = True
        except Exception as e:  # pragma: no cover
            log(f"sentence-transformers unavailable ({type(e).__name__}); F-SEM, dense and hybrid will be skipped")

    def encode(self, texts) -> np.ndarray:
        texts = [t if t else "" for t in texts]
        v = self.model.encode(texts, batch_size=256, show_progress_bar=False, normalize_embeddings=True)
        v[np.array([not t for t in texts])] = 0.0
        return v.astype(np.float32)


# %% ======================================================================
# 5. FEATURES (F-LEX 35, F-SEM 6)
# =========================================================================
def _jw_py(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    l1, l2 = len(s1), len(s2)
    md = max(0, max(l1, l2) // 2 - 1)
    m1, m2 = [False] * l1, [False] * l2
    m = 0
    for i, c in enumerate(s1):
        for j in range(max(0, i - md), min(l2, i + md + 1)):
            if not m2[j] and s2[j] == c:
                m1[i] = m2[j] = True
                m += 1
                break
    if m == 0:
        return 0.0
    t, k = 0, 0
    for i in range(l1):
        if m1[i]:
            while not m2[k]:
                k += 1
            if s1[i] != s2[k]:
                t += 1
            k += 1
    jaro = (m / l1 + m / l2 + (m - t / 2) / m) / 3
    pre = 0
    for a, b in zip(s1[:4], s2[:4]):
        if a != b:
            break
        pre += 1
    return jaro + pre * 0.1 * (1 - jaro)


def _nlev_py(a: str, b: str) -> float:
    if not a and not b:
        return 0.0
    if a == b:
        return 1.0
    a, b = a[:200], b[:200]
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1.0 - prev[-1] / max(len(a), len(b), 1)


def string_sims(sa: np.ndarray, sb: np.ndarray):
    n = len(sa)
    jw = np.zeros(n, np.float32)
    lv = np.zeros(n, np.float32)
    if HAS_RAPIDFUZZ:
        for i in range(n):
            x, y = sa[i], sb[i]
            if x and y:
                jw[i] = _RF_JW.normalized_similarity(x, y)
                lv[i] = _RF_LEV.normalized_similarity(x, y)
    else:
        for i in range(n):
            x, y = sa[i], sb[i]
            if x and y:
                jw[i] = _jw_py(x, y)
                lv[i] = _nlev_py(x, y)
    return jw, lv


def token_jaccard(sa: np.ndarray, sb: np.ndarray) -> np.ndarray:
    out = np.zeros(len(sa), np.float32)
    for i in range(len(sa)):
        if sa[i] and sb[i]:
            A, B = set(re.split(r"[\s/._\-]+", sa[i])) - {""}, set(re.split(r"[\s/._\-]+", sb[i])) - {""}
            if A or B:
                out[i] = len(A & B) / len(A | B)
    return out


def static_features(df: pd.DataFrame, pairs: np.ndarray, emb: dict | None) -> pd.DataFrame:
    """คุณลักษณะที่ไม่ต้องฟิต (ทุกค่ายกเว้น tfidf) + F-SEM ถ้ามี"""
    out = {}
    a, b = pairs[:, 0], pairs[:, 1]
    for f in FIELDS:
        sa, sb = df[f].values[a], df[f].values[b]
        pa, pb = sa != "", sb != ""
        both = (pa & pb)
        out[f + "_exact"] = ((sa == sb) & both).astype(np.float32)
        jw, lv = string_sims(sa, sb)
        out[f + "_jw"], out[f + "_nlev"] = jw, lv
        out[f + "_jacc"] = token_jaccard(sa, sb)
        out[f + "_both"] = both.astype(np.float32)
        out[f + "_onemiss"] = (pa ^ pb).astype(np.float32)
    if emb is not None:
        for f in ["fullname", "bio"]:
            E = emb[f]
            sa, sb = df[f].values[a], df[f].values[b]
            pa, pb = sa != "", sb != ""
            out["sem_" + f + "_cos"] = np.where(pa & pb, (E[a] * E[b]).sum(1), 0).astype(np.float32)
            out["sem_" + f + "_both"] = (pa & pb).astype(np.float32)
            out["sem_" + f + "_onemiss"] = (pa ^ pb).astype(np.float32)
    return pd.DataFrame(out)


def fit_field_vectorizers(df_fit: pd.DataFrame) -> dict:
    vecs = {}
    for f in FIELDS:
        texts = df_fit[f].values
        texts = texts[texts != ""]
        if f == "bio":
            v = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True)
        else:
            v = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, sublinear_tf=True)
        v.fit(texts if len(texts) else ["empty"])
        vecs[f] = v
    return vecs


def tfidf_features(df: pd.DataFrame, pairs: np.ndarray, vecs: dict) -> pd.DataFrame:
    out = {}
    a, b = pairs[:, 0], pairs[:, 1]
    for f in FIELDS:
        X = vecs[f].transform(df[f].values)
        out[f + "_tfidf"] = np.asarray(X[a].multiply(X[b]).sum(1)).ravel().astype(np.float32)
    return pd.DataFrame(out)


LEX_COLS = [f"{f}_{m}" for f in FIELDS for m in LEX_MEASURES]
SEM_COLS = [f"sem_{f}_{m}" for f in ["fullname", "bio"] for m in ["cos", "both", "onemiss"]]


def group_cols(cols: list, fieldname: str) -> list:
    return [c for c in cols if c.startswith(fieldname + "_") or c.startswith("sem_" + fieldname + "_")]


# %% ======================================================================
# 6. MODELING helpers
# =========================================================================
def gbdt(params: dict, seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(random_state=seed, early_stopping=False, **params)


def sample_gbdt_params(rng: np.random.Generator) -> dict:
    return {
        "learning_rate": float(np.exp(rng.uniform(np.log(0.02), np.log(0.3)))),
        "max_iter": int(rng.integers(100, 601)),
        "max_leaf_nodes": int(rng.integers(15, 128)),
        "min_samples_leaf": int(rng.integers(20, 201)),
        "l2_regularization": float(np.exp(rng.uniform(np.log(1e-6), np.log(1.0)))),
    }


def tune_gbdt(eval_fn, n_trials: int, seed: int) -> tuple[dict, float, str]:
    """ค้นค่าตั้ง GBDT ด้วย TPE (optuna) หรือ random search ถ้าไม่มี optuna"""
    if HAS_OPTUNA:
        def obj(trial):
            p = {
                "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.3, log=True),
                "max_iter": trial.suggest_int("max_iter", 100, 600),
                "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 15, 127),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 20, 200),
                "l2_regularization": trial.suggest_float("l2_regularization", 1e-6, 1.0, log=True),
            }
            return eval_fn(p)
        st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
        st.optimize(obj, n_trials=n_trials)
        return dict(st.best_params), float(st.best_value), "TPE"
    rng = np.random.default_rng(seed)
    best, best_v = None, -1
    for _ in range(n_trials):
        p = sample_gbdt_params(rng)
        v = eval_fn(p)
        if v > best_v:
            best, best_v = p, v
    return best, float(best_v), "random(fallback: optuna missing)"


RULE_FEATS = [f + "_tfidf" for f in FIELDS] + [f + "_jw" for f in FIELDS]


class TunedRule:
    """กฎให้คะแนน: ผลรวมถ่วงน้ำหนักของความคล้ายต่อช่อง น้ำหนักค้นแบบ Dirichlet บนข้อมูลฝึก (เลือกด้วย AP)"""

    def __init__(self, draws: int, seed: int):
        self.draws, self.seed, self.w = draws, seed, None

    def _x(self, X: pd.DataFrame) -> np.ndarray:
        return np.stack([np.maximum(X[f + "_tfidf"].values, X[f + "_jw"].values) for f in FIELDS], 1)

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        Z = self._x(X)
        rng = np.random.default_rng(self.seed)
        best, best_ap = None, -1
        for _ in range(self.draws):
            w = rng.dirichlet(np.ones(Z.shape[1]))
            ap = average_precision_score(y, Z @ w)
            if ap > best_ap:
                best, best_ap = w, ap
        self.w = best
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        s = self._x(X) @ self.w
        return np.stack([1 - s, s], 1)


# %% ======================================================================
# 7. CALIBRATION
# =========================================================================
class Calibrator:
    def __init__(self, method: str):
        self.method = method

    def fit(self, s: np.ndarray, y: np.ndarray):
        if self.method == "platt":
            self.m = LogisticRegression(C=1e6, max_iter=2000).fit(s.reshape(-1, 1), y)
        else:
            self.m = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(s, y)
        return self

    def __call__(self, s: np.ndarray) -> np.ndarray:
        s = np.asarray(s, dtype=float)
        if self.method == "platt":
            return self.m.predict_proba(s.reshape(-1, 1))[:, 1]
        return self.m.predict(s)


def choose_calibrator(scores: np.ndarray, y: np.ndarray, folds: np.ndarray) -> tuple[Calibrator, dict]:
    res = {"brier_raw": float(brier_score_loss(y, np.clip(scores, 0, 1)))}
    for m in ["platt", "isotonic"]:
        bs = []
        for k in np.unique(folds):
            tr, te = folds != k, folds == k
            c = Calibrator(m).fit(scores[tr], y[tr])
            bs.append(brier_score_loss(y[te], c(scores[te])))
        res[f"brier_{m}_crossfit"] = float(np.mean(bs))
    best = min(["platt", "isotonic"], key=lambda m: res[f"brier_{m}_crossfit"])
    res["selected"] = best
    return Calibrator(best).fit(scores, y), res


# %% ======================================================================
# 8. DECISION POLICIES
# =========================================================================
NO, REV, MATCH = 0, 1, 2


def chow_thresholds(cfg: Config) -> tuple[float, float]:
    # MATCH if c_fp(1-p) < min(c_fn p, c_r); NO if c_fn p < min(c_fp(1-p), c_r)
    t_match = max(1 - cfg.c_r / cfg.c_fp, cfg.c_fp / (cfg.c_fp + cfg.c_fn))
    t_no = min(cfg.c_r / cfg.c_fn, cfg.c_fp / (cfg.c_fp + cfg.c_fn))
    return t_match, t_no


def policy_decide(name: str, prm: dict, p: np.ndarray, ns: np.ndarray) -> np.ndarray:
    d = np.full(len(p), NO, dtype=np.int8)
    if name in {"fixed_0.5", "validation_F1", "closed_cost"}:
        d[p >= prm["t"]] = MATCH
    elif name in {"historical_R0", "three_way", "Chow"}:
        d[p >= prm["t_r"]] = REV
        d[p >= prm["t_m"]] = MATCH
    elif name == "historical_stage18":
        # การประมาณกฎ stage 18 เดิม [0.98, 0.95, 0.9, 0.7]: ใช้ name_sim ช่วยในแถบกลาง
        d[(p >= 0.70) & (ns >= 0.90)] = REV
        d[(p >= 0.95)] = REV
        d[(p >= 0.95) & (ns >= 0.90)] = MATCH
        d[p >= 0.98] = MATCH
    else:  # four-gene family: t_m, t_r, c_promote, c_demote
        band = (p >= prm["t_r"]) & (p < prm["t_m"])
        d[p >= prm["t_m"]] = MATCH
        d[band] = REV
        d[band & (ns >= prm["c_p"])] = MATCH
        d[band & (ns < prm["c_d"])] = NO
    return d


def evaluate(d: np.ndarray, y: np.ndarray, n_missing: int, n_all: int, cfg: Config, w=None) -> dict:
    if w is None:
        w = np.ones(len(y))
    tp = float((w * ((d == MATCH) & (y == 1))).sum())
    fp = float((w * ((d == MATCH) & (y == 0))).sum())
    r = float((w * (d == REV)).sum())
    r_pos = float((w * ((d == REV) & (y == 1))).sum())
    # perfect-review utility: a reviewed pair costs c_r only (the reviewer resolves it correctly);
    # missed = true pairs decided NO_MATCH + true pairs lost at blocking
    fn = float((w * ((d == NO) & (y == 1))).sum()) + n_missing
    total_pos = float((w * (y == 1)).sum()) + n_missing
    raw = cfg.c_fp * fp + cfg.c_fn * fn + cfg.c_r * r
    return {"TP": tp, "FP": fp, "FN": fn, "FN_auto": total_pos - tp, "REVIEW": r, "REVIEW_pos": r_pos, "raw_cost": raw,
            "cost_per_pair": raw / max(n_all, 1),
            "auto_precision": tp / (tp + fp) if tp + fp > 0 else float("nan"),
            "auto_recall": tp / total_pos if total_pos > 0 else float("nan"),
            "review_rate": r / max(float(w.sum()), 1)}


def u_to_params(kind: str, u: np.ndarray) -> dict:
    if kind == "four_gene":
        t_m = 0.90 + 0.099 * u[0]
        t_r = 0.30 + (t_m - 0.30) * u[1]
        c_p = 0.50 + 0.50 * u[2]
        return {"t_m": t_m, "t_r": t_r, "c_p": c_p, "c_d": c_p * u[3]}
    t_m = 0.50 + 0.499 * u[0]  # three_way
    return {"t_m": t_m, "t_r": 0.01 + (t_m - 0.01) * u[1]}


def search_policy(searcher: str, kind: str, objective, budget: int, seed: int, cfg: Config):
    """คืน (best_u, best_cost, trace ของ best-so-far)"""
    dim = 4 if kind == "four_gene" else 2
    rng = np.random.default_rng(seed)
    trace, best_u, best_c = [], None, np.inf

    def rec(u):
        nonlocal best_u, best_c
        c = objective(u)
        if c < best_c:
            best_c, best_u = c, np.array(u)
        trace.append(best_c)
        return c

    if searcher == "random":
        for _ in range(budget):
            rec(rng.random(dim))
    elif searcher == "scrambled_sobol":
        m = int(math.ceil(math.log2(max(budget, 2))))
        pts = qmc.Sobol(d=dim, scramble=True, seed=seed).random_base2(m)[:budget]
        for u in pts:
            rec(u)
    elif searcher == "TPE":
        if HAS_OPTUNA:
            st = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
            st.optimize(lambda t: rec(np.array([t.suggest_float(f"u{i}", 0, 1) for i in range(dim)])), n_trials=budget)
        else:  # separate stream so the fallback is not a copy of the "random" searcher
            rng_f = np.random.default_rng(seed + 10_000)
            for _ in range(budget):
                rec(rng_f.random(dim))
    elif searcher == "GA":
        pop_n = cfg.ga_pop
        pop = rng.random((pop_n, dim))
        fit = np.array([rec(u) for u in pop])
        while len(trace) < budget:
            elite = pop[np.argsort(fit)[:4]]
            children = []
            while len(children) < pop_n - len(elite) and len(trace) + len(children) < budget:
                def tourn():
                    idx = rng.choice(pop_n, 3, replace=False)
                    return pop[idx[np.argmin(fit[idx])]]
                p1, p2 = tourn(), tourn()
                mask = rng.random(dim) < 0.5
                child = np.where(mask, p1, p2)
                mut = rng.random(dim) < 0.3
                child = np.clip(child + mut * rng.normal(0, 0.05, dim), 0, 1)
                children.append(child)
            if not children:
                break
            ch = np.array(children)
            cf = np.array([rec(u) for u in ch])
            pop = np.vstack([elite, ch])
            fit = np.concatenate([np.sort(fit)[:4], cf])
            pop_n = len(pop)
    return best_u, best_c, trace


# %% ======================================================================
# 10. STATISTICS (entity-cluster bootstrap, Holm, TOST)
# =========================================================================
def pair_weights(m: np.ndarray, ea: np.ndarray, eb: np.ndarray) -> np.ndarray:
    return np.where(ea == eb, m[ea], m[ea] * m[eb]).astype(float)


def holm(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    k = len(items)
    adj, run = {}, 0.0
    for i, (h, p) in enumerate(items):
        run = max(run, min(1.0, (k - i) * p))
        adj[h] = run
    return adj


def summarize_contrast(delta: float, boot: np.ndarray, margin: float) -> dict:
    B = len(boot)
    cen = boot - delta
    p = (1 + np.sum(np.abs(cen) >= abs(delta))) / (B + 1)
    p_lo = (1 + np.sum(cen >= delta + margin)) / (B + 1)   # H0: delta <= -margin
    p_hi = (1 + np.sum(cen <= delta - margin)) / (B + 1)   # H0: delta >= +margin
    return {"delta": float(delta), "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "ci90": [float(np.percentile(boot, 5)), float(np.percentile(boot, 95))], "p": float(p),
            "tost_p": float(max(p_lo, p_hi)), "sesoi": margin, "B": int(B)}


def decide(c: dict) -> str:
    if c["ci95"][0] > c["sesoi"] and c["holm_p"] < 0.05:
        return "supported"
    if c["tost_holm_p"] < 0.05 and c["ci90"][0] > -c["sesoi"] and c["ci90"][1] < c["sesoi"]:
        return "equivalent"
    return "not supported"


# %% ======================================================================
# 11. VISUALIZATION helpers
# =========================================================================
PALETTE = {"main": "#2E5A88", "alt": "#D9822B", "good": "#3A8D5C", "bad": "#B33A3A", "grey": "#8A8F98"}


def savefig(fig, path: Path):
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def barh(ax, labels, values, highlight=None, fmt="{:.4f}", color=None):
    cols = [PALETTE["alt"] if (highlight and l in highlight) else (color or PALETTE["main"]) for l in labels]
    y = np.arange(len(labels))
    ax.barh(y, values, color=cols)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    for i, v in enumerate(values):
        ax.text(v, i, " " + fmt.format(v), va="center", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)


# %% ======================================================================
# MAIN EXPERIMENT
# =========================================================================
def run(cfg: Config) -> None:
    t0 = time.time()
    rng = set_seed(cfg.seed)
    out = Path(cfg.out)
    figdir, artdir, depdir = out / "figures", out / "artifacts", out / "deploy"
    for d in (out, figdir, artdir, depdir):
        d.mkdir(parents=True, exist_ok=True)
    results: dict = {"config": asdict(cfg), "classification": "EXPLORATORY (LinkSocial, retrospectively exposed)",
                     "env": {"rapidfuzz": HAS_RAPIDFUZZ, "optuna": HAS_OPTUNA}}
    log(f"rapidfuzz={HAS_RAPIDFUZZ} optuna={HAS_OPTUNA}")

    # ---------------- 1. ingestion
    if cfg.demo:
        raw = make_demo(seed=cfg.seed)
        log(f"demo data: {len(raw)} rows")
    elif cfg.data and Path(cfg.data).is_dir():
        raw = load_json_dir(cfg.data)
        log(f"loaded JSON dir: {len(raw)} rows")
    elif cfg.data:
        raw = load_csv(cfg.data)
        log(f"loaded CSV: {len(raw)} rows")
    else:
        sys.exit("ต้องระบุ --data หรือ --demo")

    # ---------------- 3. preparation
    df, dstats = prepare(raw)
    df = assign_folds(df, cfg.n_folds, cfg.seed)
    gt = ground_truth(df)
    dstats["cross_platform_positive_pairs"] = int(len(gt))
    dstats["all_cross_platform_pairs"] = n_cross_pairs(df)
    results["data"] = dstats
    log(f"profiles={len(df)} entities={dstats['distinct_entities']} positives={len(gt)}")
    dev_folds = [k for k in range(cfg.n_folds) if k != cfg.test_fold]
    is_dev = df["fold"].isin(dev_folds).values
    gt_dev, gt_test = gt[gt["fold"].isin(dev_folds)], gt[gt["fold"] == cfg.test_fold]
    N = len(df)
    gt_keys = set(pair_key(gt["a"].values, gt["b"].values, N).tolist())
    nall = {k: n_cross_pairs(df[df["fold"] == k]) for k in range(cfg.n_folds)}

    # ---------------- 2. data understanding (figures)
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.6))
    pc = df["platform"].value_counts()
    axs[0].bar(pc.index, pc.values, color=PALETTE["main"]); axs[0].set_title("Profiles per platform")
    nn = {f: int((df[f] != "").sum()) for f in FIELDS}
    axs[1].bar(list(nn), list(nn.values()), color=PALETTE["main"]); axs[1].set_title("Non-empty fields")
    axs[1].tick_params(axis="x", rotation=30)
    gs = df.groupby("entity").size().value_counts().sort_index()
    axs[2].bar(gs.index.astype(str), gs.values, color=PALETTE["main"]); axs[2].set_title("Profiles per entity")
    for a in axs:
        a.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "01_data_understanding.png")

    # ---------------- semantic embeddings (frozen)
    emb_model = Embedder(cfg.st_model, cfg.use_semantic)
    use_sem = emb_model.ok
    emb = None
    if use_sem:
        log("encoding profiles with MiniLM (frozen)")
        emb = {f: emb_model.encode(df[f].tolist()) for f in ["fullname", "bio"]}
        emb["profile"] = emb_model.encode(profile_text(df).tolist())

    # ---------------- 4. blocking per fold
    log("blocking ...")
    cand = {m: {} for m in ["B0", "sparse", "dense", "hybrid_union", "hybrid_rrf"]}
    ranked_cache = {}
    for k in range(cfg.n_folds):
        dff = df[df["fold"] == k]
        b0 = block_b0(dff, cfg.b0_max_block)
        budget = len(b0)
        cand["B0"][k] = b0
        fit_mask = df["fold"].isin([j for j in dev_folds if j != k]) if k != cfg.test_fold else df["fold"].isin(dev_folds)
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), sublinear_tf=True, min_df=1)
        vec.fit(profile_text(df[fit_mask]).values)
        Xs = vec.transform(profile_text(dff).values)
        r_s = knn_scored_pairs(dff, Xs, cfg.knn_k)
        cand["sparse"][k] = take_budget(r_s, budget)
        ranked_cache[(k, "sparse")] = r_s
        if use_sem:
            Xd = emb["profile"][dff["pid"].values]
            r_d = knn_scored_pairs(dff, Xd, cfg.knn_k)
            cand["dense"][k] = take_budget(r_d, budget)
            cand["hybrid_union"][k] = take_budget(union_lists(r_s, r_d), budget)
            cand["hybrid_rrf"][k] = take_budget(rrf(r_s, r_d), budget)
    methods = [m for m in cand if cand[m]]

    def pc_of(m, folds):
        found = sum(len(set(pair_key(cand[m][k][:, 0], cand[m][k][:, 1], N).tolist()) & gt_keys) for k in folds)
        tot = len(gt[gt["fold"].isin(folds)])
        return found / max(tot, 1), found, tot

    blk_dev = {m: dict(zip(["PC", "found", "GT"], pc_of(m, dev_folds))) | {"C": int(sum(len(cand[m][k]) for k in dev_folds))} for m in methods}
    results["blocking_dev"] = blk_dev
    lexical_methods = [m for m in ["B0", "sparse"] if m in methods]
    b_star = max(lexical_methods + [m for m in methods if m.startswith("hybrid")], key=lambda m: blk_dev[m]["PC"])
    best_lex = max(lexical_methods, key=lambda m: blk_dev[m]["PC"])
    results["B_star"] = b_star
    log(f"dev PC: " + ", ".join(f"{m}={v['PC']:.4f}" for m, v in blk_dev.items()) + f" -> B*={b_star}")

    # ---------------- 5. features for B* candidates (+ B0 / hybrid on test for factorial)
    def build_static(pairs):
        return static_features(df, pairs, emb if use_sem else None)

    def pairs_frame(m, folds):
        arr = np.vstack([cand[m][k] for k in folds if len(cand[m][k])])
        f = df["fold"].values[arr[:, 0]]
        y = np.array([kk in gt_keys for kk in pair_key(arr[:, 0], arr[:, 1], N)], dtype=np.int8)
        return arr, f, y

    log("features (static) ...")
    P_dev, F_dev, y_dev = pairs_frame(b_star, dev_folds)
    P_test, F_test, y_test = pairs_frame(b_star, [cfg.test_fold])
    S_dev, S_test = build_static(P_dev), build_static(P_test)
    log(f"dev candidates={len(P_dev)} (pos {y_dev.sum()}), test candidates={len(P_test)}")

    # TF-IDF contexts: round k = fit on dev folds except k; 'full' = fit on all dev folds
    log("features (TF-IDF per context, fit on training folds only) ...")
    vec_ctx = {k: fit_field_vectorizers(df[df["fold"].isin([j for j in dev_folds if j != k])]) for k in dev_folds}
    vec_ctx["full"] = fit_field_vectorizers(df[is_dev])
    T_dev = {c: tfidf_features(df, P_dev, v) for c, v in vec_ctx.items()}
    T_test_full = tfidf_features(df, P_test, vec_ctx["full"])
    lex_cols = LEX_COLS
    sem_cols = SEM_COLS if use_sem else []

    def X_of(static: pd.DataFrame, tf: pd.DataFrame, cols: list) -> pd.DataFrame:
        M = pd.concat([static.reset_index(drop=True), tf.reset_index(drop=True)], axis=1)
        return M[cols]

    name_sim_dev = np.maximum(S_dev["username_jw"].values, S_dev["fullname_jw"].values)
    name_sim_test = np.maximum(S_test["username_jw"].values, S_test["fullname_jw"].values)

    # ---------------- 6. modeling (OOF on dev)
    def oof_predict(make_model, cols, seeds=(42,), rows_mask=None, ent_frac=None):
        oof = np.zeros(len(P_dev))
        for k in dev_folds:
            tr, te = F_dev != k, F_dev == k
            if ent_frac is not None:
                ents_tr = np.unique(df["entity"].values[P_dev[tr, 0]])
                keep = np.random.default_rng(42).choice(ents_tr, max(1, int(len(ents_tr) * ent_frac)), replace=False)
                # anchor on side a only: positives and negatives both shrink by ent_frac (class balance kept)
                tr = tr & np.isin(df["entity"].values[P_dev[:, 0]], keep)
            X = X_of(S_dev, T_dev[k], cols)
            pk = np.zeros(te.sum())
            for s in seeds:
                m = make_model(s).fit(X[tr], y_dev[tr])
                pk += m.predict_proba(X[te])[:, 1]
            oof[te] = pk / len(seeds)
        return oof

    def fold_aps(pred):
        return [average_precision_score(y_dev[F_dev == k], pred[F_dev == k]) for k in dev_folds]

    def test_predict(make_model, cols, seeds=(42,)):
        Xtr, Xte = X_of(S_dev, T_dev["full"], cols), X_of(S_test, T_test_full, cols)
        out_ = np.zeros(len(P_test)); models = []
        for s in seeds:
            m = make_model(s).fit(Xtr, y_dev)
            out_ += m.predict_proba(Xte)[:, 1]; models.append(m)
        return out_ / len(seeds), models

    models_dev, oof_scores, test_scores, trained = {}, {}, {}, {}
    feature_sets = {"lexical": lex_cols}
    if use_sem:
        feature_sets["fusion"] = lex_cols + sem_cols
        feature_sets["semantic"] = sem_cols

    best_params = {}
    for fs in [f for f in ["lexical", "fusion"] if f in feature_sets]:
        cols = feature_sets[fs]
        log(f"tuning GBDT-{fs}: {cfg.gbdt_trials} configs ...")
        bp, bv, how = tune_gbdt(lambda p: float(np.mean(fold_aps(oof_predict(lambda s: gbdt(p, s), cols)))),
                                cfg.gbdt_trials, cfg.seed)
        best_params[fs] = bp
        results.setdefault("tuning", {})[f"GBDT-{fs}"] = {"best_params": bp, "best_mean_fold_AP": bv, "sampler": how}

    def run_model(name, make_model, cols, seeds):
        oof = oof_predict(make_model, cols, seeds)
        ts, ms = test_predict(make_model, cols, seeds)
        oof_scores[name], test_scores[name], trained[name] = oof, ts, ms
        models_dev[name] = {"OOF_AP": float(average_precision_score(y_dev, oof)), "fold_AP": fold_aps(oof),
                            "n_features": len(cols), "seeds": len(seeds)}
        log(f"  {name}: OOF AP={models_dev[name]['OOF_AP']:.4f}")

    log("training models (OOF + test predictions; test scores stay sealed until step 10) ...")
    run_model("rule", lambda s: TunedRule(cfg.rule_draws, s), RULE_FEATS, (42,))
    run_model("LR-lexical", lambda s: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), lex_cols, (42,))
    run_model("GBDT-lexical", lambda s: gbdt(best_params["lexical"], s), lex_cols, cfg.model_seeds)
    if use_sem:
        run_model("LR-fusion", lambda s: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), feature_sets["fusion"], (42,))
        run_model("GBDT-fusion", lambda s: gbdt(best_params["fusion"], s), feature_sets["fusion"], cfg.model_seeds)
        run_model("GBDT-semantic", lambda s: gbdt(best_params["fusion"], s), sem_cols, cfg.model_seeds)
    for f in FIELDS:
        run_model(f"GBDT-single-{f}", lambda s: gbdt(best_params["lexical"], s), group_cols(lex_cols, f), cfg.model_seeds)
    if cfg.run_ablations:
        base_fs = "fusion" if use_sem else "lexical"
        for f in FIELDS:
            cols = [c for c in feature_sets[base_fs] if c not in group_cols(feature_sets[base_fs], f)]
            oof = oof_predict(lambda s: gbdt(best_params[base_fs], s), cols, (42,))
            models_dev[f"GBDT-{base_fs}-without-{f}"] = {"OOF_AP": float(average_precision_score(y_dev, oof)), "n_features": len(cols), "seeds": 1}
            log(f"  ablation without {f}: {models_dev[f'GBDT-{base_fs}-without-{f}']['OOF_AP']:.4f}")
    lc = {}
    if cfg.run_learning_curve:
        for frac in [0.1, 0.25, 0.5, 1.0]:
            g = oof_predict(lambda s: gbdt(best_params["lexical"], s), lex_cols, (42,), ent_frac=frac)
            l_ = oof_predict(lambda s: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), lex_cols, (42,), ent_frac=frac)
            lc[frac] = {"GBDT": float(np.mean(fold_aps(g))), "LR": float(np.mean(fold_aps(l_)))}
        results["learning_curve"] = lc
    results["models_dev"] = models_dev

    single = {f: models_dev[f"GBDT-single-{f}"]["OOF_AP"] for f in FIELDS}
    best_single = f"GBDT-single-{max(single, key=single.get)}"
    m_star = max([m for m in ["GBDT-lexical", "GBDT-fusion"] if m in models_dev], key=lambda m: models_dev[m]["OOF_AP"])
    results["selection"] = {"best_single_group": best_single, "M_star": m_star}
    log(f"best single group={best_single}, M*={m_star}")

    # ---------------- 7. calibration (dev only)
    cal, cal_res = choose_calibrator(oof_scores[m_star], y_dev, F_dev)
    cal_rule, _ = choose_calibrator(oof_scores["rule"], y_dev, F_dev)
    results["calibration"] = cal_res
    p_dev = cal(oof_scores[m_star])
    log(f"calibration: {cal_res}")

    # ---------------- 8. policies (select on dev)
    n_missing_dev = len(gt_dev) - int(y_dev.sum())
    nall_dev = sum(nall[k] for k in dev_folds)
    t_cm, t_cn = chow_thresholds(cfg)
    prec, rec, thr = precision_recall_curve(y_dev, p_dev)
    f1 = 2 * prec * rec / np.maximum(prec + rec, 1e-12)
    t_f1 = float(thr[np.nanargmax(f1[:-1])]) if len(thr) else 0.5
    fixed_policies = {
        "fixed_0.5": {"t": 0.5}, "validation_F1": {"t": t_f1},
        "closed_cost": {"t": cfg.c_fp / (cfg.c_fp + cfg.c_fn)},
        "historical_R0": {"t_m": 0.98, "t_r": 0.95}, "historical_stage18": {},
        "Chow": {"t_m": t_cm, "t_r": t_cn},
    }
    pol_dev, pol_params, traces = {}, {}, {}
    for name, prm in fixed_policies.items():
        pol_params[name] = [prm]
        pol_dev[name] = [evaluate(policy_decide(name, prm, p_dev, name_sim_dev), y_dev, n_missing_dev, nall_dev, cfg)]

    def dev_cost(name, kind):
        return lambda u: evaluate(policy_decide(name, u_to_params(kind, u), p_dev, name_sim_dev), y_dev, n_missing_dev, nall_dev, cfg)["raw_cost"]

    log(f"policy search: budget={cfg.policy_budget} x seeds={len(cfg.policy_seeds)} ...")
    searched = {"three_way": ("random", "three_way")}
    for s in ["random", "scrambled_sobol", "TPE", "GA"]:
        searched[s] = (s, "four_gene")
    for name, (searcher, kind) in searched.items():
        pol_params[name], pol_dev[name], traces[name] = [], [], []
        for sd in cfg.policy_seeds:
            u, c, tr = search_policy(searcher, kind, dev_cost(name, kind), cfg.policy_budget, sd, cfg)
            prm = u_to_params(kind, u)
            pol_params[name].append(prm)
            pol_dev[name].append(evaluate(policy_decide(name, prm, p_dev, name_sim_dev), y_dev, n_missing_dev, nall_dev, cfg))
            traces[name].append(tr)
    dev_cost_mean = {n: float(np.mean([r["cost_per_pair"] for r in v])) for n, v in pol_dev.items()}
    best_non_ga = min([n for n in dev_cost_mean if n != "GA"], key=dev_cost_mean.get)
    best_val_policy = min(dev_cost_mean, key=dev_cost_mean.get)
    results["policy_dev"] = {n: {"cost_per_pair_mean": dev_cost_mean[n], "params": pol_params[n]} for n in pol_dev}
    results["selection"].update({"best_non_GA_policy": best_non_ga, "best_validation_policy": best_val_policy,
                                 "tpe_sampler": "optuna TPE" if HAS_OPTUNA else "random (optuna missing)"})
    log(f"best non-GA policy={best_non_ga}, best validation policy={best_val_policy}")

    # ---------------- 9. FREEZE
    frozen = {"B_star": b_star, "M_star": m_star, "best_single": best_single, "calibrator": cal,
              "rule_calibrator": cal_rule, "policies": pol_params, "best_params": best_params,
              "vectorizers_full": vec_ctx["full"]}
    joblib.dump(frozen, artdir / "frozen_selection.joblib")
    for name, ms in trained.items():
        joblib.dump(ms, artdir / f"model_{name}.joblib")
    manifest = {p.name: sha256_file(p) for p in sorted(artdir.glob("*.joblib"))}
    (artdir / "FROZEN_MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    test_access_log = out / "test_access.jsonl"
    with open(test_access_log, "a") as f:
        f.write(json.dumps({"time": time.time(), "event": "OPEN_TEST_ONCE", "manifest_sha": hashlib.sha256(json.dumps(manifest).encode()).hexdigest()}) + "\n")
    log("frozen; opening sealed test fold ONCE")
    log(f"test candidates={len(P_test)} (pos {y_test.sum()})")

    # ---------------- 10. FINAL EVALUATION on test fold
    ent_a, ent_b = df["entity"].values[P_test[:, 0]], df["entity"].values[P_test[:, 1]]
    test_ents = np.unique(df["entity"].values[df["fold"] == cfg.test_fold])
    ent_index = {e: i for i, e in enumerate(test_ents)}
    ia, ib = np.vectorize(ent_index.get)(ent_a), np.vectorize(ent_index.get)(ent_b)
    n_missing_test = len(gt_test) - int(y_test.sum())
    nall_test = nall[cfg.test_fold]

    blk_test = {m: dict(zip(["PC", "found", "GT"], pc_of(m, [cfg.test_fold]))) for m in methods}
    results["blocking_test"] = blk_test
    matcher_test = {}
    for name in ["rule", "GBDT-lexical", "GBDT-fusion", best_single, "LR-lexical"]:
        if name not in test_scores:
            continue
        s = test_scores[name]
        matcher_test[name] = {"AP": float(average_precision_score(y_test, s))}
    results["matchers_test"] = matcher_test

    p_test = cal(test_scores[m_star])
    pol_test = {}
    for name, plist in pol_params.items():
        rs = [evaluate(policy_decide(name, prm, p_test, name_sim_test), y_test, n_missing_test, nall_test, cfg) for prm in plist]
        pol_test[name] = {k: float(np.mean([r[k] for r in rs])) for k in rs[0]} | {"seeds": len(rs),
                          "cost_sd": float(np.std([r["cost_per_pair"] for r in rs]))}
    results["policies_test"] = pol_test

    # bootstrap contrasts
    log(f"bootstrap B={cfg.bootstrap_B} ...")
    gt_test_ent = np.vectorize(ent_index.get)(gt_test["entity"].values)
    found_by = {}
    for m in methods:
        ks = set(pair_key(cand[m][cfg.test_fold][:, 0], cand[m][cfg.test_fold][:, 1], N).tolist())
        found_by[m] = np.array([kk in ks for kk in pair_key(gt_test["a"].values, gt_test["b"].values, N)])
    missing_mask = ~found_by[b_star]
    missing_ent = gt_test_ent[missing_mask]

    contrasts = {}
    specs = {"H1": ("GBDT-lexical", best_single), "H2": ("GBDT-lexical", "rule")}
    if use_sem:
        specs["H3"] = ("GBDT-fusion", "GBDT-lexical")
    ga_d = [policy_decide("GA", prm, p_test, name_sim_test) for prm in pol_params["GA"]]
    base_d = [policy_decide(best_non_ga, prm, p_test, name_sim_test) for prm in pol_params[best_non_ga]]
    brng = np.random.default_rng(4242)
    boots = defaultdict(list)
    for _ in range(cfg.bootstrap_B):
        m = brng.multinomial(len(test_ents), np.full(len(test_ents), 1 / len(test_ents))).astype(float)
        w = pair_weights(m, ia, ib)
        if w[y_test == 1].sum() == 0:
            continue
        for h, (a_, b_) in specs.items():
            boots[h].append(average_precision_score(y_test, test_scores[a_], sample_weight=w)
                            - average_precision_score(y_test, test_scores[b_], sample_weight=w))
        miss_w = float(m[missing_ent].sum())
        ca = np.mean([evaluate(d, y_test, miss_w, nall_test, cfg, w)["raw_cost"] for d in ga_d])
        cb = np.mean([evaluate(d, y_test, miss_w, nall_test, cfg, w)["raw_cost"] for d in base_d])
        boots["H4"].append((cb - ca) / cb)
        if "hybrid_rrf" in found_by:
            wp = m[gt_test_ent]
            boots["H5"].append((wp * found_by["hybrid_rrf"]).sum() / wp.sum() - (wp * found_by[best_lex]).sum() / wp.sum())
    point = {h: average_precision_score(y_test, test_scores[a_]) - average_precision_score(y_test, test_scores[b_]) for h, (a_, b_) in specs.items()}
    ca0 = np.mean([evaluate(d, y_test, n_missing_test, nall_test, cfg)["raw_cost"] for d in ga_d])
    cb0 = np.mean([evaluate(d, y_test, n_missing_test, nall_test, cfg)["raw_cost"] for d in base_d])
    point["H4"] = (cb0 - ca0) / cb0
    if "hybrid_rrf" in found_by:
        point["H5"] = found_by["hybrid_rrf"].mean() - found_by[best_lex].mean()
    for h in point:
        contrasts[h] = summarize_contrast(point[h], np.array(boots[h]), cfg.sesoi[h])
    hp = holm({h: c["p"] for h, c in contrasts.items()})
    ht = holm({h: c["tost_p"] for h, c in contrasts.items()})
    for h in contrasts:
        contrasts[h]["holm_p"], contrasts[h]["tost_holm_p"] = hp[h], ht[h]
        contrasts[h]["decision"] = decide(contrasts[h])
    contrasts["H4"]["baseline"] = best_non_ga
    results["primary_contrasts"] = contrasts
    for h, c in contrasts.items():
        log(f"{h}: delta={c['delta']:.4f} CI95={c['ci95'][0]:.4f}..{c['ci95'][1]:.4f} -> {c['decision']}")

    # factorial 2x2x2 on test: blocker (B0 vs hybrid_rrf|sparse) x matcher (rule vs M*) x policy (fixed0.5 vs best-val)
    b1 = "hybrid_rrf" if "hybrid_rrf" in methods else ("sparse" if b_star != "sparse" else "B0")
    fact = []
    m_cols = feature_sets["fusion" if m_star == "GBDT-fusion" else "lexical"]
    for bi, bname in enumerate(["B0", b1]):
        Pb, _, yb = pairs_frame(bname, [cfg.test_fold])
        Sb = build_static(Pb)
        Tb = tfidf_features(df, Pb, vec_ctx["full"])
        nsb = np.maximum(Sb["username_jw"].values, Sb["fullname_jw"].values)
        miss_b = len(gt_test) - int(yb.sum())
        rule_p = cal_rule(np.mean([mm.predict_proba(X_of(Sb, Tb, RULE_FEATS))[:, 1] for mm in trained["rule"]], 0))
        mstar_p = cal(np.mean([mm.predict_proba(X_of(Sb, Tb, m_cols))[:, 1] for mm in trained[m_star]], 0))
        for mi, pb in enumerate([rule_p, mstar_p]):
            for pi, (pname, plist) in enumerate([("fixed_0.5", [{"t": 0.5}]), (best_val_policy, pol_params[best_val_policy])]):
                rs = [evaluate(policy_decide(pname, prm, pb, nsb), yb, miss_b, nall_test, cfg) for prm in plist]
                fact.append({"B": bi, "M": mi, "P": pi, "blocker": bname, "cost": float(np.mean([r["cost_per_pair"] for r in rs])),
                             "auto_recall": float(np.mean([r["auto_recall"] for r in rs]))})
    fdf = pd.DataFrame(fact)
    eff = {}
    for name, cols_ in {"blocker": ["B"], "matcher": ["M"], "policy": ["P"], "blocker x matcher": ["B", "M"],
                        "blocker x policy": ["B", "P"], "matcher x policy": ["M", "P"], "blocker x matcher x policy": ["B", "M", "P"]}.items():
        sgn = np.prod([2 * fdf[c].values - 1 for c in cols_], axis=0)
        eff[name] = {"cost": float(2 * np.mean(sgn * fdf["cost"].values)), "auto_recall": float(2 * np.mean(sgn * fdf["auto_recall"].values))}
    results["factorial"] = {"cells": fact, "effects": eff, "B1": b1}

    # ---------------- 11. VISUALIZATION
    log("figures ...")
    # 02 blocking PC dev vs test
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ms = sorted(methods, key=lambda m: -blk_dev[m]["PC"])
    x = np.arange(len(ms))
    ax.bar(x - 0.2, [blk_dev[m]["PC"] for m in ms], 0.4, label="development", color=PALETTE["main"])
    ax.bar(x + 0.2, [blk_test[m]["PC"] for m in ms], 0.4, label="sealed test", color=PALETTE["alt"])
    ax.set_xticks(x, ms); ax.set_ylabel("Pair completeness (PC)"); ax.set_ylim(0, 1.05)
    ax.set_title("Blocking at equal candidate budget", pad=22)
    ax.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8)
    for i, m in enumerate(ms):
        ax.text(i - 0.2, blk_dev[m]["PC"], f"{blk_dev[m]['PC']:.3f}", ha="center", va="bottom", fontsize=7)
        ax.text(i + 0.2, blk_test[m]["PC"], f"{blk_test[m]['PC']:.3f}", ha="center", va="bottom", fontsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "02_blocking_pc.png")

    # 03 dev OOF AP comparison (models + single groups + ablations)
    md = sorted(models_dev.items(), key=lambda kv: -kv[1]["OOF_AP"])
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(md) + 1))
    barh(ax, [k for k, _ in md], [v["OOF_AP"] for _, v in md], highlight={m_star, best_single, "rule"})
    ax.set_xlabel("Development OOF AP"); ax.set_title("Model / feature-set comparison (development)")
    ax.set_xlim(0, 1.08)
    savefig(fig, figdir / "03_model_ap_dev.png")

    # 04 PR curves on test
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for name, col in zip(matcher_test, [PALETTE["grey"], PALETTE["main"], PALETTE["alt"], PALETTE["bad"], PALETTE["good"]]):
        pr, rc, _ = precision_recall_curve(y_test, test_scores[name])
        ax.plot(rc, pr, label=f"{name} (AP={matcher_test[name]['AP']:.3f})", color=col)
    ax.set_xlabel("Recall (candidate)"); ax.set_ylabel("Precision"); ax.set_title("Precision-recall on sealed test")
    ax.legend(fontsize=7, frameon=False); ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "04_pr_curves_test.png")

    # 05 learning curve
    if lc:
        fig, ax = plt.subplots(figsize=(5.5, 3.6))
        fr = sorted(lc)
        ax.plot(fr, [lc[f]["GBDT"] for f in fr], "o-", color=PALETTE["main"], label="GBDT")
        ax.plot(fr, [lc[f]["LR"] for f in fr], "s-", color=PALETTE["alt"], label="LR")
        ax.set_xscale("log"); ax.set_xticks(fr, [f"{int(f*100)}%" for f in fr])
        ax.set_xlabel("Training entities"); ax.set_ylabel("Mean fold AP"); ax.set_title("Learning curve (development)")
        ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
        savefig(fig, figdir / "05_learning_curve.png")

    # 06 reliability diagram
    fig, ax = plt.subplots(figsize=(4.8, 4.5))
    bins = np.linspace(0, 1, 11)
    for lab, pp, col in [("raw score", np.clip(test_scores[m_star], 0, 1), PALETTE["grey"]), (f"{cal_res['selected']} calibrated", p_test, PALETTE["main"])]:
        idx = np.digitize(pp, bins[1:-1])
        xs = [pp[idx == i].mean() for i in range(10) if (idx == i).any()]
        ys = [y_test[idx == i].mean() for i in range(10) if (idx == i).any()]
        ax.plot(xs, ys, "o-", label=lab, color=col)
    ax.plot([0, 1], [0, 1], "--", color="black", lw=0.8)
    ax.set_xlabel("Predicted probability"); ax.set_ylabel("Observed match rate"); ax.set_title("Calibration (sealed test)")
    ax.legend(frameon=False, fontsize=8); ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "06_calibration_reliability.png")

    # 07 policy cost bar (test)
    pt = sorted(pol_test.items(), key=lambda kv: kv[1]["cost_per_pair"])
    fam = lambda n: PALETTE["bad"] if n == "GA" else (PALETTE["good"] if n in {"Chow", "three_way"} else (PALETTE["alt"] if n in {"random", "scrambled_sobol", "TPE"} else PALETTE["grey"]))
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    y_ = np.arange(len(pt))
    ax.barh(y_, [v["cost_per_pair"] * 1e5 for _, v in pt], xerr=[v["cost_sd"] * 1e5 for _, v in pt], color=[fam(n) for n, _ in pt])
    ax.set_yticks(y_, [n for n, _ in pt]); ax.invert_yaxis()
    for i, (_, v) in enumerate(pt):
        ax.text(v["cost_per_pair"] * 1e5, i, f" {v['cost_per_pair']*1e5:.2f}", va="center", fontsize=8)
    ax.set_xlabel("Expected cost per cross-platform pair (x1e-5), 2:1:0.1")
    ax.set_title("Decision policies on sealed test")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=PALETTE["good"], label="cost-based three-way"), Patch(color=PALETTE["alt"], label="4-parameter rule, non-GA search"),
                       Patch(color=PALETTE["bad"], label="4-parameter rule, GA"), Patch(color=PALETTE["grey"], label="single threshold / historical")],
              frameon=False, fontsize=7, loc="center right")
    ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "07_policy_cost_test.png")

    # 08 cost vs auto recall
    fig, ax = plt.subplots(figsize=(6, 4.2))
    for n, v in pol_test.items():
        ax.scatter(v["auto_recall"], v["cost_per_pair"] * 1e5, color=fam(n), s=40)
        ax.annotate(n, (v["auto_recall"], v["cost_per_pair"] * 1e5), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("Automatic end-to-end recall"); ax.set_ylabel("Cost per pair (x1e-5)")
    ax.set_title("Recall vs cost trade-off (test)"); ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "08_policy_recall_vs_cost.png")

    # 09 search convergence (dev, best-so-far)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for name, col, lw, ls in [("random", PALETTE["grey"], 1.2, "-"), ("scrambled_sobol", PALETTE["alt"], 1.2, "-"),
                              ("TPE", PALETTE["main"], 1.2, "--"), ("GA", PALETTE["bad"], 2.2, "-")]:
        L = min(len(t) for t in traces[name])
        arr = np.array([t[:L] for t in traces[name]]) / nall_dev * 1e5
        lab = name if (name != "TPE" or HAS_OPTUNA) else "TPE (fallback = random)"
        ax.plot(np.arange(1, L + 1), arr.mean(0), label=lab, color=col, lw=lw, ls=ls)
    ax.axhline(dev_cost_mean["Chow"] * 1e5, ls="--", color=PALETTE["good"], label="Chow (no search)")
    ax.set_xscale("log"); ax.set_xlabel("Evaluations"); ax.set_ylabel("Best dev cost so far (x1e-5)")
    ax.set_title("Policy search at equal budget (development)"); ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "09_policy_search_convergence.png")

    # 10 forest plot H1-H5 (one panel per hypothesis: different units)
    hs = list(contrasts)
    units = {"H1": "delta AP", "H2": "delta AP", "H3": "delta AP", "H4": "relative cost reduction (GA vs best non-GA)", "H5": "delta PC"}
    fig, axs = plt.subplots(len(hs), 1, figsize=(7, 1.15 * len(hs) + 0.6))
    axs = np.atleast_1d(axs)
    for ax, h in zip(axs, hs):
        c = contrasts[h]
        col = PALETTE["good"] if c["decision"] == "supported" else (PALETTE["main"] if c["decision"] == "equivalent" else PALETTE["bad"])
        lo, hi = c["ci95"]
        span = max(abs(lo), abs(hi), c["sesoi"]) * 1.4
        ax.axvspan(-c["sesoi"], c["sesoi"], color="#EEEEEE")
        ax.axvline(0, color="black", lw=0.8)
        ax.errorbar(c["delta"], 0, xerr=[[c["delta"] - lo], [hi - c["delta"]]], fmt="o", color=col, capsize=5)
        ax.set_xlim(-span, span); ax.set_yticks([0], [h]); ax.set_ylim(-1, 1)
        ax.set_title(f"{h}: {units[h]} = {c['delta']:.4f} [{lo:.4f}, {hi:.4f}]  ->  {c['decision']}", fontsize=8, loc="left", color=col)
        ax.spines[["top", "right", "left"]].set_visible(False); ax.tick_params(labelsize=7)
    fig.suptitle("Primary hypotheses on sealed test (95% CI; grey band = ±SESOI)", fontsize=10)
    savefig(fig, figdir / "10_hypotheses_forest.png")

    # 11 factorial effects
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    names = list(eff)
    axs[0].barh(names, [eff[n]["auto_recall"] for n in names], color=PALETTE["main"]); axs[0].set_title("Effect on automatic recall")
    axs[1].barh(names, [eff[n]["cost"] * 1e5 for n in names], color=PALETTE["alt"]); axs[1].set_title("Effect on cost (x1e-5)")
    for a in axs:
        a.invert_yaxis(); a.axvline(0, color="black", lw=0.8); a.spines[["top", "right"]].set_visible(False)
    savefig(fig, figdir / "11_factorial_effects.png")

    # 12 decision matrix for best validation policy
    bd = policy_decide(best_val_policy, pol_params[best_val_policy][0], p_test, name_sim_test)
    mat = np.array([[((bd == d) & (y_test == 1)).sum() for d in (MATCH, REV, NO)],
                    [((bd == d) & (y_test == 0)).sum() for d in (MATCH, REV, NO)]], dtype=float)
    mat[0, 2] += n_missing_test
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.imshow(np.log1p(mat), cmap="Blues")
    for i in range(2):
        for j in range(3):
            ax.text(j, i, f"{int(mat[i, j]):,}", ha="center", va="center", fontsize=9)
    ax.set_xticks(range(3), ["MATCH", "REVIEW", "NO_MATCH"]); ax.set_yticks(range(2), ["true pair", "not same person"])
    ax.set_title(f"Decision matrix: {best_val_policy} (test, incl. blocked positives)")
    savefig(fig, figdir / "12_decision_matrix.png")

    # ---------------- 12. DEPLOY bundle
    log("building deployment bundle ...")
    bundle = {
        "version": "v2-single-file",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "classification": results["classification"],
        "cost_ratio": [cfg.c_fp, cfg.c_fn, cfg.c_r],
        "blocker_vectorizer": TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), sublinear_tf=True).fit(profile_text(df[is_dev]).values),
        "field_vectorizers": vec_ctx["full"],
        "feature_cols": m_cols,
        "models": trained[m_star],
        "calibrator": cal,
        "policy_name": best_val_policy,
        "policy_params": pol_params[best_val_policy][0],
        "use_semantic": m_star == "GBDT-fusion",
        "st_model": cfg.st_model,
        "knn_k": cfg.deploy_knn_k,
    }
    joblib.dump(bundle, depdir / "bundle.joblib")
    (depdir / "MODEL_CARD.md").write_text(model_card(results, bundle), encoding="utf-8")

    # ---------------- outputs
    results["runtime_seconds"] = round(time.time() - t0, 1)
    (out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    (out / "REPORT.md").write_text(report_md(results), encoding="utf-8")
    (out / "run.log").write_text("\n".join(LOG), encoding="utf-8")
    log(f"done in {results['runtime_seconds']} s -> {out}")


def report_md(r: dict) -> str:
    L = ["# Unified run report (EXPLORATORY)", "", f"Profiles: {r['data']['eligible_rows']:,} | positives: {r['data']['cross_platform_positive_pairs']:,} | B* = {r['B_star']} | M* = {r['selection']['M_star']}", ""]
    L += ["## Blocking (PC)", "", "| Method | dev | test |", "| --- | --- | --- |"]
    L += [f"| {m} | {v['PC']:.4f} | {r['blocking_test'][m]['PC']:.4f} |" for m, v in r["blocking_dev"].items()]
    L += ["", "## Matchers on test (AP)", "", "| Model | AP |", "| --- | --- |"] + [f"| {m} | {v['AP']:.4f} |" for m, v in r["matchers_test"].items()]
    L += ["", "## Policies on test (cost x1e-5, 2:1:0.1)", "", "| Policy | cost | auto P | auto recall | review rate |", "| --- | --- | --- | --- | --- |"]
    for n, v in sorted(r["policies_test"].items(), key=lambda kv: kv[1]["cost_per_pair"]):
        L.append(f"| {n} | {v['cost_per_pair']*1e5:.2f} | {v['auto_precision']:.4f} | {v['auto_recall']:.4f} | {v['review_rate']:.4f} |")
    L += ["", "## Primary hypotheses", "", "| H | delta | 95% CI | Holm p | TOST Holm p | decision |", "| --- | --- | --- | --- | --- | --- |"]
    for h, c in r["primary_contrasts"].items():
        L.append(f"| {h} | {c['delta']:.4f} | {c['ci95'][0]:.4f} to {c['ci95'][1]:.4f} | {c['holm_p']:.4f} | {c['tost_holm_p']:.4f} | {c['decision']} |")
    L += ["", "Figures: see ./figures. All results are exploratory; cost ratio is an assumption."]
    return "\n".join(L)


def model_card(r: dict, b: dict) -> str:
    return "\n".join([
        "# Model card: cross-platform identity resolver", "",
        f"- Created: {b['created']}", f"- Status: {b['classification']}",
        f"- Pipeline: sparse TF-IDF kNN blocking (k={b['knn_k']}) -> {r['selection']['M_star']} ({len(b['models'])} seeds) -> {r['calibration']['selected']} calibration -> {b['policy_name']} policy",
        f"- Policy params: {json.dumps(b['policy_params'])}", f"- Cost ratio (FP:FN:REVIEW, assumption): {b['cost_ratio']}",
        "- Intended use: offline linking of public profile records (username, full name, bio, location, links); REVIEW items require a human.",
        "- Not validated on: other platforms, other languages, live CRM data. Labels are user_folder-based and were not human-audited.",
    ])


# %% ======================================================================
# 12. DEPLOY: resolver + CLI + REST API (stdlib)
# =========================================================================
class IdentityResolver:
    def __init__(self, bundle_path: str):
        self.b = joblib.load(bundle_path)
        self.emb = Embedder(self.b["st_model"], self.b["use_semantic"]) if self.b["use_semantic"] else None
        if self.b["use_semantic"] and not (self.emb and self.emb.ok):
            raise RuntimeError("bundle needs sentence-transformers for semantic features")

    def _prep(self, records) -> pd.DataFrame:
        raw = pd.DataFrame(records)
        for c in ["username", "fullname", "bio", "location", "externalurl", "platform"]:
            if c not in raw:
                alt = {"username": "userName", "fullname": "fullName", "externalurl": "externalUrl"}.get(c)
                raw[c] = raw[alt] if alt in raw else ""
        raw["user_folder"] = "x"
        df, _ = prepare(raw)
        return df

    def _score(self, df: pd.DataFrame, pairs: np.ndarray) -> pd.DataFrame:
        emb = None
        if self.b["use_semantic"]:
            emb = {f: self.emb.encode(df[f].tolist()) for f in ["fullname", "bio"]}
        S = static_features(df, pairs, emb)
        T = tfidf_features(df, pairs, self.b["field_vectorizers"])
        X = pd.concat([S, T], axis=1)[self.b["feature_cols"]]
        raw = np.mean([m.predict_proba(X)[:, 1] for m in self.b["models"]], 0)
        p = self.b["calibrator"](raw)
        ns = np.maximum(S["username_jw"].values, S["fullname_jw"].values)
        d = policy_decide(self.b["policy_name"], self.b["policy_params"], p, ns)
        lab = np.array(["NO_MATCH", "REVIEW", "MATCH"])[d]
        return pd.DataFrame({"a": pairs[:, 0], "b": pairs[:, 1], "probability": p.round(6), "decision": lab})

    def score_pair(self, a: dict, b: dict) -> dict:
        df = self._prep([a, b])
        r = self._score(df, np.array([[0, 1]]))
        return {"probability": float(r["probability"][0]), "decision": r["decision"][0]}

    def link(self, records) -> pd.DataFrame:
        df = self._prep(records)
        X = self.b["blocker_vectorizer"].transform(profile_text(df).values)
        cands = knn_scored_pairs(df, X, self.b["knn_k"])
        if cands.empty:
            return pd.DataFrame(columns=["a", "b", "probability", "decision"])
        res = self._score(df, cands[["a", "b"]].values.astype(np.int64))
        for side in ("a", "b"):
            res[f"{side}_platform"] = df["platform"].values[res[side].values]
            res[f"{side}_username"] = df["username"].values[res[side].values]
        return res.sort_values("probability", ascending=False).reset_index(drop=True)


def cmd_predict(args):
    r = IdentityResolver(args.bundle)
    recs = pd.read_csv(args.input, dtype=str, keep_default_na=False).to_dict("records")
    res = r.link(recs)
    res.to_csv(args.output, index=False)
    print(res["decision"].value_counts().to_string())
    print(f"saved -> {args.output}")


def cmd_serve(args):
    from http.server import BaseHTTPRequestHandler, HTTPServer
    resolver = IdentityResolver(args.bundle)

    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"status": "ok", "policy": resolver.b["policy_name"]})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            try:
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                if self.path == "/score":
                    return self._send(200, resolver.score_pair(data["a"], data["b"]))
                if self.path == "/link":
                    return self._send(200, resolver.link(data["profiles"]).to_dict("records"))
                self._send(404, {"error": "not found"})
            except Exception as e:
                self._send(400, {"error": f"{type(e).__name__}: {e}"})

    print(f"serving on http://{args.host}:{args.port}  (GET /health, POST /score, POST /link)")
    HTTPServer((args.host, args.port), H).serve_forever()


# %% ======================================================================
# CLI
# =========================================================================
def main():
    ap = argparse.ArgumentParser(description="Cross-platform identity resolution: full experiment in one file")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the whole experiment (CRISP-DM -> deploy bundle)")
    r.add_argument("--data", help="merged profiles CSV or LinkSocial JSON folder")
    r.add_argument("--demo", action="store_true", help="use synthetic data")
    r.add_argument("--out", default="runs/demo")
    r.add_argument("--quick", action="store_true", help="small budgets for a smoke test")
    r.add_argument("--paper", action="store_true", help="protocol budgets (GBDT 200 configs, bootstrap 10,000, policy 2,048 x 10 seeds)")
    r.add_argument("--no-semantic", action="store_true")
    p = sub.add_parser("predict", help="link profiles in a CSV with a deployed bundle")
    p.add_argument("--bundle", required=True); p.add_argument("--input", required=True); p.add_argument("--output", default="decisions.csv")
    s = sub.add_parser("serve", help="REST API with a deployed bundle")
    s.add_argument("--bundle", required=True); s.add_argument("--port", type=int, default=8000)
    s.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 only if other machines must reach the API (no auth)")
    args = ap.parse_args()

    if args.cmd == "predict":
        return cmd_predict(args)
    if args.cmd == "serve":
        return cmd_serve(args)
    cfg = Config(out=args.out, data=args.data, demo=args.demo, use_semantic=not args.no_semantic)
    if args.quick:
        cfg.gbdt_trials, cfg.model_seeds, cfg.policy_budget, cfg.policy_seeds = 4, (11, 42), 128, (0, 1)
        cfg.bootstrap_B, cfg.rule_draws = 200, 100
    if args.paper:
        cfg.gbdt_trials, cfg.policy_budget, cfg.policy_seeds, cfg.bootstrap_B = 200, 2048, tuple(range(10)), 10000
    run(cfg)


if __name__ == "__main__":
    main()
