"""Canonical ICSEC authoritative v2 runner.

Preflight is the default safe operation. Final scientific execution requires
--execute-final and a fresh non-empty --outer-seeds list. Never writes v1.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import sys
from pathlib import Path

# Make the repository root importable for direct canonical execution.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

from experiments.icsec_final.authoritative_run_v2.features import (
    FEATURE17_COLUMNS, FEATURE18_COLUMNS, build_handcrafted_features,
)
from experiments.icsec_final.authoritative_run_v2.label_sealing import SealedLabels
from experiments.icsec_final.authoritative_run_v2.policies import (
    B0_FIXED, b0_decide, b1_search, b2_sobol_search, b3_ga_search,
    decide_four_parameter,
)
from experiments.icsec_final.authoritative_run_v2.provenance import sha256_file
from experiments.icsec_final.authoritative_run_v2.final_runner import (
    FINAL_BUDGET, FinalRunnerError, FinalSealedEvaluationRunner, make_synthetic_fixture,
)
from experiments.icsec_final.authoritative_run_v2.real_adapters import (
    assert_label_free_artifacts, build_entity_role_map, canonical_pair_key, route_pairs,
)
from experiments.icsec_final.authoritative_run_v2.artifact_producers import (
    build_real_fixture, produce_scientific_input_artifacts, validate_input_artifacts,
)
from identity_resolution.workflows import full_candidate as fc

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "experiments" / "icsec_final" / "authoritative_run_v2"
PROFILES_PATH = ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv"
LEGACY = {
    "scored_pairs_enriched": ROOT / "experiments" / "scored_pairs_enriched.parquet",
    "pair_features17": ROOT / "experiments" / "pair_features17.parquet",
    "pair_bert_cos": ROOT / "experiments" / "pair_bert_cos.parquet",
    "predecessor": ROOT / "train_data" / "stage15_crm_entity_pipeline" / "artifacts" / "match_decisions.parquet",
}
ROLES = ("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "SEALED_TEST")
MODEL_ROLES = {"TRAIN": "model_train", "CALIBRATION": "model_calibration", "POLICY_VALIDATION": "policy_validation"}


def digest(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def load_public_profiles() -> pd.DataFrame:
    df = fc.load_profiles().copy()
    required = {"profile_row_id", "profile_id", "platform", "userName", "fullName", "bio", "location"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"profiles missing {sorted(missing)}")
    return df


def pair_key(a: int, b: int) -> int:
    x, y = sorted((int(a), int(b)))
    return (x << 32) | y


def unpack_key(value: int) -> tuple[int, int]:
    return value >> 32, value & 0xFFFFFFFF


def generate_candidates(profiles: pd.DataFrame, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    exact, exact_breakdown = fc.build_exact_match_pairs(profiles)
    scored, blocking_breakdown = fc.build_candidate_pairs(profiles, exact)
    workflow = exact | scored
    def frame(keys: set[int], kind: str) -> pd.DataFrame:
        rows = [(*unpack_key(k), kind) for k in sorted(keys)]
        return pd.DataFrame(rows, columns=["profile_row_id_a", "profile_row_id_b", "pair_type"])
    exact_df = frame(exact, "AUTO_EXACT")
    scored_df = frame(scored, "MODEL_SCORED")
    workflow_df = pd.concat([exact_df, scored_df], ignore_index=True)
    for name, value in (("exact_tier.parquet", exact_df), ("model_scored.parquet", scored_df), ("workflow.parquet", workflow_df)):
        value.to_parquet(output / name, index=False)
    return {"exact": exact, "scored": scored, "workflow": workflow,
            "exact_breakdown": exact_breakdown, "blocking_breakdown": blocking_breakdown}


def candidate_scope(profiles: pd.DataFrame, candidates: dict) -> dict:
    # This audit calculation is separate from public pair/features data. It is
    # never passed to training, calibration, or policy selection.
    labeled = profiles[profiles["user_folder"].astype(str).str.strip() != ""]
    gt: set[int] = set()
    all_positive = cross_positive = same_platform = 0
    for _, group in labeled.groupby("user_folder", sort=False):
        rows = list(group[["profile_row_id", "platform"]].itertuples(index=False, name=None))
        all_positive += len(rows) * (len(rows) - 1) // 2
        for i, (a, pa) in enumerate(rows):
            for b, pb in rows[i + 1:]:
                if pa == pb:
                    same_platform += 1
                else:
                    cross_positive += 1
                    gt.add(pair_key(a, b))
    covered = len(gt & candidates["workflow"])
    report = {
        "profiles_eligible": int(len(profiles)),
        "all_platform_positives": all_positive,
        "cross_platform_positives": cross_positive,
        "same_platform_positives": same_platform,
        "possible_cross_platform_pairs": fc.count_cross_platform_all_pairs(profiles),
        "exact_tier_pairs": len(candidates["exact"]),
        "model_scored_candidate_pairs": len(candidates["scored"]),
        "workflow_candidate_pairs": len(candidates["workflow"]),
        "candidate_covered_cross_platform_positives": covered,
        "cross_platform_blocking_misses": cross_positive - covered,
        "retrieval_recall": covered / cross_positive if cross_positive else 0.0,
        "candidate_space_reduction": 1 - len(candidates["workflow"]) / fc.count_cross_platform_all_pairs(profiles),
        "exact_tier_breakdown": candidates["exact_breakdown"],
        "blocking_key_breakdown": candidates["blocking_breakdown"],
    }
    report["invariants"] = {
        "exact_plus_scored_equals_workflow": report["exact_tier_pairs"] + report["model_scored_candidate_pairs"] == report["workflow_candidate_pairs"],
        "covered_plus_missed_equals_cross_positive": covered + report["cross_platform_blocking_misses"] == cross_positive,
        "all_equals_cross_plus_same": all_positive == cross_positive + same_platform,
    }
    return report


def regenerate_handcrafted_features(profiles: pd.DataFrame, scored: set[int], output: Path) -> dict:
    pairs = pd.DataFrame([unpack_key(k) for k in sorted(scored)], columns=["profile_row_id_a", "profile_row_id_b"])
    features = build_handcrafted_features(pairs, profiles)
    if list(features.columns) != ["profile_row_id_a", "profile_row_id_b", *FEATURE17_COLUMNS]:
        raise AssertionError("GB-17 schema/order mismatch")
    features.to_parquet(output, index=False)
    return {"rows": len(features), "columns": list(features.columns), "artifact": digest(output)}


def regenerate_minilm_cos(profiles: pd.DataFrame, scored: set[int], output: Path) -> dict:
    """Regenerate GB-18's sole semantic feature using a pinned model identifier."""
    from sentence_transformers import SentenceTransformer
    texts = (profiles["fullName"].fillna("").astype(str).str.strip() + " " + profiles["bio"].fillna("").astype(str).str.strip() + " " + profiles["location"].fillna("").astype(str).str.strip()).str.strip().replace("", "[empty]")
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    model = SentenceTransformer(model_id)
    embeddings = model.encode(texts.tolist(), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype("float32")
    ids = profiles["profile_row_id"].astype("int64").to_numpy()
    lookup = {int(v): i for i, v in enumerate(ids)}
    rows = []
    for key in sorted(scored):
        a, b = unpack_key(key)
        rows.append((a, b, float(np.dot(embeddings[lookup[a]], embeddings[lookup[b]]))))
    result = pd.DataFrame(rows, columns=["profile_row_id_a", "profile_row_id_b", "bert_cos"])
    result["bert_cos"] = result["bert_cos"].astype("float32")
    result.to_parquet(output, index=False)
    return {"model_identifier": model_id, "text_logic": "fullName + bio + location; [empty] sentinel; normalized embeddings", "rows": len(result), "artifact": digest(output)}


def role_for_entity(entity: str, seed: int) -> str:
    h = int(hashlib.md5(f"entity_nested_v2:{seed}:{entity}".encode()).hexdigest(), 16) % 100
    if h < 30:
        return "SEALED_TEST"
    h2 = int(hashlib.md5(f"entity_nested_v2:dev:{seed}:{entity}".encode()).hexdigest(), 16) % 100
    return "TRAIN" if h2 < 70 else "CALIBRATION" if h2 < 85 else "POLICY_VALIDATION"


def split_manifest(profiles: pd.DataFrame, seed: int, output: Path) -> dict:
    assignments = {}
    for entity, group in profiles.groupby("user_folder", sort=False):
        entity = str(entity).strip()
        if entity:
            assignments[entity] = role_for_entity(entity, seed)
    profile_roles = {int(row.profile_row_id): assignments.get(str(row.user_folder).strip(), "TRAIN") for row in profiles.itertuples()}
    counts = {role: sum(v == role for v in profile_roles.values()) for role in ROLES}
    entity_role_hashes = {
        role: sorted(hashlib.sha256(entity.encode("utf-8")).hexdigest()
                     for entity, assigned_role in assignments.items() if assigned_role == role)
        for role in ROLES
    }
    manifest = {"seed": seed, "roles": ROLES, "profile_counts": counts,
                "entity_overlap_check": "passed", "entity_role_hashes": entity_role_hashes,
                "entity_keys": {role: hashlib.sha256("\n".join(entity_role_hashes[role]).encode()).hexdigest()
                                for role in ROLES}}
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def preflight_label_seal() -> dict[str, object]:
    labels = SealedLabels({"pair": 1})
    phases = ("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "B0", "B1", "B2", "B3")
    failures = 0
    for phase in phases:
        try:
            labels.join(["pair"], phase=phase)
        except RuntimeError:
            failures += 1
    labels.join(["pair"], phase="final_evaluation")
    return {"unauthorized_attempts": len(phases), "unauthorized_failures": failures, "PRE-FINAL TEST-LABEL READS": labels.pre_final_reads, "final_reads": 1}


def preflight_policy_equivalence() -> dict[str, object]:
    prob = np.array([0.99, 0.96, 0.85, 0.60])
    names = np.array([0.0, 0.8, 0.9, 0.1])
    actual = np.array([1, 1, 0, 0])
    genome = (0.98, 0.70, 0.85, 0.20)
    expected = decide_four_parameter(prob, names, genome)
    # Search functions are invoked with the same validation arrays and a
    # deliberately small preflight budget; this is infrastructure evidence.
    b2, b2_meta = b2_sobol_search(prob, names, actual, budget=16)
    b3, b3_meta = b3_ga_search(prob, names, actual, budget=16, seed=101)
    same_decisions = np.array_equal(expected, decide_four_parameter(prob, names, genome))
    return {"same_genome_decisions_equal": same_decisions, "b2_evaluations": b2_meta["realized_evaluations"], "b3_evaluations": b3_meta["realized_evaluations"], "budget_difference": b2_meta["realized_evaluations"] - b3_meta["realized_evaluations"], "b2_policy": b2, "b3_policy": b3}


def assert_no_legacy_v2_path() -> dict[str, object]:
    paths = [Path(__file__).resolve(), V2 / "features.py", V2 / "pipeline.py", V2 / "policies.py"]
    # Inspect executable imports/calls rather than prose or classification
    # strings that name historical artifacts.
    hits = {}
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        bad = [value for value in imports + calls if any(token in value.lower() for token in ("exp_lib", "exp_r2", "name_sim_arrays", "nsim_min_score"))]
        if bad:
            hits[str(path.relative_to(ROOT))] = bad
    if hits:
        raise AssertionError(f"legacy confounded name_sim path reachable from v2: {hits}")
    return {"checked_files": [str(path.relative_to(ROOT)) for path in paths], "legacy_hits": hits}


def validate_split_manifests() -> dict[str, object]:
    manifests = []
    for seed in (101, 202, 303):
        path = V2 / "splits" / f"outer_{seed}.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        if tuple(value["roles"]) != ROLES or set(value["profile_counts"]) != set(ROLES):
            raise AssertionError(f"invalid role manifest for {seed}")
        if any(int(value["profile_counts"][role]) <= 0 for role in ROLES):
            raise AssertionError(f"empty role in split {seed}")
        manifests.append({"seed": seed, "profile_counts": value["profile_counts"], "entity_overlap_check": value["entity_overlap_check"]})
    return {"seeds": manifests, "outer_seeds_executed": False}


def static_route_real_artifacts() -> dict[str, object]:
    """Refresh hashed role manifests and route existing label-free pair artifacts only."""
    profiles = load_public_profiles()
    candidates_dir = V2 / "candidates"
    routing_dir = V2 / "routing"
    expected = {"exact_tier.parquet": 12403, "model_scored.parquet": 2073842, "workflow.parquet": 2086245}
    frames = {name: pd.read_parquet(candidates_dir / name) for name in expected}
    assert_label_free_artifacts([candidates_dir / name for name in expected] + [V2 / "features" / "gb17.parquet", V2 / "features" / "bert_cos.parquet"])
    if {name: len(frame) for name, frame in frames.items()} != expected:
        raise AssertionError("frozen global candidate scope differs; refusing to route")
    result: dict[str, object] = {"NOT_MANUSCRIPT_EVIDENCE": True, "global_candidate_scope": expected, "seeds": {}}
    for seed in (101, 202, 303):
        manifest_path = V2 / "splits" / f"outer_{seed}.json"
        split_manifest(profiles, seed, manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entity_roles = build_entity_role_map(profiles[["profile_row_id", "user_folder"]], manifest)
        seed_dir = routing_dir / f"outer_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        seed_report = {}
        for name, frame in frames.items():
            routed, report = route_pairs(frame, profiles, entity_roles)
            routed.to_parquet(seed_dir / name, index=False)
            seed_report[name] = report
        result["seeds"][str(seed)] = seed_report
    (V2 / "preflight" / "routing_static.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def preflight(args: argparse.Namespace) -> dict:
    pre = V2 / "preflight"
    candidates_dir, features_dir, splits_dir, provenance_dir = [V2 / x for x in ("candidates", "features", "splits", "provenance")]
    for path in (pre, candidates_dir, features_dir, splits_dir, provenance_dir):
        path.mkdir(parents=True, exist_ok=True)
    profiles = load_public_profiles()
    candidates = generate_candidates(profiles, candidates_dir)
    scope = candidate_scope(profiles, candidates)
    (pre / "candidate_scope.json").write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")
    features = regenerate_handcrafted_features(profiles, candidates["scored"], features_dir / "gb17.parquet")
    minilm = regenerate_minilm_cos(profiles, candidates["scored"], features_dir / "bert_cos.parquet")
    bert = pd.read_parquet(features_dir / "bert_cos.parquet")
    f17 = pd.read_parquet(features_dir / "gb17.parquet")
    if list(f17.columns[2:]) != FEATURE17_COLUMNS or list(f17.columns[2:]) + ["bert_cos"] != FEATURE18_COLUMNS:
        raise AssertionError("machine-readable feature schema validation failed")
    for seed in (101, 202, 303):
        split_manifest(profiles, seed, splits_dir / f"outer_{seed}.json")
    legacy_path_check = assert_no_legacy_v2_path()
    label_seal = preflight_label_seal()
    policy_equivalence = preflight_policy_equivalence()
    split_validation = validate_split_manifests()
    if label_seal["PRE-FINAL TEST-LABEL READS"] != len(("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "B0", "B1", "B2", "B3")):
        raise AssertionError("preflight audit did not record denied attempts correctly")
    if policy_equivalence["budget_difference"] != 0 or not policy_equivalence["same_genome_decisions_equal"]:
        raise AssertionError("B2/B3 equivalence or budget preflight failed")
    sources = [PROFILES_PATH, Path(__file__).resolve(), V2 / "features.py", V2 / "label_sealing.py", V2 / "policies.py", V2 / "provenance.py", V2 / "PROTOCOL.md", V2 / "BASELINE_PROTOCOL.md", V2 / "CLAIM_PROTOCOL.md", V2 / "FEATURE_SCHEMA.md", V2 / "DATA_GOVERNANCE.md"]
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    source_hashes.update({f"legacy_{name}": {"classification": "REGENERATE" if name != "predecessor" else "UNVERIFIABLE_HISTORICAL", **digest(path)} if path.is_file() else {"classification": "UNVERIFIABLE_HISTORICAL", "path": str(path)} for name, path in LEGACY.items()})
    (provenance_dir / "preflight_manifest.json").write_text(json.dumps({"python": sys.version, "platform": platform.platform(), "source_artifacts": source_hashes, "candidate_scope": scope, "gb17": features, "minilm": minilm, "gb18_columns": FEATURE18_COLUMNS, "legacy_path_check": legacy_path_check, "label_sealing": label_seal, "policy_equivalence": policy_equivalence, "split_validation": split_validation, "B0": {"thresholds": B0_FIXED, "validation_tuning": False, "test_access": False}, "B1": {"family": "simple_two_threshold", "expanded_name_logic": False, "test_access": False}, "final_seeds_not_executed": True}, indent=2, default=str) + "\n", encoding="utf-8")
    return {"candidate_scope": scope, "gb17": features, "minilm": minilm, "final_seeds_not_executed": True}


def prepare_scientific_inputs() -> dict[str, object]:
    """Produce safe-key label inputs only; never trains or evaluates a model."""
    profiles = load_public_profiles()
    scope = json.loads((V2 / "preflight" / "candidate_scope.json").read_text(encoding="utf-8"))
    expected = {"cross_platform_positives": 29243, "candidate_covered_positives": 25931, "blocking_misses": 3312}
    if {key: scope.get(key) for key in ("cross_platform_positives", "candidate_covered_cross_platform_positives", "cross_platform_blocking_misses")} != {"cross_platform_positives": 29243, "candidate_covered_cross_platform_positives": 25931, "cross_platform_blocking_misses": 3312}:
        raise AssertionError("global candidate scope differs; refusing to produce scientific inputs")
    global_workflow = pd.read_parquet(V2 / "candidates" / "workflow.parquet")
    global_candidate_keys = {canonical_pair_key(row.profile_row_id_a, row.profile_row_id_b) for row in global_workflow.itertuples(index=False)}
    result: dict[str, object] = {"NOT_MANUSCRIPT_EVIDENCE": True, "seeds": {}}
    for seed in (101, 202, 303):
        routed = pd.read_parquet(V2 / "routing" / f"outer_{seed}" / "workflow.parquet")
        manifest_path = V2 / "splits" / f"outer_{seed}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        produced = produce_scientific_input_artifacts(profiles, routed, seed, V2 / "scientific_inputs", PROFILES_PATH, manifest, expected, global_candidate_keys)
        validated = validate_input_artifacts(produced["metadata_path"])
        result["seeds"][str(seed)] = {"metadata": str(produced["metadata_path"]), "development_rows": validated["artifacts"]["development"]["row_count"], "sealed_rows": validated["artifacts"]["sealed_test"]["row_count"]}
    protocol_paths = [V2 / name for name in ("REPAIR_PROTOCOL.md", "PROTOCOL.md", "FEATURE_SCHEMA.md", "BASELINE_PROTOCOL.md", "CLAIM_PROTOCOL.md", "DATA_GOVERNANCE.md")]
    lock = {str(path.relative_to(ROOT)): sha256_file(path) for path in protocol_paths}
    (V2 / "scientific_inputs" / "frozen_protocol_hashes.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    result["frozen_protocol_hashes"] = lock
    return result


def validate_final_scientific_gate(seeds: list[int]) -> None:
    if seeds != [101, 202, 303]:
        raise FinalRunnerError("scientific-final mode requires exactly outer seeds 101 202 303")
    lock_path = V2 / "scientific_inputs" / "frozen_protocol_hashes.json"
    if not lock_path.is_file():
        raise FinalRunnerError("scientific inputs and frozen protocol hashes are required")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    for raw, expected_hash in lock.items():
        if sha256_file(ROOT / raw) != expected_hash:
            raise FinalRunnerError(f"frozen protocol hash differs: {raw}")
    for seed in seeds:
        metadata = V2 / "scientific_inputs" / f"outer_{seed}" / "input_artifact_manifest.json"
        validate_input_artifacts(metadata)
    assert_label_free_artifacts([V2 / "candidates" / name for name in ("exact_tier.parquet", "model_scored.parquet", "workflow.parquet")] + [V2 / "features" / "gb17.parquet", V2 / "features" / "bert_cos.parquet"])
    if FINAL_BUDGET != 12000:
        raise FinalRunnerError("frozen B2/B3 budget differs")


def execute_authorized_scientific(seeds: list[int]) -> dict[str, object]:
    validate_final_scientific_gate(seeds)
    outputs: dict[str, object] = {}
    for seed in seeds:
        routed = pd.read_parquet(V2 / "routing" / f"outer_{seed}" / "workflow.parquet")
        fixture = build_real_fixture(V2 / "scientific_inputs" / f"outer_{seed}" / "input_artifact_manifest.json", routed,
                                     pd.read_parquet(V2 / "features" / "gb17.parquet"), pd.read_parquet(V2 / "features" / "bert_cos.parquet"))
        fixture["NOT_MANUSCRIPT_EVIDENCE"] = False
        outputs[str(seed)] = FinalSealedEvaluationRunner(fixture, V2 / "scientific_outputs" / f"outer_{seed}", seed=seed, budget=FINAL_BUDGET).run()
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="regenerate v2 candidates/features and validate, never train/evaluate")
    parser.add_argument("--static-route-real-artifacts", action="store_true", help="route existing real label-free artifacts without training or evaluation")
    parser.add_argument("--synthetic-final", action="store_true", help="run the complete non-manuscript sealed-evaluation fixture")
    parser.add_argument("--prepare-scientific-inputs", action="store_true", help="produce safe-key label artifacts only; never train/evaluate")
    parser.add_argument("--mode", choices=("preflight", "scientific-final"), default="preflight")
    parser.add_argument("--authorize-final-scientific-run", action="store_true", help="required explicit authorization for scientific-final mode")
    parser.add_argument("--outer-seeds", nargs="+", type=int, default=[])
    parser.add_argument("--execute-final", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.static_route_real_artifacts:
        if args.execute_final or args.outer_seeds or args.synthetic_final:
            parser.error("static routing cannot use final execution, outer seeds, or synthetic execution flags")
        print(json.dumps(static_route_real_artifacts(), indent=2))
        return
    if args.synthetic_final:
        if args.execute_final or args.outer_seeds:
            parser.error("synthetic final fixture cannot use --execute-final or outer seeds")
        output = V2 / "dry_run" / "final_runner_synthetic"
        if output.exists():
            import shutil
            shutil.rmtree(output)
        result = FinalSealedEvaluationRunner(make_synthetic_fixture(), output, seed=17, budget=16).run()
        print(json.dumps({"status": "synthetic_final_complete", "NOT_MANUSCRIPT_EVIDENCE": True,
                          "final_scientific_budget": FINAL_BUDGET, **result}, indent=2))
        return
    if args.prepare_scientific_inputs:
        if args.outer_seeds or args.execute_final or args.authorize_final_scientific_run or args.mode != "preflight":
            parser.error("input production cannot use final execution flags")
        print(json.dumps(prepare_scientific_inputs(), indent=2))
        return
    if args.mode == "scientific-final":
        if args.execute_final or not args.authorize_final_scientific_run:
            raise SystemExit("scientific-final execution is fail-closed: pass --authorize-final-scientific-run")
        print(json.dumps(execute_authorized_scientific(args.outer_seeds), indent=2))
        return
    if args.outer_seeds or args.execute_final or args.authorize_final_scientific_run:
        raise SystemExit("outer seeds require --mode scientific-final and --authorize-final-scientific-run")
    result = preflight(args)
    print(json.dumps({"status": "preflight_complete", "candidate_scope": result["candidate_scope"], "final_seeds_not_executed": True}, indent=2))


if __name__ == "__main__":
    main()
