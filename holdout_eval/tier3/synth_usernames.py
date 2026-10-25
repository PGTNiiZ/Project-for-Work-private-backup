"""ชั้นที่ 3: สร้าง username สังเคราะห์จาก full_name (sensitivity analysis เท่านั้น)

*** ห้ามรายงานผลจากไฟล์ที่สคริปต์นี้สร้างเป็นผล confirmatory ***
ทุกไฟล์ output มีคอลัมน์ synthetic_noise_level กำกับไว้

Input:  records.csv จากชั้นที่ 2 (Febrl4 หรือ NC Voters)
Output: <out_dir>/records_noise_<level>.csv หนึ่งไฟล์ต่อระดับ noise

สองฝั่งของคู่เดียวกันใช้ seed ต่างกัน (ขึ้นกับ record_id) จึงมักได้ username ต่างรูปแบบ
เหมือนคนจริงที่ตั้งชื่อต่างกันในแต่ละแพลตฟอร์ม

รัน:
python tier3/synth_usernames.py --records tier2/out/febrl4_records.csv \
    --levels 0 0.1 0.2 0.3 0.4 0.5 --out tier3/out/febrl4
"""
from __future__ import annotations

import argparse
import hashlib
import random
import re
import string
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.schema import read_records, write_records  # noqa: E402

LEET = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
WORDS = ["sky", "runner", "pixel", "wolf", "coffee", "night", "byte", "river",
         "storm", "lucky", "ghost", "panda", "neo", "zen", "echo", "nova"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


def base_username(first: str, last: str, rng: random.Random) -> str:
    sep = rng.choice(["", "", "_", "."])
    options = []
    if first and last:
        options += [first + sep + last, last + sep + first,
                    first[0] + sep + last, first + sep + last[0]]
    options += [first or last]
    return rng.choice([o for o in options if o]) or "user"


def typo(u: str, rng: random.Random) -> str:
    if len(u) < 3:
        return u
    i = rng.randrange(len(u) - 1)
    op = rng.choice(["del", "swap", "sub"])
    if op == "del":
        return u[:i] + u[i + 1:]
    if op == "swap":
        return u[:i] + u[i + 1] + u[i] + u[i + 2:]
    return u[:i] + rng.choice(string.ascii_lowercase) + u[i + 1:]


def make_username(full_name: str, level: float, rng: random.Random,
                  preferred: str | None = None) -> str:
    """preferred = username หลักของคนนั้น (ใช้แทนการสุ่มรูปแบบใหม่ เมื่อจำลองการใช้ชื่อซ้ำ)"""
    parts = norm(full_name).split()
    first, last = (parts[0], parts[-1]) if len(parts) >= 2 else ((parts or [""])[0], "")

    if rng.random() < level * 0.5:          # ไม่เกี่ยวกับชื่อเลย
        return rng.choice(WORDS) + rng.choice(WORDS) + str(rng.randrange(100))

    u = preferred or base_username(first, last, rng)
    if rng.random() < level:                # เติมตัวเลข
        u += str(rng.choice([rng.randrange(10, 100), rng.randrange(1960, 2010)]))
    if rng.random() < level and len(u) > 5: # ตัดท้าย
        u = u[: rng.randrange(4, len(u))]
    if rng.random() < level:                # พิมพ์ผิด
        u = typo(u, rng)
    if rng.random() < level * 0.5:          # leetspeak
        u = "".join(LEET.get(c, c) if rng.random() < 0.5 else c for c in u)
    return u


def seeded_rng(base_seed: int, level: float, record_id: str) -> random.Random:
    h = hashlib.sha256(f"{base_seed}|{level}|{record_id}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--levels", type=float, nargs="+", default=[0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ap.add_argument("--reuse", type=float, default=0.3829,
                    help="ความน่าจะเป็นที่คนใช้ username หลักเดิมซ้ำข้ามแพลตฟอร์ม — ค่าเริ่มต้นวัดจาก "
                         "LinkSocial dev data (tools/measure_reuse.py; ดู RUN_LOG.md 2026-10-26)")
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = read_records(args.records)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for level in args.levels:
        df = base.copy()
        usernames = []
        for n, rid, ent in zip(df.full_name, df.record_id, df.entity_id):
            rng = seeded_rng(args.seed, level, rid)
            pref = None
            if rng.random() < args.reuse:
                # username หลักของ entity (เหมือนกันทุก record ของคนเดียวกัน)
                ent_rng = seeded_rng(args.seed, -1.0, "entity:" + ent)
                p = norm(n).split()
                pref = base_username(p[0] if p else "", p[-1] if len(p) > 1 else "", ent_rng)
            usernames.append(make_username(n, level, rng, pref))
        df["username"] = usernames
        path = out_dir / f"records_noise_{level:.1f}.csv"
        write_records(df, str(path))
        # แท็กกำกับว่าเป็นข้อมูลสังเคราะห์ (คอลัมน์เพิ่ม ไม่กระทบ schema กลาง)
        written = read_records(str(path))
        written["synthetic_noise_level"] = f"{level:.1f}"
        written.to_csv(path, index=False, encoding="utf-8")
        g = df.groupby("entity_id").username
        same = g.nunique()[g.size() == 2] == 1
        print(f"  noise {level:.1f}: คู่ที่ username เหมือนกันเป๊ะ {same.mean():.1%}")


if __name__ == "__main__":
    main()
