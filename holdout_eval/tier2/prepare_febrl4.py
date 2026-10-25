"""Febrl4 → schema กลาง สำหรับชั้นที่ 2 (ทดสอบเฉพาะโมดูลชื่อ + location)

ตัดออก: date_of_birth, soc_sec_id (โซเชียลไม่มี ทำให้งานง่ายเกินจริง)
        street_number, address_1, address_2 (โปรไฟล์โซเชียลระบุแค่ระดับเมือง)
เก็บ:   given_name + surname → full_name
        suburb, state, postcode → location (รูปแบบ "suburb, state postcode")

ต้องติดตั้ง:  pip install recordlinkage
รัน:         python tier2/prepare_febrl4.py --out tier2/out/febrl4_records.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.schema import write_records  # noqa: E402

DROPPED = ["date_of_birth", "soc_sec_id", "street_number", "address_1", "address_2"]


def clean(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().replace({"nan": ""})


def location(df: pd.DataFrame) -> pd.Series:
    sub, state, pc = clean(df["suburb"]), clean(df["state"]), clean(df["postcode"])
    tail = (state + " " + pc).str.strip()
    return (sub + ", " + tail).str.strip(", ").str.strip()


def to_rows(df: pd.DataFrame, source: str, entity: dict[str, str]) -> pd.DataFrame:
    df = df.drop(columns=[c for c in DROPPED if c in df.columns])
    full = (clean(df["given_name"]) + " " + clean(df["surname"])).str.strip()
    return pd.DataFrame({
        "record_id": source + ":" + df.index.astype(str),
        "source": source,
        "entity_id": [entity.get(i, f"{source}-only:{i}") for i in df.index],
        "full_name": full.values,
        "location": location(df).values,
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="tier2/out/febrl4_records.csv")
    args = ap.parse_args()

    from recordlinkage.datasets import load_febrl4
    df_a, df_b, links = load_febrl4(return_links=True)

    # entity id จาก links ที่ชุดข้อมูลให้มา (ไม่ parse จากชื่อ rec_id)
    ent_a, ent_b = {}, {}
    for i, (a, b) in enumerate(links):
        ent_a[a] = ent_b[b] = f"febrl-e{i}"

    out = pd.concat([to_rows(df_a, "febrl_a", ent_a), to_rows(df_b, "febrl_b", ent_b)],
                    ignore_index=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_records(out, args.out)
    print("ฟิลด์ที่ตัดออก:", ", ".join(DROPPED))


if __name__ == "__main__":
    main()
