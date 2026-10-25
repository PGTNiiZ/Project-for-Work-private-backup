"""NC Voters (Leipzig, 5-party) → schema กลาง สำหรับชั้นที่ 2

readme ระบุฟิลด์: recId (ค่าเดียวกัน = คนเดียวกัน), givenname, surname, postcode, suburb
แต่ละไฟล์ใน tar.gz = 1 source, source ละ 1,000,000 เรคคอร์ด

ขนาดใหญ่เกินจำเป็น จึงเลือก 2 source แล้วสุ่ม N recId ที่อยู่ในทั้งสอง source
บวก non-match จากแต่ละฝั่งอีก N เพื่อให้มี record ที่ไม่มีคู่ (ใกล้สถานการณ์จริง)

ขั้นตอน:
  1. tar -xzf 5Party-ocp20.tar.gz -C data/ncvoters
  2. python tier2/prepare_ncvoters.py --inspect data/ncvoters
     ดูชื่อไฟล์ ตัวคั่น และชื่อคอลัมน์ เทียบกับ readme
  3. python tier2/prepare_ncvoters.py --left <ไฟล์ A> --right <ไฟล์ B> --n 5000
     (ถ้าไฟล์ไม่มี header ใช้ --names recid,givenname,surname,postcode,suburb)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.schema import write_records  # noqa: E402

WANTED = {"recid": "recid", "givenname": "givenname", "surname": "surname",
          "postcode": "postcode", "suburb": "suburb"}


def inspect(folder: Path) -> None:
    for p in sorted(folder.rglob("*")):
        if p.is_file():
            print(f"\n=== {p.name} ({p.stat().st_size/1e6:.1f} MB)")
            with p.open(encoding="utf-8", errors="replace") as f:
                for _ in range(3):
                    print("   ", f.readline().rstrip()[:200])


def read_source(path: Path, sep: str | None, names: list[str] | None) -> pd.DataFrame:
    df = pd.read_csv(path, sep=sep, engine="python" if sep is None else "c",
                     names=names, header=None if names else "infer",
                     dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
    missing = [c for c in WANTED if c not in df.columns]
    if missing:
        raise SystemExit(f"{path.name}: ไม่พบคอลัมน์ {missing} (มี {list(df.columns)}) "
                         "ลองใช้ --names หรือ --sep")
    return df[list(WANTED)]


def to_rows(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    return pd.DataFrame({
        "record_id": source + ":" + df.index.astype(str),
        "source": source,
        "entity_id": "nc-" + df["recid"].str.strip(),
        "full_name": (df["givenname"].str.strip() + " " + df["surname"].str.strip()).str.strip(),
        "location": (df["suburb"].str.strip() + " " + df["postcode"].str.strip()).str.strip(),
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", type=Path)
    ap.add_argument("--left", type=Path)
    ap.add_argument("--right", type=Path)
    ap.add_argument("--n", type=int, default=5000, help="จำนวนคู่ที่ตรงกัน")
    ap.add_argument("--sep", default=None)
    ap.add_argument("--names", default=None)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", default="tier2/out/ncvoters_records.csv")
    args = ap.parse_args()

    if args.inspect:
        inspect(args.inspect)
        return

    names = args.names.split(",") if args.names else None
    A = read_source(args.left, args.sep, names)
    B = read_source(args.right, args.sep, names)

    common = sorted(set(A.recid) & set(B.recid))
    print(f"recId ร่วมกัน {len(common):,} จาก {len(A):,} / {len(B):,}")
    sample = pd.Series(common).sample(min(args.n, len(common)), random_state=args.seed)
    pick = set(sample)

    only_a = A[~A.recid.isin(set(B.recid))].sample(min(args.n, len(A)), random_state=args.seed)
    only_b = B[~B.recid.isin(set(A.recid))].sample(min(args.n, len(B)), random_state=args.seed + 1)
    A_s = pd.concat([A[A.recid.isin(pick)], only_a]).drop_duplicates()
    B_s = pd.concat([B[B.recid.isin(pick)], only_b]).drop_duplicates()

    # ถ้า recId ซ้ำภายใน source เดียว เก็บเรคคอร์ดแรก
    A_s = A_s.drop_duplicates("recid")
    B_s = B_s.drop_duplicates("recid")

    out = pd.concat([to_rows(A_s, "nc_a"), to_rows(B_s, "nc_b")], ignore_index=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_records(out, args.out)


if __name__ == "__main__":
    main()
