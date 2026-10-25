"""แปลง COSNET (AMiner, Zhang et al. KDD 2015) เป็น schema กลาง (ชั้นที่ 1B)

ยังไม่ได้ยืนยันรูปแบบไฟล์ของ COSNET ฉบับที่ดาวน์โหลดได้ตอนนี้
ขั้นตอน:
  1. ดาวน์โหลดแล้วรัน:  python tier1/prepare_cosnet.py --inspect <โฟลเดอร์>
     สคริปต์จะพิมพ์รายชื่อไฟล์และ 5 บรรทัดแรกของแต่ละไฟล์
  2. เติม load_profiles() และ load_ground_truth() ให้ตรงกับไฟล์จริง
  3. รัน:  python tier1/prepare_cosnet.py --data <โฟลเดอร์> --left twitter --right livejournal

ห้ามปรับ pipeline หลังจากเห็นข้อมูลชุดนี้ การ inspect ทำได้เฉพาะเพื่อเขียน parser
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.schema import write_records  # noqa: E402


def inspect(folder: Path) -> None:
    for p in sorted(folder.rglob("*")):
        if p.is_file():
            print(f"\n=== {p.relative_to(folder)} ({p.stat().st_size:,} bytes)")
            try:
                with p.open(encoding="utf-8", errors="replace") as f:
                    for _ in range(5):
                        line = f.readline()
                        if not line:
                            break
                        print("   ", line.rstrip()[:200])
            except OSError as e:
                print("    อ่านไม่ได้:", e)


def load_profiles(folder: Path, platform: str) -> pd.DataFrame:
    """คืน DataFrame คอลัมน์ platform_user_id, username, full_name, bio,
    external_url, profile_pic_url, location (คอลัมน์ที่ไม่มีละไว้ได้)"""
    raise NotImplementedError("เติมตามรูปแบบไฟล์จริงหลัง --inspect")


def load_ground_truth(folder: Path, left: str, right: str) -> pd.DataFrame:
    """คืน DataFrame คอลัมน์ left_user_id, right_user_id (คู่ที่เป็นคนเดียวกัน)"""
    raise NotImplementedError("เติมตามรูปแบบไฟล์จริงหลัง --inspect")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", type=Path)
    ap.add_argument("--data", type=Path)
    ap.add_argument("--left")
    ap.add_argument("--right")
    ap.add_argument("--out", default="tier1/out_cosnet/records.csv")
    args = ap.parse_args()

    if args.inspect:
        inspect(args.inspect)
        return

    L = load_profiles(args.data, args.left).astype({"platform_user_id": str})
    R = load_profiles(args.data, args.right).astype({"platform_user_id": str})
    gt = load_ground_truth(args.data, args.left, args.right).astype(str)

    # entity_id: คู่ใน gt ใช้ id ร่วม, คนที่ไม่มีคู่ใช้ id ของตัวเอง (เป็น negative)
    ent_l = {u: f"e{i}" for i, u in enumerate(gt.left_user_id)}
    ent_r = {u: f"e{i}" for i, u in enumerate(gt.right_user_id)}
    L["entity_id"] = [ent_l.get(u, f"{args.left}-only:{u}") for u in L.platform_user_id]
    R["entity_id"] = [ent_r.get(u, f"{args.right}-only:{u}") for u in R.platform_user_id]
    L["source"], R["source"] = args.left, args.right
    L["record_id"] = args.left + ":" + L.platform_user_id
    R["record_id"] = args.right + ":" + R.platform_user_id

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_records(pd.concat([L, R], ignore_index=True), args.out)


if __name__ == "__main__":
    main()
