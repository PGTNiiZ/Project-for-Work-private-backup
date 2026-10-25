"""เก็บคู่บัญชี GitHub ↔ Bluesky หรือ X เป็น confirmatory holdout (ชั้นที่ 1)

Ground truth: บัญชีโซเชียลที่เจ้าของผูกไว้เองใน GitHub
  GET /users/{login}/social_accounts  → [{provider, url}, ...]

ต้องมี:
  GITHUB_TOKEN   (personal access token, ไม่ต้องให้สิทธิ์พิเศษ; rate limit 5,000 req/ชม.)
  X_BEARER_TOKEN (เฉพาะ --target x; ต้องมีสิทธิ์ users lookup ของ X API)
Bluesky ใช้ public API ไม่ต้อง login

ตัวอย่าง:
python tier1/collect_github_social.py --target bluesky --pairs 1200 --out tier1/out

ผลลัพธ์:
  <out>/records.csv   schema กลาง (source = github / bluesky หรือ x)
  <out>/raw.jsonl     ข้อมูลดิบทุกคู่ (เก็บไว้ตรวจสอบย้อนหลัง)
  <out>/progress.json จุดที่สุ่มไปแล้ว (รันต่อได้)

ก่อนเก็บจริง ตรวจ ToS ของแต่ละแพลตฟอร์มและ ethics approval ของมหาวิทยาลัย
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.schema import write_records  # noqa: E402
from common.scrub import patterns, scrub  # noqa: E402

GH = "https://api.github.com"
BSKY = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile"
X_API = "https://api.x.com/2/users/by/username/{}"
MAX_GH_ID = 230_000_000
STOP_BIO_REMOVED = 0.20  # STOP (c): สัดส่วนตัวอักษร bio (ทั้งสองฝั่ง ทุกคู่) ที่ scrub ลบออก  # ขอบบนโดยประมาณของ user id ปัจจุบัน ปรับได้


class GitHub:
    def __init__(self, token: str):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}",
                               "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28"})

    def get(self, path: str, **params):
        while True:
            r = self.s.get(GH + path, params=params, timeout=30)
            if r.status_code in (403, 429) and r.headers.get("X-RateLimit-Remaining") == "0":
                wait = int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time() + 5
                print(f"  GitHub rate limit — รอ {wait/60:.1f} นาที")
                time.sleep(max(wait, 5))
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()


def handle_from_url(url: str, provider: str) -> str | None:
    """ดึง handle จาก URL ของ social account"""
    try:
        p = urlparse(url if "://" in url else "https://" + url)
    except ValueError:
        return None
    parts = [x for x in p.path.split("/") if x]
    if provider == "bluesky":
        # https://bsky.app/profile/<handle>
        if "profile" in parts and parts.index("profile") + 1 < len(parts):
            return parts[parts.index("profile") + 1].lower()
        return None
    if provider == "twitter":
        if p.netloc.lower().removeprefix("www.") in {"twitter.com", "x.com", "mobile.twitter.com"} and parts:
            return parts[0].lstrip("@").lower()
    return None


def fetch_bluesky(handle: str) -> dict | None:
    r = requests.get(BSKY, params={"actor": handle}, timeout=30)
    if r.status_code != 200:
        return None
    d = r.json()
    return {"username": d.get("handle", ""), "full_name": d.get("displayName", ""),
            "bio": d.get("description", ""), "external_url": "",
            "profile_pic_url": d.get("avatar", ""), "location": "",
            "platform_id": d.get("did", "")}


def fetch_x(handle: str, token: str) -> dict | None:
    r = requests.get(X_API.format(handle), timeout=30,
                     headers={"Authorization": f"Bearer {token}"},
                     params={"user.fields": "description,location,name,profile_image_url,url,entities"})
    if r.status_code == 429:
        reset = int(r.headers.get("x-rate-limit-reset", time.time() + 900))
        time.sleep(max(reset - time.time() + 5, 5))
        return fetch_x(handle, token)
    if r.status_code != 200 or "data" not in r.json():
        return None
    d = r.json()["data"]
    # ใช้ expanded URL ถ้ามี (url ของ X เป็น t.co)
    url = d.get("url", "")
    for u in d.get("entities", {}).get("url", {}).get("urls", []):
        url = u.get("expanded_url", url)
    return {"username": d.get("username", ""), "full_name": d.get("name", ""),
            "bio": d.get("description", ""), "external_url": url,
            "profile_pic_url": d.get("profile_image_url", ""),
            "location": d.get("location", ""), "platform_id": d.get("id", "")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["bluesky", "x"], default="bluesky")
    ap.add_argument("--pairs", type=int, default=1200, help="จำนวนคู่ที่ต้องการ")
    ap.add_argument("--out", default="tier1/out")
    ap.add_argument("--seed", type=int, default=20261026)
    args = ap.parse_args()

    gh_token = os.environ.get("GITHUB_TOKEN") or sys.exit("ต้องตั้ง GITHUB_TOKEN")
    x_token = os.environ.get("X_BEARER_TOKEN")
    if args.target == "x" and not x_token:
        sys.exit("ต้องตั้ง X_BEARER_TOKEN สำหรับ --target x")
    provider = "bluesky" if args.target == "bluesky" else "twitter"

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prog_path, raw_path = out / "progress.json", out / "raw.jsonl"
    progress = json.loads(prog_path.read_text()) if prog_path.exists() else {"seen": [], "pairs": 0}
    seen = set(progress["seen"])

    gh = GitHub(gh_token)
    rng = random.Random(args.seed + len(seen))
    n_pairs = progress["pairs"]

    with raw_path.open("a", encoding="utf-8") as raw:
        while n_pairs < args.pairs:
            since = rng.randrange(0, MAX_GH_ID)
            batch = gh.get("/users", since=since, per_page=100) or []
            for u in batch:
                login = u["login"]
                if login in seen or u.get("type") != "User":
                    continue
                seen.add(login)
                accounts = gh.get(f"/users/{login}/social_accounts") or []
                handle = None
                for a in accounts:
                    if a.get("provider") == provider:
                        handle = handle_from_url(a.get("url", ""), provider)
                        break
                if not handle:
                    continue
                prof = gh.get(f"/users/{login}")
                if not prof:
                    continue
                tgt = fetch_bluesky(handle) if args.target == "bluesky" else fetch_x(handle, x_token)
                if not tgt:
                    continue
                raw.write(json.dumps({"github": prof, "target": tgt, "handle": handle},
                                     ensure_ascii=False) + "\n")
                n_pairs += 1
                print(f"[{n_pairs}/{args.pairs}] {login} ↔ {handle}")
                if n_pairs >= args.pairs:
                    break
            progress = {"seen": sorted(seen), "pairs": n_pairs}
            prog_path.write_text(json.dumps(progress))

    # สร้าง records.csv จาก raw.jsonl (scrub leakage ตอนนี้ เก็บ raw ไว้ไม่แตะ)
    # นับเฉพาะ aggregate: จำนวนโปรไฟล์ที่ถูก scrub ต่อ side ต่อ pattern (ไม่ log ค่า)
    rows, flags = [], []
    counts: collections.Counter = collections.Counter()
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        g, t, handle = d["github"], d["target"], d["handle"]
        ent = f"gh:{g['id']}"
        gp = patterns(g["login"], handle, "github")
        tp = patterns(g["login"], handle, "target")
        g_bio_raw, t_bio_raw = g.get("bio") or "", t["bio"] or ""
        g_bio, h1 = scrub(g_bio_raw, gp)
        g_url, h2 = scrub(g.get("blog") or "", gp)
        t_bio, h3 = scrub(t_bio_raw, tp)
        for raw_bio, new_bio in ((g_bio_raw, g_bio), (t_bio_raw, t_bio)):
            before = len(re.sub(r"\s+", " ", raw_bio).strip())
            counts["bio_chars_total"] += before
            counts["bio_chars_removed"] += max(before - len(new_bio), 0)
        counts["pairs_with_bio_scrubbed"] += bool(h1 or h3)
        t_url, h4 = scrub(t["external_url"], tp)
        hits = {"github": h1 | h2, args.target: h3 | h4}
        for side, names in hits.items():
            counts[f"{side}.profiles_scrubbed"] += bool(names)
            for n in names:
                counts[f"{side}.{n}"] += 1
        flags.append({"entity_id": ent, "flag": int(any(hits.values()))})
        rows.append({"record_id": f"github:{g['id']}", "source": "github", "entity_id": ent,
                     "username": g.get("login", ""), "full_name": g.get("name") or "",
                     "bio": g_bio, "external_url": g_url,
                     "profile_pic_url": g.get("avatar_url", ""),
                     "location": g.get("location") or ""})
        rows.append({"record_id": f"{args.target}:{t['platform_id'] or handle}",
                     "source": args.target, "entity_id": ent,
                     "username": t["username"], "full_name": t["full_name"],
                     "bio": t_bio, "external_url": t_url,
                     "profile_pic_url": t["profile_pic_url"], "location": t["location"]})
    n_pairs_built = len(flags)
    counts["pairs"] = n_pairs_built
    counts["pairs_with_scrubbed_reference"] = sum(f["flag"] for f in flags)
    removed = counts["bio_chars_removed"] / counts["bio_chars_total"] if counts["bio_chars_total"] else 0.0
    summary = dict(sorted(counts.items()))
    summary["bio_content_removed_fraction"] = round(removed, 6)
    summary["pairs_with_bio_scrubbed_fraction"] = (round(counts["pairs_with_bio_scrubbed"] / n_pairs_built, 6)
                                                    if n_pairs_built else 0.0)
    (out / "scrub_counts.json").write_text(json.dumps(summary, indent=2))
    if removed > STOP_BIO_REMOVED:
        # STOP condition (c) ของผู้วิจัย: scrub ลบเนื้อหา bio ของคู่ holdout เกิน 20% → หยุดและถามผู้วิจัย
        sys.exit(f"STOP (c): scrub removed {removed:.1%} of holdout bio content (> {STOP_BIO_REMOVED:.0%}); "
                 "records.csv NOT written — ask the researcher")
    pd.DataFrame(flags).to_csv(out / "strata.csv", index=False)
    print("scrub counts:", dict(sorted(counts.items())))
    df = pd.DataFrame(rows).drop_duplicates("record_id")
    write_records(df, str(out / "records.csv"))


if __name__ == "__main__":
    main()
