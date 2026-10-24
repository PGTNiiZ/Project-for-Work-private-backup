"""Deterministic, label-free handcrafted features for authoritative v2."""
from __future__ import annotations

import math
import unicodedata
from collections.abc import Sequence

from rapidfuzz import fuzz
from rapidfuzz.distance import Jaro, JaroWinkler, Levenshtein


FEATURE17_COLUMNS = [
    "username_jaro", "username_lev_sim", "username_token_sort",
    "fullname_jaro", "fullname_lev_sim", "fullname_token_sort", "name_sim",
    "bio_jaccard", "bio_len_ratio", "both_have_bio", "location_jaro",
    "location_exact", "both_have_location", "same_platform",
    "username_len_diff", "fullname_wordcount_diff", "username_prefix3_match",
]
FEATURE18_COLUMNS = FEATURE17_COLUMNS + ["bert_cos"]


def _normalize(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().strip().lstrip("@").split())


def corrected_name_sim(
    username_a: Sequence[object],
    fullname_a: Sequence[object],
    username_b: Sequence[object],
    fullname_b: Sequence[object],
) -> list[float]:
    """Max four cross-field Jaro-Winkler similarities, with no model/label gate.

    Inputs are pair-aligned sequences. Missing values contribute no candidate;
    a pair with no available comparison returns exactly 0.0.
    """
    if not (len(username_a) == len(fullname_a) == len(username_b) == len(fullname_b)):
        raise ValueError("name feature inputs must have equal lengths")
    result: list[float] = []
    for ua, fa, ub, fb in zip(username_a, fullname_a, username_b, fullname_b):
        left = [_normalize(ua), _normalize(fa)]
        right = [_normalize(ub), _normalize(fb)]
        scores = [JaroWinkler.similarity(x, y) for x in left for y in right if x and y]
        result.append(float(max(scores, default=0.0)))
    return result


def build_handcrafted_features(pairs, profiles):
    """Generate all corrected GB-17 columns from pair keys and profile text."""
    import pandas as pd

    required = {"profile_row_id_a", "profile_row_id_b"}
    if not required.issubset(pairs.columns):
        raise ValueError("pairs must contain profile_row_id_a/profile_row_id_b")
    profile_index = profiles.set_index("profile_row_id", drop=False)
    fields = {name: [] for name in ("userName", "fullName", "bio", "location", "platform")}
    base_fields = tuple(fields)
    for side in ("a", "b"):
        ids = pairs[f"profile_row_id_{side}"].astype("int64")
        for field in base_fields:
            fields[field + "_" + side] = [_normalize(v) for v in profile_index.loc[ids, field]]

    def sim(left, right):
        return float(Jaro.similarity(left, right)) if left and right else 0.0

    def lev_sim(left, right):
        if not left or not right:
            return 0.0
        return float(1.0 - Levenshtein.distance(left, right) / max(len(left), len(right)))

    def token_sort(left, right):
        return float(fuzz.token_sort_ratio(left, right) / 100.0) if left and right else 0.0

    rows = []
    for i in range(len(pairs)):
        ua, ub = fields["userName_a"][i], fields["userName_b"][i]
        fa, fb = fields["fullName_a"][i], fields["fullName_b"][i]
        ba, bb = fields["bio_a"][i], fields["bio_b"][i]
        la, lb = fields["location_a"][i], fields["location_b"][i]
        name_values = corrected_name_sim([ua], [fa], [ub], [fb])
        bio_a, bio_b = set(ba.split()), set(bb.split())
        max_bio = max(len(ba), len(bb))
        max_user = max(len(ua), len(ub))
        max_words = max(len(fa.split()), len(fb.split()))
        rows.append({
            "profile_row_id_a": int(pairs.iloc[i].profile_row_id_a),
            "profile_row_id_b": int(pairs.iloc[i].profile_row_id_b),
            "username_jaro": sim(ua, ub),
            "username_lev_sim": lev_sim(ua, ub),
            "username_token_sort": token_sort(ua, ub),
            "fullname_jaro": sim(fa, fb),
            "fullname_lev_sim": lev_sim(fa, fb),
            "fullname_token_sort": token_sort(fa, fb),
            "name_sim": name_values[0],
            "bio_jaccard": len(bio_a & bio_b) / len(bio_a | bio_b) if (bio_a or bio_b) else 0.0,
            "bio_len_ratio": min(len(ba), len(bb)) / max_bio if max_bio else 0.0,
            "both_have_bio": float(bool(ba and bb)),
            "location_jaro": sim(la, lb),
            "location_exact": float(bool(la and la == lb)),
            "both_have_location": float(bool(la and lb)),
            "same_platform": float(bool(fields["platform_a"][i] and fields["platform_a"][i] == fields["platform_b"][i])),
            "username_len_diff": abs(len(ua) - len(ub)) / max_user if max_user else 0.0,
            "fullname_wordcount_diff": abs(len(fa.split()) - len(fb.split())) / max_words if max_words else 0.0,
            "username_prefix3_match": float(len(ua) >= 3 and len(ub) >= 3 and ua[:3] == ub[:3]),
        })
    result = pd.DataFrame(rows)
    for column in FEATURE17_COLUMNS:
        result[column] = result[column].astype("float32")
    return result[["profile_row_id_a", "profile_row_id_b", *FEATURE17_COLUMNS]]
