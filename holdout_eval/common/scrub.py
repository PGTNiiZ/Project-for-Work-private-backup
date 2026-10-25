"""ลบการอ้างอิงบัญชีของอีกแพลตฟอร์มออกจาก bio / external_url (กัน label leakage)

gold ของชั้น 1A สร้างจากลิงก์ GitHub → Bluesky จึงต้องไม่ให้ลิงก์/handle นั้นหลุดเข้าโมเดล
ไม่แตะ username (การใช้ handle ซ้ำข้ามแพลตฟอร์มเป็นสัญญาณที่ถูกต้อง)

จับแบบ case-insensitive; ตัวอักษรความกว้างศูนย์ถูกมองข้าม; ตัวอักษรหน้าตาเหมือน (NFKC,
fullwidth, Cyrillic/Greek ที่คล้าย latin) ถูกแปลงเป็น latin ก่อนเทียบ
ข้อความที่ถูกลบคืนเป็นช่องว่างในข้อความต้นฉบับ (ไม่ได้ normalize ข้อความที่เหลือ)
"""
from __future__ import annotations

import re
import unicodedata

ZERO_WIDTH = {"​", "‌", "‍", "‎", "‏", "⁠", "﻿", "­"}
LOOKALIKE = {  # Cyrillic/Greek → latin (เฉพาะตัวที่หน้าตาเหมือนมาก)
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i",
    "ј": "j", "ѕ": "s", "ԁ": "d", "һ": "h", "ԛ": "q", "ɡ": "g",
    "α": "a", "ε": "e", "ο": "o", "ρ": "p", "ν": "v", "τ": "t", "ι": "i", "κ": "k",
}


def fold(text: str) -> tuple[str, list[int]]:
    """คืน (ข้อความ folded, index ต้นฉบับของแต่ละตัวอักษร)"""
    out, idx = [], []
    for i, ch in enumerate(text):
        if ch in ZERO_WIDTH:
            continue
        for c in unicodedata.normalize("NFKC", ch).casefold():
            if c in ZERO_WIDTH:
                continue
            out.append(LOOKALIKE.get(c, c))
            idx.append(i)
    return "".join(out), idx


def patterns(gh_login: str, handle: str, side: str) -> dict[str, re.Pattern]:
    """side='github' = ข้อความจากโปรไฟล์ GitHub (ลบอ้างอิง Bluesky)
    side='target' = ข้อความจากโปรไฟล์ปลายทาง (ลบอ้างอิง GitHub)"""
    def f(s: str) -> str:
        return re.escape(fold(s)[0])
    sp = r"[\s]*"
    if side == "github":
        h = f(handle)
        return {
            "bsky_url": re.compile(rf"(?:https?://)?(?:www\.)?bsky\.app/profile/{h}(?![a-z0-9-])"),
            "at_handle": re.compile(rf"@{h}(?![a-z0-9-])"),
            "bare_handle": re.compile(rf"(?<![a-z0-9@-]){h}(?![a-z0-9-])"),
        }
    g = f(gh_login)
    return {
        "github_url": re.compile(rf"(?:https?://)?(?:www\.)?github\.com/{g}(?![a-z0-9-])"),
        "github_io": re.compile(rf"(?:https?://)?{g}\.github\.io(?![a-z0-9-])"),
        "gh_prefix": re.compile(rf"(?<![a-z0-9])gh{sp}:{sp}@?{g}(?![a-z0-9-])"),
        "github_prefix": re.compile(rf"(?<![a-z0-9])github{sp}:{sp}@?{g}(?![a-z0-9-])"),
        "at_login_on_github": re.compile(rf"@{g}{sp}on{sp}github"),
    }


def scrub(text: str, pats: dict[str, re.Pattern]) -> tuple[str, set[str]]:
    """คืน (ข้อความหลัง scrub, ชื่อ pattern ที่เจอ)"""
    if not text:
        return "", set()
    folded, idx = fold(text)
    drop, hit = set(), set()
    for name, p in pats.items():
        for m in p.finditer(folded):
            if m.end() > m.start():
                hit.add(name)
                drop.update(range(idx[m.start()], idx[m.end() - 1] + 1))
    if not hit:
        return re.sub(r"\s+", " ", text).strip(), hit
    kept = "".join(" " if i in drop else c for i, c in enumerate(text))
    return re.sub(r"\s+", " ", kept).strip(), hit
