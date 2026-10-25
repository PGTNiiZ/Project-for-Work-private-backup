"""บันทึกสถานะ pipeline ก่อนแตะ holdout

ตัวอย่าง:
python -m common.freeze \
    --repo ../Project-for-Work \
    --files ../Project-for-Work/models/final.pkl ../Project-for-Work/config.yaml \
    --threshold 0.62 \
    --decision-rule "ขอบล่าง 95% CI ของ F1 บน tier1 >= 0.70" \
    --out freeze_manifest.json

จากนั้น commit freeze_manifest.json เข้า repo ก่อนเปิดข้อมูล holdout
evaluate.py จะเช็ก hash ของไฟล์ซ้ำตอนประเมิน ถ้าไม่ตรงจะเตือน
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info(repo: str) -> dict:
    def run(*args):
        return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    try:
        return {
            "commit": run("rev-parse", "HEAD"),
            "dirty": bool(run("status", "--porcelain")),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--files", nargs="+", required=True,
                    help="ไฟล์โมเดล, config, รายชื่อฟีเจอร์ ฯลฯ ที่ต้อง freeze")
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--decision-rule", required=True)
    ap.add_argument("--possible-threshold", type=float,
                    help="เกณฑ์ POSSIBLE_MATCH (secondary, ไม่ใช่ confirmatory)")
    ap.add_argument("--reference-f1", type=float,
                    help="F1 บน LinkSocial ระดับ end-to-end ที่ใช้เทียบ")
    ap.add_argument("--delta", type=float, help="ค่า tolerance ของ decision rule")
    ap.add_argument("--primary-metric", default="f1")
    ap.add_argument("--out", default="freeze_manifest.json")
    args = ap.parse_args()

    git = git_info(args.repo)
    if "error" in git:
        raise SystemExit(f"อ่านสถานะ git ไม่ได้: {git['error']}")
    if git["dirty"]:
        raise SystemExit("ไม่ freeze: repo มีการแก้ไข/ไฟล์ใหม่ที่ยังไม่ commit — commit หรือ ignore ก่อน")

    manifest = {
        "frozen_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git": git,
        "files": {str(Path(p)): sha256(p) for p in args.files},
        "threshold": args.threshold,
        "possible_threshold": args.possible_threshold,
        "reference_f1": args.reference_f1,
        "delta": args.delta,
        "primary_metric": args.primary_metric,
        "decision_rule": args.decision_rule,
        "bootstrap": {"n": 1000, "ci": 0.95, "unit": "left entity"},
    }
    Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(f"บันทึก {args.out} แล้ว — commit ไฟล์นี้ก่อนเปิด holdout")


if __name__ == "__main__":
    main()
