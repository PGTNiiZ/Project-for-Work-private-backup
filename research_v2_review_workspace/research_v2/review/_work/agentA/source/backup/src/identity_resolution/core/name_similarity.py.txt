"""Pure, bounded name-similarity primitives for identity-resolution features."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

from rapidfuzz import fuzz
from rapidfuzz.distance import DamerauLevenshtein


def normalize_name(value: object) -> str:
    """Return a Unicode-normalized, case-folded name or handle."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    return re.sub(r"\s+", " ", text.lstrip("@").strip())


def _non_empty_pair(left: object, right: object) -> tuple[str, str] | None:
    left_text, right_text = normalize_name(left), normalize_name(right)
    return (left_text, right_text) if left_text and right_text else None


def damerau_similarity(left: object, right: object) -> float:
    """Normalized Damerau-Levenshtein similarity, with empty values scored as zero."""
    pair = _non_empty_pair(left, right)
    if pair is None:
        return 0.0
    left_text, right_text = pair
    distance = DamerauLevenshtein.distance(left_text, right_text)
    return 1.0 - distance / max(len(left_text), len(right_text))


def token_set_similarity(left: object, right: object) -> float:
    """RapidFuzz token-set similarity normalized to the closed interval [0, 1]."""
    pair = _non_empty_pair(left, right)
    return fuzz.token_set_ratio(*pair) / 100.0 if pair is not None else 0.0


def char_ngram_cosine(left: object, right: object, ngram_size: int = 3) -> float:
    """Cosine similarity of character n-gram counts without corpus-level fitting."""
    if ngram_size < 1:
        raise ValueError("ngram_size must be positive")
    pair = _non_empty_pair(left, right)
    if pair is None:
        return 0.0
    left_text, right_text = pair
    left_grams = [left_text[index:index + ngram_size] for index in range(max(len(left_text) - ngram_size + 1, 1))]
    right_grams = [right_text[index:index + ngram_size] for index in range(max(len(right_text) - ngram_size + 1, 1))]
    left_counts, right_counts = Counter(left_grams), Counter(right_grams)
    dot_product = sum(left_counts[gram] * right_counts[gram] for gram in left_counts.keys() & right_counts.keys())
    left_norm = math.sqrt(sum(count * count for count in left_counts.values()))
    right_norm = math.sqrt(sum(count * count for count in right_counts.values()))
    return dot_product / (left_norm * right_norm) if left_norm and right_norm else 0.0


def compact_handle(value: object) -> str:
    """Remove common handle separators while preserving letters and digits."""
    return re.sub(r"[\W_]+", "", normalize_name(value), flags=re.UNICODE)


def handle_features(left: object, right: object) -> dict[str, float]:
    """Return bounded signals for formatting variants of social-media handles."""
    left_handle, right_handle = compact_handle(left), compact_handle(right)
    if not left_handle or not right_handle:
        return {"exact": 0.0, "prefix": 0.0, "suffix": 0.0, "length_ratio": 0.0, "available": 0.0}
    shortest = min(len(left_handle), len(right_handle))
    prefix = 0
    while prefix < shortest and left_handle[prefix] == right_handle[prefix]:
        prefix += 1
    suffix = 0
    while suffix < shortest and left_handle[-(suffix + 1)] == right_handle[-(suffix + 1)]:
        suffix += 1
    longest = max(len(left_handle), len(right_handle))
    return {
        "exact": float(left_handle == right_handle),
        "prefix": prefix / longest,
        "suffix": suffix / longest,
        "length_ratio": shortest / longest,
        "available": 1.0,
    }


def latin_soundex(value: object) -> str:
    """Return a four-character Soundex code for Latin-only text, otherwise an empty code."""
    text = normalize_name(value)
    if not text or not re.fullmatch(r"[a-z ]+", text):
        return ""
    letters = text.replace(" ", "")
    codes = {
        **dict.fromkeys("bfpv", "1"),
        **dict.fromkeys("cgjkqsxz", "2"),
        **dict.fromkeys("dt", "3"),
        "l": "4",
        **dict.fromkeys("mn", "5"),
        "r": "6",
    }
    result = [letters[0].upper()]
    previous = codes.get(letters[0], "")
    for letter in letters[1:]:
        code = codes.get(letter, "")
        if code and code != previous:
            result.append(code)
        previous = code
        if len(result) == 4:
            break
    return "".join(result).ljust(4, "0")


def latin_soundex_match(left: object, right: object) -> float:
    """Return phonetic agreement for Latin names and zero when either value is unavailable."""
    left_code, right_code = latin_soundex(left), latin_soundex(right)
    return float(bool(left_code and left_code == right_code))