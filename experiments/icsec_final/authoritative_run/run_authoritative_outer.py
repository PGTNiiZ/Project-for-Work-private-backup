"""Fresh authoritative ICSEC outer runs using current experiment logic."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from experiments.code import exp_lib
from experiments.code import exp_r1_ga_redecision as ga
from experiments.code import run_gb_transformer_experiments as base
from experiments.code.run_icsec_repeated_outer import outer_role

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "icsec_final" / "authoritative_run"
CAND = OUT / "candidates"
FEATURE17 = ROOT / "experiments" / "pair_features17.parquet"
BERT = ROOT / "experiments" / "pair_bert_cos.parquet"
SEEDS = [101, 202, 303]


def hash_entity(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def pair_digest(frame: pd.DataFrame) -> str:
    ordered = frame[["profile_id_a", "profile_id_b"]].astype("int64").sort_values(["profile_id_a", "profile_id_b"])
    return hashlib.sha256("\n".join(f"{a},{b}" for a, b in ordered.itertuples(index=False, name=None)).encode()).hexdigest()


def build_cache() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, set[int]]:
    profiles = base.pd.read_csv(ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv", keep_default_na=False, low_memory=False)
    profiles["profile_row_id"] = pd.to_numeric(profiles["profile_row_id"], errors="coerce").astype("Int64")
    profiles = profiles[profiles["profile_row_id"].notna()].copy()
    profiles["profile_row_id"] = profiles["profile_row_id"].astype(int)
    by_id = profiles.set_index("profile_row_id")
    workflow = pd.read_parquet(CAND / "candidate_workflow.parquet")
    misses = pd.read_parquet(CAND / "blocking_missed_positives.parquet")
    cache = workflow.rename(columns={"source": "decision_source", "profile_row_id_a": "profile_id_a", "profile_row_id_b": "profile_id_b"})
    cache["split"] = [exp_lib.bucket(str(by_id.loc[a, "user_folder"])) == "test" and "test" or "val" for a in cache.profile_id_a]
    cache["actual"] = cache["actual"].astype(np.int8)
    scored_mask = cache["decision_source"] != "AUTO_EXACT"
    feat17 = pd.read_parquet(FEATURE17)
    bert = pd.read_parquet(BERT)
    assert len(cache[scored_mask]) == len(feat17) == len(bert)
    assert set(map(tuple, cache[scored_mask][["profile_id_a", "profile_id_b"]].to_numpy())) == set(map(tuple, feat17[["profile_id_a", "profile_id_b"]].to_numpy()))
    feature_name = feat17[["profile_id_a", "profile_id_b", "name_sim"]]
    cache = cache.merge(feature_name, on=["profile_id_a", "profile_id_b"], how="left", validate="one_to_one", sort=False)
    cache.loc[cache["decision_source"] == "AUTO_EXACT", "name_sim"] = 0.0
    assert cache["name_sim"].notna().all()
    miss_keys = {(int(a) << 32) | int(b) for a, b in misses[["profile_row_id_a", "profile_row_id_b"]].itertuples(index=False, name=None)}
    return cache, feat17, bert, misses, miss_keys


def constants(assigned: pd.DataFrame, misses: pd.DataFrame, profiles: pd.DataFrame, seed: int) -> dict[str, dict[str, int]]:
    by_id = profiles.set_index("profile_row_id")
    miss_roles = []
    for a, b in misses[["profile_row_id_a", "profile_row_id_b"]].itertuples(index=False, name=None):
        entity = str(by_id.loc[int(a), "user_folder"])
        assert entity == str(by_id.loc[int(b), "user_folder"])
        miss_roles.append(outer_role(entity, seed))
    miss_test = int(sum(role == "test" for role in miss_roles))
    out = {}
    for role in ("model_train", "model_calibration", "ga_validation", "test"):
        exact = assigned[(assigned.decision_source == "AUTO_EXACT") & (assigned.experiment_split == role)]
        scored = assigned[(assigned.decision_source != "AUTO_EXACT") & (assigned.experiment_split == role)]
        missed = miss_test if role == "test" else 0
        out[role] = {
            "tp_exact": int((exact.actual == 1).sum()),
            "fp_exact": int((exact.actual == 0).sum()),
            "fn_blocking": missed,
            "total_pos": int((scored.actual == 1).sum()) + int((exact.actual == 1).sum()) + missed,
            "n_scored": int(len(scored)),
        }
    return out


def main() -> None:
    if (OUT / "outer_101").exists():
        raise FileExistsError("authoritative outer output already exists")
    cache, feat17, bert, misses, miss_keys = build_cache()
    profiles = base.pd.read_csv(ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv", keep_default_na=False, low_memory=False)
    profiles["profile_row_id"] = pd.to_numeric(profiles["profile_row_id"], errors="coerce").astype("Int64")
    profiles = profiles[profiles["profile_row_id"].notna()].copy()
    profiles["profile_row_id"] = profiles["profile_row_id"].astype(int)
    keys = exp_lib.entity_keys_by_profile()
    # The cache uses profile_row_id under the historical column names.
    events = {"test_label_requests_before_final": 0, "test_label_requests_after_final": 0}
    original_labels_for = base.labels_for
    final_eval = False
    def guarded_labels_for(assigned, keys_frame, role, allow_test=False):
        nonlocal final_eval
        if role == "test":
            if not final_eval or not allow_test:
                events["test_label_requests_before_final"] += 1
                raise AssertionError("test labels requested before final evaluation")
            events["test_label_requests_after_final"] += 1
        return original_labels_for(assigned, keys_frame, role, allow_test=allow_test)
    base.labels_for = guarded_labels_for
    all_rows = []
    for seed in SEEDS:
        d = OUT / f"outer_{seed}"; d.mkdir(parents=True); (d / "model").mkdir()
        seeded = cache.copy()
        a = seeded.profile_id_a.map(keys); b = seeded.profile_id_b.map(keys)
        seeded["split"] = np.where(
            a.map(lambda x: outer_role(str(x), seed)) == b.map(lambda x: outer_role(str(x), seed)),
            a.map(lambda x: outer_role(str(x), seed)), "drop")
        assigned, manifest = exp_lib.build_nested_entity_split(seeded, seed=seed, entity_keys=keys)
        work = base.validate_inputs(seeded, feat17, bert, assigned)
        const = constants(assigned, misses, profiles, seed)
        p17, m17 = base.train_gb_variant("GB-17", base.FEATURE17_COLS.copy(), work, assigned, d, 42)
        p18, m18 = base.train_gb_variant("GB-18", base.FEATURE17_COLS + ["bert_cos"], work, assigned, d, 42)
        p17f = pd.read_parquet(d / "gb17_probabilities.parquet")
        p18f = pd.read_parquet(d / "gb18_probabilities.parquet")
        trials, generations, selection = base.run_ga_trials(work, assigned, p18f, const, base.GA_SEEDS, d)
        test_mask = work.experiment_split.to_numpy() == "test"
        test_work = work.loc[test_mask].copy()
        final_eval = True
        y = base.labels_for(assigned, test_work[base.KEY_COLS], "test", allow_test=True)
        genome = np.array([selection["selected_genome"][k] for k in ("t_m", "t_r", "c_promote", "c_demote")])
        decisions = {
            "GB-17": base.manual_decision(p17[test_mask]),
            "GB-18": base.manual_decision(p18f.loc[test_mask, "probability_gb18"].to_numpy()),
            "GB-18-GA": ga.decide_code(p18f.loc[test_mask, "probability_gb18"].to_numpy(), test_work.name_sim.to_numpy(), genome),
        }
        names = {0: "NO_MATCH", 1: "REVIEW", 2: "MATCH"}
        for method, decision in decisions.items():
            method_dir = d / method.replace("-", "_"); method_dir.mkdir()
            exact = assigned[(assigned.experiment_split == "test") & (assigned.decision_source == "AUTO_EXACT")][["profile_id_a", "profile_id_b", "actual"]].copy()
            exact["decision"] = "MATCH"; exact["scope"] = "exact_tier"
            scored = test_work[["profile_id_a", "profile_id_b"]].copy()
            scored["actual"] = y
            scored["decision"] = [names[int(v)] for v in decision]; scored["scope"] = "model_scored"
            miss_roles = []
            for a_id, b_id in misses[["profile_row_id_a", "profile_row_id_b"]].itertuples(index=False, name=None):
                entity = str(profiles.loc[profiles.profile_row_id == int(a_id), "user_folder"].iloc[0])
                if outer_role(entity, seed) == "test":
                    miss_roles.append({"profile_id_a": int(a_id), "profile_id_b": int(b_id), "actual": 1, "decision": "NO_MATCH", "scope": "blocking_missed"})
            blocking = pd.DataFrame(miss_roles)
            workflow = pd.concat([exact, scored, blocking], ignore_index=True)
            for name, frame in [("exact_tier_decisions.parquet", exact), ("model_scored_decisions.parquet", scored), ("blocking_missed_positives.parquet", blocking), ("workflow_decisions.parquet", workflow)]:
                frame.to_parquet(method_dir / name, index=False)
            metric = base.metric_with_cost(decision, y, const["test"], base.GA_WEIGHTS)
            all_rows.append({"outer_seed": seed, "method": method, **metric, "candidate_recall": 1 - const["test"]["fn_blocking"] / const["test"]["total_pos"], "blocking_missed": const["test"]["fn_blocking"]})
        (d / "training_metadata.json").write_text(json.dumps({"GB-17": m17, "GB-18": m18}, indent=2))
        pd.DataFrame(trials).to_csv(d / "ga_trials.csv", index=False); pd.DataFrame(generations).to_csv(d / "ga_generations.csv", index=False)
        (d / "selected_policy.json").write_text(json.dumps(selection, indent=2))
        # Hashed entity manifest only; raw entity identifiers are never exported.
        entity_roles = {}
        for role in ("model_train", "model_calibration", "ga_validation", "test"):
            role_frame = assigned[assigned.experiment_split == role]
            ids = set(keys.loc[role_frame.profile_id_a]).union(set(keys.loc[role_frame.profile_id_b]))
            entity_roles[role] = sorted(hash_entity(str(v)) for v in ids)
        manifest.update({"outer_seed": seed, "entity_assignment": "MD5(icsec-outer-v1:seed:entity_key) < 30 => test; entity_nested_v1 development allocation", "hashed_entity_keys": entity_roles, "constants": const, "test_label_access_audit": events.copy()})
        (d / "split_manifest.json").write_text(json.dumps(manifest, indent=2))
        final_eval = False
    pd.DataFrame(all_rows).to_csv(OUT / "runner_outputs.csv", index=False)
    (OUT / "label_access_audit.json").write_text(json.dumps(events, indent=2))
    print(json.dumps({"rows": len(all_rows), "label_access": events}, indent=2))


if __name__ == "__main__":
    main()
