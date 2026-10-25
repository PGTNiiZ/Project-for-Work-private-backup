"""Schema กลางสำหรับทุกชั้นของ holdout

records.csv หนึ่งแถว = หนึ่งบัญชี/เรคคอร์ด
ground truth: record สองตัวที่ entity_id เดียวกันแต่ source ต่างกัน = คู่ที่ตรงกัน
"""
from __future__ import annotations

import pandas as pd

COLUMNS = [
    "record_id",       # unique ทั้งไฟล์
    "source",          # ชื่อแพลตฟอร์ม/ตาราง เช่น github, bluesky, febrl_a
    "entity_id",       # คนเดียวกัน = ค่าเดียวกัน
    "username",
    "full_name",
    "bio",
    "external_url",
    "profile_pic_url",
    "location",
]


def to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """เติมคอลัมน์ที่ขาดเป็นค่าว่าง เรียงคอลัมน์ และตรวจความถูกต้องพื้นฐาน"""
    out = df.copy()
    for col in COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[COLUMNS].fillna("")
    for col in COLUMNS:
        out[col] = out[col].astype(str).str.strip()
    if out["record_id"].duplicated().any():
        dup = out.loc[out["record_id"].duplicated(), "record_id"].head().tolist()
        raise ValueError(f"record_id ซ้ำ เช่น {dup}")
    if (out["entity_id"] == "").any():
        raise ValueError("มีแถวที่ entity_id ว่าง")
    return out


def write_records(df: pd.DataFrame, path: str) -> pd.DataFrame:
    out = to_schema(df)
    out.to_csv(path, index=False, encoding="utf-8")
    n_pairs = len(gold_pairs(out))
    print(f"เขียน {len(out):,} records ({out['source'].value_counts().to_dict()}), "
          f"gold pairs ข้าม source = {n_pairs:,} → {path}")
    return out


def read_records(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def gold_pairs(records: pd.DataFrame, src_left: str | None = None,
               src_right: str | None = None) -> set[tuple[str, str]]:
    """คืนเซตคู่ (left_record_id, right_record_id) ที่ตรงกัน

    ถ้าระบุ src_left/src_right จะคืนเฉพาะคู่ของสอง source นั้น
    ถ้าไม่ระบุ จะคืนทุกคู่ข้าม source (เรียง source ตามตัวอักษร)
    """
    pairs: set[tuple[str, str]] = set()
    for _, g in records.groupby("entity_id"):
        if g["source"].nunique() < 2:
            continue
        rows = g[["record_id", "source"]].values.tolist()
        for rid_a, src_a in rows:
            for rid_b, src_b in rows:
                if src_a == src_b:
                    continue
                if src_left is not None:
                    if src_a == src_left and src_b == src_right:
                        pairs.add((rid_a, rid_b))
                elif src_a < src_b:
                    pairs.add((rid_a, rid_b))
    return pairs
