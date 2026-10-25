"""วัดค่า --reuse ของชั้น 3 จาก LinkSocial dev data (aggregate เท่านั้น ไม่พิมพ์ค่าโปรไฟล์)

นิยาม: สัดส่วนของ gold cross-platform pairs (user_folder เดียวกัน, platform ต่างกัน) ที่ username
หลัง normalize (NFKC + casefold + trim + ตัด '@' นำหน้า + ยุบช่องว่าง; ฟังก์ชันเดียวกับ features V2)
เหมือนกันและไม่ว่าง — คิดเฉพาะ entity ที่อยู่ใน development (ไม่ใช่ SEALED_TEST) ของแต่ละ outer seed
ตามกฎ role ของ V2/V2R1 (MD5 "entity_nested_v2:{seed}:{entity}" % 100 < 30 → SEALED_TEST)

รัน (จาก repo root):  .venv/bin/python holdout_eval/tools/measure_reuse.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from experiments.icsec_final.authoritative_run_v2.features import _normalize  # noqa: E402
from identity_resolution.workflows import full_candidate as fc  # noqa: E402


def is_test(entity: str, seed: int) -> bool:
    return int(hashlib.md5(f"entity_nested_v2:{seed}:{entity}".encode()).hexdigest(), 16) % 100 < 30


def main() -> None:
    prof = fc.load_profiles()
    out = {"eligible_profiles": int(len(prof)), "per_seed": {}}
    for seed in (101, 202, 303):
        n = same = 0
        for ent, g in prof.groupby("user_folder", sort=False):
            ent = str(ent).strip()
            if not ent or is_test(ent, seed):
                continue
            rows = list(zip(g.platform, g.userName.map(_normalize)))
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    if rows[i][0] == rows[j][0]:
                        continue
                    n += 1
                    same += int(bool(rows[i][1]) and rows[i][1] == rows[j][1])
        out["per_seed"][str(seed)] = {"dev_gold_pairs": n, "identical_username_pairs": same,
                                      "fraction": round(same / n, 6)}
    out["reuse_mean_of_seeds"] = round(sum(v["fraction"] for v in out["per_seed"].values()) / 3, 4)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
