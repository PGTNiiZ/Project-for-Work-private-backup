"""Build the ICSEC authoritative cross-platform candidate artifacts.

This script is intentionally separate from historical runners. It calls the
current production candidate-generation implementation and writes only
non-identifying row IDs plus aggregate evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from identity_resolution.workflows import full_candidate as fc

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "icsec_final" / "authoritative_run"
CAND = OUT / "candidates"


def key(a: int, b: int) -> int:
    x, y = (a, b) if a < b else (b, a)
    return (x << 32) | y


def unpack(value: int) -> tuple[int, int]:
    return value >> 32, value & 0xFFFFFFFF


def entity_hash(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def build_gt(profiles: pd.DataFrame) -> set[int]:
    gt: set[int] = set()
    eligible = profiles[profiles["user_folder"].astype(str).str.strip() != ""]
    for _, group in eligible.groupby("user_folder", sort=False):
        rows = group[["profile_row_id", "platform"]].to_records(index=False)
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if rows[i][1] != rows[j][1]:
                    gt.add(key(int(rows[i][0]), int(rows[j][0])))
    return gt


def pair_frame(keys: set[int], source: str, gt: set[int],
               profiles: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for value in sorted(keys):
        a, b = unpack(value)
        rows.append({"profile_row_id_a": a, "profile_row_id_b": b,
                     "source": source, "actual": int(value in gt)})
    return pd.DataFrame(rows)


def main() -> None:
    CAND.mkdir(parents=True, exist_ok=False)
    profiles = fc.load_profiles()
    profiles = profiles[profiles["profile_row_id"].notna() & profiles["profile_id"].notna()].copy()
    profiles["profile_row_id"] = profiles["profile_row_id"].astype(int)
    gt = build_gt(profiles)
    exact, exact_counts = fc.build_exact_match_pairs(profiles)
    blocked, block_counts = fc.build_candidate_pairs(profiles, exact)
    workflow = exact | blocked
    all_cross = fc.count_cross_platform_all_pairs(profiles)
    misses = gt - workflow

    # Ensure the production function did not accidentally produce same-platform pairs.
    by_row = profiles.set_index("profile_row_id")["platform"]
    for value in workflow:
        a, b = unpack(value)
        assert by_row[a] != by_row[b]
    assert exact.isdisjoint(blocked)
    assert len(exact) + len(blocked) == len(workflow)
    assert len(gt) == len(workflow & gt) + len(misses)

    exact_df = pair_frame(exact, "AUTO_EXACT", gt, profiles)
    scored_df = pair_frame(blocked, "MODEL_SCORED", gt, profiles)
    workflow_df = pd.concat([exact_df, scored_df], ignore_index=True)
    workflow_df.to_parquet(CAND / "candidate_workflow.parquet", index=False)
    exact_df.to_parquet(CAND / "exact_tier_decisions.parquet", index=False)
    scored_df.to_parquet(CAND / "model_scored_candidates.parquet", index=False)

    prof_lookup = profiles.set_index("profile_row_id")
    miss_rows = []
    for value in sorted(misses):
        a, b = unpack(value)
        ua = str(prof_lookup.loc[a, "user_folder"])
        ub = str(prof_lookup.loc[b, "user_folder"])
        assert ua == ub and ua.strip()
        miss_rows.append({
            "profile_row_id_a": a,
            "profile_row_id_b": b,
            "platform_a": str(prof_lookup.loc[a, "platform"]),
            "platform_b": str(prof_lookup.loc[b, "platform"]),
            "entity_key_sha256": entity_hash(ua),
        })
    pd.DataFrame(miss_rows).to_parquet(CAND / "blocking_missed_positives.parquet", index=False)
    pd.DataFrame(miss_rows).to_csv(CAND / "blocking_missed_positives.csv", index=False)

    # Aggregate positive proof, with no entity or profile text.
    all_positive = 0
    same_platform = 0
    cross_platform = 0
    for _, group in profiles[profiles["user_folder"].astype(str).str.strip() != ""].groupby("user_folder", sort=False):
        n = len(group)
        all_positive += n * (n - 1) // 2
        platforms = group["platform"].tolist()
        for i in range(n):
            for j in range(i + 1, n):
                if platforms[i] == platforms[j]:
                    same_platform += 1
                else:
                    cross_platform += 1
    assert all_positive == cross_platform + same_platform
    report = {
        "protocol_version": "authoritative_run_v1",
        "profiles_eligible": int(len(profiles)),
        "platform_counts": {str(k): int(v) for k, v in profiles["platform"].value_counts().items()},
        "all_platform_positives": int(all_positive),
        "cross_platform_positives": int(cross_platform),
        "same_platform_positives": int(same_platform),
        "possible_cross_platform_pairs": int(all_cross),
        "exact_tier_pairs": int(len(exact)),
        "model_scored_candidate_pairs": int(len(blocked)),
        "workflow_candidate_pairs": int(len(workflow)),
        "candidate_covered_cross_platform_positives": int(len(workflow & gt)),
        "cross_platform_blocking_misses": int(len(misses)),
        "retrieval_recall": float(len(workflow & gt) / cross_platform),
        "candidate_space_reduction": float(1 - len(workflow) / all_cross),
        "exact_tier_breakdown": {str(k): int(v) for k, v in exact_counts.items()},
        "blocking_key_breakdown": {str(k): int(v) for k, v in block_counts.items()},
        "invariants": {
            "exact_plus_scored_equals_workflow": len(exact) + len(blocked) == len(workflow),
            "covered_plus_missed_equals_cross_positive": len(workflow & gt) + len(misses) == cross_platform,
            "all_equals_cross_plus_same": all_positive == cross_platform + same_platform,
        },
    }
    (CAND / "candidate_scope.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
