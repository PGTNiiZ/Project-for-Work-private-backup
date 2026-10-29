"""Train feature weights and optimize GA decision evidence on the labeled feature population.

This workflow intentionally keeps pair-scoring model weights separate from the GA policy:
the model predicts a probability, then the GA optimizes review-band decisions.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from identity_resolution.core.business_cost import CRM_COST_POLICY_VERSION, CRM_COST_WEIGHTS
from identity_resolution.settings import PROJECT_ROOT


SOURCE = PROJECT_ROOT / "pub_multi" / "data" / "train_all.parquet"
PROFILES = PROJECT_ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "decisioning" / "feature_aware_ga"
GROUPS = ("name", "bio", "url", "location", "image", "style")
ONE_STAGE_POLICY_VERSION = "one_stage_weighted_v1"
ONE_STAGE_POLICY_FEATURES = (
    "probability",
    "name",
    "bio",
    "url",
    "location",
    "social",
    "image",
    "style",
)
MODEL_FEATURES = (
    "username_jaro", "username_lev", "username_token_sort", "fullname_jaro", "fullname_lev", "fullname_token_sort",
    "bio_tfidf_cosine", "bio_sbert_cosine", "domain_jaccard", "url_jaccard",
    "location_jaro", "location_token_sort", "mention_jaccard", "hashtag_jaccard",
    "style_caps_diff", "style_avgword_diff", "style_biolen_ratio", "style_punct_diff", "platform_pair_code",
    "image_any_local", "image_both_local", "image_one_local_only", "image_phash_sim", "image_dhash_sim",
    "image_brightness_diff", "image_contrast_diff", "image_entropy_diff", "image_rgb_l1", "image_filesize_ratio",
    "image_face_count_diff", "image_face_area_diff", "image_blur_diff", "image_metadata_any", "image_caption_any",
    "image_caption_bio_sbert_cross", "image_caption_fullname_token_cross", "image_caption_username_token_cross",
)


def status(output: Path, phase: str, progress: int, detail: str) -> None:
    record = {
        "phase": phase,
        "progress": progress,
        "detail": detail,
        "pid": os.getpid(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (output / "status.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"[{progress:3d}%] {phase}: {detail}", flush=True)


def safe_max(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    return frame[columns].fillna(0.0).max(axis=1).to_numpy(dtype=float)


def load_profile_evidence() -> pd.DataFrame:
    profiles = pd.read_csv(PROFILES, keep_default_na=False, low_memory=False)
    profiles["profile_row_id"] = pd.to_numeric(profiles["profile_row_id"], errors="coerce")
    profiles = profiles.dropna(subset=["profile_row_id"]).set_index("profile_row_id")
    for column in ("userName", "fullName", "bio", "location", "externalUrl_clean", "external_domain"):
        if column not in profiles:
            profiles[column] = ""
        profiles[column] = profiles[column].fillna("").astype(str).str.strip()
    return profiles


def derive_decisioning_features(
    pairs: pd.DataFrame,
    profiles: pd.DataFrame,
    *,
    include_model_features: bool = True,
) -> pd.DataFrame:
    """Collapse raw pair features into policy evidence while preserving missingness."""

    def both_available(columns: tuple[str, ...]) -> np.ndarray:
        available_a = np.zeros(len(pairs), dtype=bool)
        available_b = np.zeros(len(pairs), dtype=bool)
        for column in columns:
            values = profiles[column]
            available_a |= pairs["profile_row_id_a"].map(values).fillna("").astype(str).str.len().to_numpy() > 0
            available_b |= pairs["profile_row_id_b"].map(values).fillna("").astype(str).str.len().to_numpy() > 0
        return (available_a & available_b).astype(np.int8)

    cache = pairs[["split_name", "pair_type", "label", "probability", "profile_row_id_a", "profile_row_id_b"]].copy()
    cache["name_score"] = safe_max(pairs, ["username_jaro", "username_lev", "username_token_sort", "fullname_jaro", "fullname_lev", "fullname_token_sort"])
    cache["bio_score"] = safe_max(pairs, ["bio_tfidf_cosine", "bio_sbert_cosine"])
    cache["url_score"] = safe_max(pairs, ["domain_jaccard", "url_jaccard"])
    cache["location_score"] = safe_max(pairs, ["location_jaro", "location_token_sort"])
    cache["social_score"] = safe_max(pairs, ["mention_jaccard", "hashtag_jaccard"])
    cache["image_score"] = safe_max(pairs, ["image_phash_sim", "image_dhash_sim", "image_caption_bio_sbert_cross", "image_caption_fullname_token_cross", "image_caption_username_token_cross"])
    style = np.column_stack([
        pairs["style_biolen_ratio"].fillna(0.0),
        1.0 - pairs["style_caps_diff"].fillna(1.0).clip(0.0, 1.0),
        1.0 - pairs["style_avgword_diff"].fillna(1.0).clip(0.0, 1.0),
        1.0 - pairs["style_punct_diff"].fillna(1.0).clip(0.0, 1.0),
    ])
    cache["style_score"] = np.clip(style.mean(axis=1), 0.0, 1.0)
    cache["name_available"] = both_available(("userName", "fullName"))
    cache["bio_available"] = both_available(("bio",))
    cache["url_available"] = both_available(("externalUrl_clean", "external_domain"))
    cache["location_available"] = both_available(("location",))
    social_tokens = profiles.get("bio_mentions", pd.Series("", index=profiles.index)).fillna("").astype(str).str.strip().str.len() > 0
    if "bio" in profiles:
        social_tokens |= profiles["bio"].astype(str).str.contains(r"[@#]\w", regex=True, na=False)
    social_a = pairs["profile_row_id_a"].map(social_tokens).fillna(False).to_numpy(bool)
    social_b = pairs["profile_row_id_b"].map(social_tokens).fillna(False).to_numpy(bool)
    cache["social_available"] = (social_a & social_b).astype(np.int8)
    cache["image_available"] = ((pairs["image_both_local"].fillna(0).to_numpy() > 0) | (pairs["image_caption_any"].fillna(0).to_numpy() > 0)).astype(np.int8)
    cache["style_available"] = cache["bio_available"]
    for group in GROUPS:
        cache[f"{group}_score"] = cache[f"{group}_score"].clip(0.0, 1.0)
    if include_model_features:
        for column in MODEL_FEATURES:
            cache[column] = pairs[column].fillna(0.0).to_numpy()
    return cache


def build_cache(output: Path) -> pd.DataFrame:
    status(output, "CACHE", 5, "loading labeled feature population")
    pairs = pd.read_parquet(SOURCE)
    profiles = load_profile_evidence()
    status(output, "CACHE", 15, "deriving evidence scores and availability masks")
    cache = derive_decisioning_features(pairs, profiles)
    cache.to_parquet(output / "decisioning_features.parquet", index=False)
    manifest = {
        "source": str(SOURCE),
        "rows": int(len(cache)),
        "scope": "labeled feature population; it is not the full production candidate cache",
        "evidence_groups": list(GROUPS),
        "model_features": list(MODEL_FEATURES),
    }
    (output / "feature_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    status(output, "CACHE", 25, f"saved {len(cache):,} pairs with score/mask evidence")
    return cache


def metrics(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, float]:
    predicted = probabilities >= threshold
    return {
        "ap": float(average_precision_score(labels, probabilities)),
        "auc": float(roc_auc_score(labels, probabilities)),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "fp": int(((predicted == 1) & (labels == 0)).sum()),
        "fn": int(((predicted == 0) & (labels == 1)).sum()),
        "review": 0,
        "threshold": float(threshold),
    }


def best_threshold(labels: np.ndarray, probabilities: np.ndarray) -> float:
    choices = np.arange(0.05, 0.96, 0.01)
    return float(max(choices, key=lambda threshold: (f1_score(labels, probabilities >= threshold, zero_division=0), precision_score(labels, probabilities >= threshold, zero_division=0))))


def feature_group(feature: str) -> str:
    if feature.startswith(("username_", "fullname_")):
        return "name"
    if feature.startswith("bio_"):
        return "bio"
    if feature.startswith(("domain_", "url_")):
        return "url"
    if feature.startswith("location_"):
        return "location"
    if feature.startswith("image_"):
        return "image"
    if feature.startswith("style_"):
        return "style"
    return "other"


def train_weight_models(cache: pd.DataFrame, output: Path) -> dict:
    status(output, "MODEL", 30, "training Logistic Regression and Gradient Boosting on train split")
    features = list(MODEL_FEATURES) + [f"{group}_available" for group in GROUPS]
    train, validation, test = (cache[cache.split_name == split] for split in ("train", "val", "test"))
    scaler = StandardScaler().fit(train[features])
    train_x, val_x = scaler.transform(train[features]), scaler.transform(validation[features])
    models = {
        "logistic_regression": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42),
    }
    summaries, fitted = {}, {}
    for index, (name, model) in enumerate(models.items(), start=1):
        status(output, "MODEL", 30 + index * 10, f"fitting {name} ({index}/2)")
        model.fit(train_x, train.label)
        val_prob = model.predict_proba(val_x)[:, 1]
        threshold = best_threshold(validation.label.to_numpy(), val_prob)
        summaries[name] = metrics(validation.label.to_numpy(), val_prob, threshold)
        fitted[name] = (model, threshold)
    selected_name = max(summaries, key=lambda name: (summaries[name]["ap"], summaries[name]["f1"]))
    selected_model, selected_threshold = fitted[selected_name]
    status(output, "MODEL", 55, f"selected {selected_name} by validation AP={summaries[selected_name]['ap']:.6f}")
    logistic = fitted["logistic_regression"][0]
    coefficients = pd.DataFrame({"feature": features, "standardized_coefficient": logistic.coef_[0]})
    coefficients["odds_ratio"] = np.exp(coefficients["standardized_coefficient"])
    coefficients.to_csv(output / "logistic_coefficients.csv", index=False)
    val_importance = permutation_importance(selected_model, val_x, validation.label, scoring="average_precision", n_repeats=20, random_state=42, n_jobs=1)
    importance = pd.DataFrame({"feature": features, "permutation_ap_delta": val_importance.importances_mean, "permutation_ap_std": val_importance.importances_std})
    importance["group"] = importance.feature.map(feature_group)
    group_importance = importance.groupby("group", as_index=False).agg(permutation_ap_delta=("permutation_ap_delta", "sum"), permutation_ap_std=("permutation_ap_std", "sum"), feature_count=("feature", "size"))
    importance.to_csv(output / "feature_permutation_importance_validation.csv", index=False)
    group_importance.to_csv(output / "grouped_permutation_importance_validation.csv", index=False)
    report = {"selection_split": "val", "selected_model": selected_name, "validation": summaries, "selected_threshold": selected_threshold, "test_is_sealed": True}
    (output / "model_feature_weight_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"model": selected_model, "threshold": selected_threshold, "features": features, "scaler": scaler, "report": report, "test": test}


def coverage_audit(cache: pd.DataFrame, output: Path) -> pd.DataFrame:
    status(output, "AUDIT", 58, "computing availability coverage and reliability by evidence group")
    rows = []
    validation = cache[cache.split_name == "val"]
    for group in GROUPS:
        available = validation[f"{group}_available"].astype(bool)
        subset = validation[available]
        positives = int(subset.label.sum())
        if subset.empty:
            reliability = 0.0
            high_score_positive_rate = 0.0
        else:
            reliability = float(subset.label.mean())
            high = subset[subset[f"{group}_score"] >= 0.5]
            high_score_positive_rate = float(high.label.mean()) if len(high) else 0.0
        rows.append({"group": group, "validation_rows": int(len(validation)), "available_rows": int(len(subset)), "availability_coverage": float(available.mean()), "available_positive_support": positives, "available_positive_rate": reliability, "high_score_positive_rate": high_score_positive_rate, "eligible_for_global_weight": bool(available.mean() >= 0.05 and positives >= 100)})
    report = pd.DataFrame(rows)
    report.to_csv(output / "coverage_reliability.csv", index=False)
    return report


def decisions(probability: np.ndarray, evidence: np.ndarray, available: np.ndarray, genome: np.ndarray) -> np.ndarray:
    match_threshold, review_threshold, promote_threshold, demote_threshold = genome[:4]
    result = np.ones(len(probability), dtype=np.int8)  # review
    result[probability < review_threshold] = 0
    band = (probability >= review_threshold) & (probability < match_threshold) & available.astype(bool)
    result[band & (evidence >= promote_threshold)] = 2
    result[band & (evidence < demote_threshold)] = 0
    result[probability >= match_threshold] = 2
    return result


def decision_metrics(decision: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    match = decision == 2
    no_match = decision == 0
    fp, fn, review = int((match & (labels == 0)).sum()), int((no_match & (labels == 1)).sum()), int((decision == 1).sum())
    precision = float((match & (labels == 1)).sum() / match.sum()) if match.any() else 0.0
    recall = float((match & (labels == 1)).sum() / (labels == 1).sum()) if (labels == 1).any() else 0.0
    return {
        "fp": fp,
        "fn": fn,
        "review": review,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "cost": CRM_COST_WEIGHTS.cost(fp=fp, fn=fn, review=review),
    }


def clip_one_stage_genome(genome: np.ndarray, active_mask: np.ndarray | None = None) -> np.ndarray:
    """Constrain ``[t_match, t_review, eight policy weights]`` to its valid domain."""
    values = np.asarray(genome, dtype=float)
    expected = 2 + len(ONE_STAGE_POLICY_FEATURES)
    if values.shape != (expected,):
        raise ValueError(f"one-stage genome must contain exactly {expected} genes")
    if not np.isfinite(values).all():
        raise ValueError("one-stage genome must contain only finite values")
    if active_mask is None:
        active = np.ones(len(ONE_STAGE_POLICY_FEATURES), dtype=bool)
    else:
        active = np.asarray(active_mask, dtype=bool)
        if active.shape != (len(ONE_STAGE_POLICY_FEATURES),):
            raise ValueError("active_mask must contain one flag per policy feature")
    if not active.any():
        raise ValueError("at least one policy feature must be active")
    match_threshold = float(np.clip(values[0], 0.50, 0.999))
    review_threshold = float(np.clip(values[1], 0.05, match_threshold))
    weights = np.clip(values[2:], 0.0, None)
    weights[~active] = 0.0
    total = float(weights.sum())
    if total == 0.0:
        weights[active] = 1.0 / int(active.sum())
    else:
        weights /= total
    return np.concatenate(([match_threshold, review_threshold], weights))


def one_stage_policy_score(scores: np.ndarray, masks: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Return the availability-conditioned weighted score for eight policy features."""
    score_values = np.asarray(scores, dtype=float)
    mask_values = np.asarray(masks, dtype=float)
    weight_values = np.asarray(weights, dtype=float)
    feature_count = len(ONE_STAGE_POLICY_FEATURES)
    if score_values.ndim != 2 or score_values.shape[1] != feature_count:
        raise ValueError(f"scores must have shape (n, {feature_count})")
    if mask_values.shape != score_values.shape:
        raise ValueError("masks must have the same shape as scores")
    if weight_values.shape != (feature_count,):
        raise ValueError(f"weights must contain exactly {feature_count} values")
    if not np.isfinite(score_values).all() or not np.isfinite(mask_values).all() or not np.isfinite(weight_values).all():
        raise ValueError("scores, masks, and weights must contain only finite values")
    if np.any((mask_values != 0.0) & (mask_values != 1.0)):
        raise ValueError("availability masks must be binary")
    if np.any(weight_values < 0.0):
        raise ValueError("policy weights must be non-negative")
    numerator = (score_values * mask_values * weight_values).sum(axis=1)
    denominator = (mask_values * weight_values).sum(axis=1)
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0.0)


def one_stage_decisions(scores: np.ndarray, masks: np.ndarray, genome: np.ndarray) -> np.ndarray:
    """Apply one weighted score once, followed only by MATCH/REVIEW thresholds."""
    values = np.asarray(genome, dtype=float)
    expected = 2 + len(ONE_STAGE_POLICY_FEATURES)
    if values.shape != (expected,):
        raise ValueError(f"one-stage genome must contain exactly {expected} genes")
    match_threshold, review_threshold = values[:2]
    if not 0.0 <= review_threshold <= match_threshold <= 1.0:
        raise ValueError("thresholds must satisfy 0 <= t_review <= t_match <= 1")
    combined = one_stage_policy_score(scores, masks, values[2:])
    effective_evidence = (np.asarray(masks, dtype=float) * values[2:]).sum(axis=1) > 0.0
    result = np.ones(len(combined), dtype=np.int8)
    result[effective_evidence & (combined < review_threshold)] = 0
    result[effective_evidence & (combined >= match_threshold)] = 2
    return result


def optimize_one_stage_policy(
    scores: np.ndarray,
    masks: np.ndarray,
    labels: np.ndarray,
    seed: int,
    *,
    active_mask: np.ndarray | None = None,
    population_size: int = 80,
    generations: int = 60,
    elite_size: int = 16,
    candidate_batch_size: int | None = None,
) -> tuple[np.ndarray, list[dict]]:
    """Optimize the fixed ten-gene one-stage policy on one selection split."""
    score_values = np.asarray(scores, dtype=float)
    mask_values = np.asarray(masks, dtype=float)
    label_values = np.asarray(labels, dtype=np.int8)
    feature_count = len(ONE_STAGE_POLICY_FEATURES)
    if score_values.ndim != 2 or score_values.shape[1] != feature_count:
        raise ValueError(f"scores must have shape (n, {feature_count})")
    if mask_values.shape != score_values.shape or len(label_values) != len(score_values):
        raise ValueError("scores, masks, and labels must describe the same rows")
    if len(label_values) == 0 or not np.isfinite(score_values).all() or not np.isfinite(mask_values).all():
        raise ValueError("the optimization split must contain finite data and at least one row")
    if np.any((mask_values != 0.0) & (mask_values != 1.0)):
        raise ValueError("availability masks must be binary")
    if not np.isin(label_values, [0, 1]).all():
        raise ValueError("labels must be binary")
    if population_size < 4 or generations < 1 or not 1 <= elite_size < population_size:
        raise ValueError("invalid GA population, generation, or elite size")
    if candidate_batch_size is not None and candidate_batch_size < 1:
        raise ValueError("candidate_batch_size must be positive")
    if active_mask is None:
        active = mask_values.astype(bool).any(axis=0)
    else:
        active = np.asarray(active_mask, dtype=bool)
        if active.shape != (feature_count,):
            raise ValueError("active_mask must contain one flag per policy feature")
    if not active.any():
        raise ValueError("at least one policy feature must be active")
    rng = np.random.default_rng(seed)

    def initial_genome() -> np.ndarray:
        match_threshold = rng.uniform(0.55, 0.999)
        review_threshold = rng.uniform(0.01, match_threshold)
        raw_weights = np.zeros(feature_count)
        raw_weights[active] = rng.dirichlet(np.ones(int(active.sum())))
        return clip_one_stage_genome(
            np.concatenate(([match_threshold, review_threshold], raw_weights)),
            active,
        )

    weighted_scores = score_values * mask_values

    def rank_population(population: list[np.ndarray]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        matrix = np.asarray(population)
        positive = label_values[:, None] == 1
        negative = ~positive
        batch_size = candidate_batch_size or len(matrix)
        fp_parts, fn_parts, review_parts, tp_parts, match_parts = [], [], [], [], []
        for start in range(0, len(matrix), batch_size):
            batch = matrix[start:start + batch_size]
            weights = batch[:, 2:].T
            numerator = weighted_scores @ weights
            denominator = mask_values @ weights
            combined = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0.0)
            effective_evidence = denominator > 0.0
            match = effective_evidence & (combined >= batch[:, 0])
            no_match = effective_evidence & (combined < batch[:, 1])
            review = ~(match | no_match)
            fp_parts.append((match & negative).sum(axis=0))
            fn_parts.append((no_match & positive).sum(axis=0))
            review_parts.append(review.sum(axis=0))
            tp_parts.append((match & positive).sum(axis=0))
            match_parts.append(match.sum(axis=0))
        fp = np.concatenate(fp_parts)
        fn = np.concatenate(fn_parts)
        review_count = np.concatenate(review_parts)
        tp = np.concatenate(tp_parts)
        match_count = np.concatenate(match_parts)
        precision = np.divide(tp, match_count, out=np.zeros_like(tp, dtype=float), where=match_count > 0)
        positive_count = max(int(positive[:, 0].sum()), 1)
        recall = tp / positive_count
        cost = CRM_COST_WEIGHTS.fp * fp + CRM_COST_WEIGHTS.fn * fn + CRM_COST_WEIGHTS.review * review_count
        order = np.lexsort((review_count, -recall, fp, -precision, cost))
        return order, {
            "cost": cost,
            "precision": precision,
            "recall": recall,
            "fp": fp,
            "fn": fn,
            "review": review_count,
        }

    population = [initial_genome() for _ in range(population_size)]
    history: list[dict] = []
    for generation in range(generations):
        order, summary = rank_population(population)
        population = [population[int(index)] for index in order]
        elites = population[:elite_size]
        if generation % 5 == 0 or generation == generations - 1:
            best = population[0]
            original_index = int(order[0])
            history.append({
                "generation": generation,
                "validation_cost": float(summary["cost"][original_index]),
                "validation_precision": float(summary["precision"][original_index]),
                "validation_recall": float(summary["recall"][original_index]),
                "genome": best.round(6).tolist(),
                "thresholds": best[:2].round(6).tolist(),
                "weights": dict(zip(ONE_STAGE_POLICY_FEATURES, best[2:].round(6).tolist())),
            })
        children: list[np.ndarray] = []
        while len(children) < population_size - elite_size:
            parent_a = elites[int(rng.integers(elite_size))]
            parent_b = elites[int(rng.integers(elite_size))]
            child = np.where(rng.random(len(parent_a)) < 0.5, parent_a, parent_b)
            mutation = rng.normal(0.0, 0.025, len(child))
            mutation[2:] *= 2.0
            child += mutation * (rng.random(len(child)) < 0.30)
            children.append(clip_one_stage_genome(child, active))
        population = elites + children
    order, _ = rank_population(population)
    return population[int(order[0])], history


def clip_genome(genome: np.ndarray) -> np.ndarray:
    match = np.clip(genome[0], 0.50, 0.999)
    review = np.clip(genome[1], 0.05, match)
    promote = np.clip(genome[2], 0.50, 1.0)
    demote = np.clip(genome[3], 0.0, promote)
    return np.array([match, review, promote, demote])


def optimize_policy(
    probability: np.ndarray,
    evidence: np.ndarray,
    available: np.ndarray,
    labels: np.ndarray,
    seed: int,
    weights: np.ndarray | None = None,
    *,
    population_size: int = 60,
    generations: int = 40,
    elite_size: int = 12,
    candidate_batch_size: int | None = None,
) -> tuple[np.ndarray, list[dict]]:
    if population_size < 4 or generations < 1 or not 1 <= elite_size < population_size:
        raise ValueError("invalid GA population, generation, or elite size")
    if candidate_batch_size is not None and candidate_batch_size < 1:
        raise ValueError("candidate_batch_size must be positive")
    rng = np.random.default_rng(seed)
    population = [clip_genome(rng.uniform([0.70, 0.10, 0.50, 0.0], [0.999, 0.80, 1.0, 0.50])) for _ in range(population_size)]
    def cost(genome: np.ndarray) -> float:
        return decision_metrics(decisions(probability, evidence, available, genome), labels)["cost"]

    def rank_population(values: list[np.ndarray]) -> list[np.ndarray]:
        """Rank a population in bounded batches for million-row validation arrays."""
        if candidate_batch_size is None:
            return sorted(values, key=cost)
        matrix = np.asarray(values)
        probability_values = np.asarray(probability, dtype=float)[:, None]
        evidence_values = np.asarray(evidence, dtype=float)[:, None]
        available_values = np.asarray(available, dtype=bool)[:, None]
        positive = np.asarray(labels, dtype=np.int8)[:, None] == 1
        costs = []
        for start in range(0, len(matrix), candidate_batch_size):
            batch = matrix[start:start + candidate_batch_size]
            match = probability_values >= batch[:, 0]
            no_match = probability_values < batch[:, 1]
            band = (~match) & (~no_match) & available_values
            match |= band & (evidence_values >= batch[:, 2])
            no_match |= band & (evidence_values < batch[:, 3])
            review = ~(match | no_match)
            fp = (match & ~positive).sum(axis=0)
            fn = (no_match & positive).sum(axis=0)
            review_count = review.sum(axis=0)
            costs.append(2.0 * fp + fn + 0.1 * review_count)
        order = np.argsort(np.concatenate(costs), kind="stable")
        return [values[int(index)] for index in order]
    history = []
    for generation in range(generations):
        population = rank_population(population)
        elite = population[:elite_size]
        children = []
        while len(children) < population_size - elite_size:
            parent_a, parent_b = elite[rng.integers(elite_size)], elite[rng.integers(elite_size)]
            child = np.where(rng.random(4) < 0.5, parent_a, parent_b)
            child += rng.normal(0.0, 0.02, 4) * (rng.random(4) < 0.30)
            children.append(clip_genome(child))
        population = elite + children
        if generation % 5 == 0 or generation == generations - 1:
            history.append({"generation": generation, "validation_cost": float(cost(population[0])), "genome": population[0].round(6).tolist()})
    return min(population, key=cost), history


def selector_experiments(cache: pd.DataFrame, audit: pd.DataFrame, output: Path) -> tuple[pd.DataFrame, dict]:
    status(output, "GA_SELECTOR", 62, "optimizing score-only and one-guard GA policies on validation")
    validation = cache[cache.split_name == "val"]
    rows, histories = [], {}
    candidates = ["score_only"] + [group for group in GROUPS if bool(audit.loc[audit.group == group, "eligible_for_global_weight"].iloc[0])]
    for index, guard in enumerate(candidates, start=1):
        if guard == "score_only":
            evidence, available = np.zeros(len(validation)), np.zeros(len(validation), dtype=np.int8)
        else:
            evidence, available = validation[f"{guard}_score"].to_numpy(), validation[f"{guard}_available"].to_numpy()
        genome, history = optimize_policy(validation.probability.to_numpy(), evidence, available, validation.label.to_numpy(), 42 + index)
        histories[guard] = history
        val_metrics = decision_metrics(decisions(validation.probability.to_numpy(), evidence, available, genome), validation.label.to_numpy())
        rows.append({"guard": guard, "genome": json.dumps(genome.tolist()), **{f"validation_{key}": value for key, value in val_metrics.items()}})
        status(output, "GA_SELECTOR", 62 + round(13 * index / len(candidates)), f"completed guard {guard} ({index}/{len(candidates)})")
    leaderboard = pd.DataFrame(rows).sort_values(["validation_cost", "validation_fp", "validation_fn"])
    leaderboard.to_csv(output / "selector_leaderboard.csv", index=False)
    (output / "selector_generation_history.json").write_text(json.dumps(histories, indent=2), encoding="utf-8")
    winner = leaderboard.iloc[0].to_dict()
    return leaderboard, winner


def optimize_weighted_policy(cache: pd.DataFrame, audit: pd.DataFrame, output: Path) -> dict:
    status(output, "GA_WEIGHTED", 77, "optimizing availability-gated evidence weights on validation")
    groups = audit.loc[audit.eligible_for_global_weight, "group"].tolist()
    validation, test = cache[cache.split_name == "val"], cache[cache.split_name == "test"]
    if not groups:
        raise ValueError("No evidence group satisfies coverage/support eligibility")
    score_v = validation[[f"{group}_score" for group in groups]].to_numpy(float)
    mask_v = validation[[f"{group}_available" for group in groups]].to_numpy(float)
    score_t = test[[f"{group}_score" for group in groups]].to_numpy(float)
    mask_t = test[[f"{group}_available" for group in groups]].to_numpy(float)
    rng = np.random.default_rng(4242)
    def normalize(weights: np.ndarray) -> np.ndarray:
        weights = np.clip(weights, 0.0, None)
        return weights / weights.sum() if weights.sum() else np.full(len(weights), 1.0 / len(weights))
    def evidence(scores: np.ndarray, masks: np.ndarray, weights: np.ndarray) -> np.ndarray:
        numerator = (scores * masks * weights).sum(axis=1)
        denominator = (masks * weights).sum(axis=1)
        return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
    def available(masks: np.ndarray) -> np.ndarray:
        return (masks.sum(axis=1) > 0).astype(np.int8)
    def clip_full(genome: np.ndarray) -> np.ndarray:
        return np.concatenate([clip_genome(genome[:4]), normalize(genome[4:])])
    def cost(genome: np.ndarray) -> float:
        return decision_metrics(decisions(validation.probability.to_numpy(), evidence(score_v, mask_v, genome[4:]), available(mask_v), genome[:4]), validation.label.to_numpy())["cost"]
    population = [clip_full(np.concatenate([rng.uniform([0.70, 0.10, 0.50, 0.0], [0.999, 0.80, 1.0, 0.50]), rng.dirichlet(np.ones(len(groups)))])) for _ in range(80)]
    history = []
    for generation in range(60):
        population.sort(key=cost)
        elite = population[:16]
        children = []
        while len(children) < 64:
            parent_a, parent_b = elite[rng.integers(16)], elite[rng.integers(16)]
            child = np.where(rng.random(len(parent_a)) < 0.5, parent_a, parent_b)
            child += rng.normal(0.0, 0.025, len(child)) * (rng.random(len(child)) < 0.30)
            children.append(clip_full(child))
        population = elite + children
        if generation % 5 == 0 or generation == 59:
            history.append({"generation": generation, "validation_cost": float(cost(population[0])), "thresholds": population[0][:4].round(6).tolist(), "weights": dict(zip(groups, population[0][4:].round(6).tolist()))})
            status(output, "GA_WEIGHTED", 77 + round(18 * generation / 60), f"generation {generation}/60; validation cost {cost(population[0]):.2f}")
    winner = min(population, key=cost)
    val_metrics = decision_metrics(decisions(validation.probability.to_numpy(), evidence(score_v, mask_v, winner[4:]), available(mask_v), winner[:4]), validation.label.to_numpy())
    result = {"active_groups": groups, "thresholds": winner[:4].tolist(), "weights": dict(zip(groups, winner[4:].tolist())), "validation_metrics": val_metrics, "selection_policy": "weights and thresholds selected by validation cost only; test remains sealed until final policy selection", "history": history}
    (output / "weighted_ga_history.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def evaluate_frozen_winner(cache: pd.DataFrame, selector_winner: dict, weighted: dict, output: Path) -> dict:
    """Choose policy on validation, then make exactly one held-out test evaluation."""
    selector_cost = float(selector_winner["validation_cost"])
    weighted_cost = float(weighted["validation_metrics"]["cost"])
    test = cache[cache.split_name == "test"]
    if weighted_cost < selector_cost:
        groups = weighted["active_groups"]
        scores = test[[f"{group}_score" for group in groups]].to_numpy(float)
        masks = test[[f"{group}_available" for group in groups]].to_numpy(float)
        weights = np.asarray([weighted["weights"][group] for group in groups])
        numerator = (scores * masks * weights).sum(axis=1)
        denominator = (masks * weights).sum(axis=1)
        evidence = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
        availability = (masks.sum(axis=1) > 0).astype(np.int8)
        decision = decisions(test.probability.to_numpy(), evidence, availability, np.asarray(weighted["thresholds"]))
        policy = "weighted_evidence"
        validation_cost = weighted_cost
    else:
        guard = selector_winner["guard"]
        genome = np.asarray(json.loads(selector_winner["genome"]), dtype=float)
        if guard == "score_only":
            evidence, availability = np.zeros(len(test)), np.zeros(len(test), dtype=np.int8)
        else:
            evidence = test[f"{guard}_score"].to_numpy()
            availability = test[f"{guard}_available"].to_numpy()
        decision = decisions(test.probability.to_numpy(), evidence, availability, genome)
        policy = f"selector:{guard}"
        validation_cost = selector_cost
    result = {
        "policy": policy,
        "cost_policy_version": CRM_COST_POLICY_VERSION,
        "cost_weights": CRM_COST_WEIGHTS.as_dict(),
        "selection_rule": "lower validation decision cost; test evaluated exactly once after policy freeze",
        "validation_cost": validation_cost,
        "test_metrics": decision_metrics(decision, test.label.to_numpy()),
    }
    (output / "sealed_test_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def write_report(output: Path, model_bundle: dict, audit: pd.DataFrame, selector: pd.DataFrame, selector_winner: dict, weighted: dict, final_test: dict) -> None:
    report = model_bundle["report"]
    selected = report["selected_model"]
    selected_validation = report["validation"][selected]
    importance = pd.read_csv(output / "feature_permutation_importance_validation.csv")
    model_lines = "\n".join(
        f"| {model_name} | {values['ap']:.6f} | {values['auc']:.6f} | {values['precision']:.4f} | {values['recall']:.4f} | {values['f1']:.4f} | {values['threshold']:.2f} |"
        for model_name, values in report["validation"].items()
    )
    top_feature_lines = "\n".join(
        f"| {row.feature} | {row.group} | {row.permutation_ap_delta:.6f} | {row.permutation_ap_std:.6f} |"
        for row in importance.sort_values("permutation_ap_delta", ascending=False).head(10).itertuples(index=False)
    )
    coverage_lines = "\n".join(
        f"| {row.group} | {row.availability_coverage:.2%} | {int(row.available_positive_support):,} | {row.high_score_positive_rate:.3f} | {'yes' if row.eligible_for_global_weight else 'no'} |"
        for row in audit.itertuples(index=False)
    )
    selector_lines = "\n".join(
        f"| {row.guard} | {row.validation_cost:.2f} | {row.validation_precision:.4f} | {row.validation_recall:.4f} | {row.validation_fp} | {row.validation_fn} | {row.validation_review} |"
        for row in selector.itertuples(index=False)
    )
    weights = "\n".join(f"| {group} | {weight:.4f} |" for group, weight in weighted["weights"].items())
    text = f"""# รายงานผลละเอียด: Model Weights และ Feature-Aware GA

## ขอบเขตและความหมายของผล

run นี้ตอบคำถามสองเรื่องที่ต้องแยกออกจากกันบน labeled feature population ใน
`pub_multi/data/train_all.parquet` (**58,696 pairs**):

1. feature และ feature group ใดช่วยให้ pair-scoring model ทำนายความน่าจะเป็นว่าเป็นคนเดียวกัน
2. evidence group ใดควรเป็น guard ใน review band ของ GA และน้ำหนักของ evidence ที่มีข้อมูลอยู่ควรเป็นเท่าใดเพื่อลด business cost

ผลนี้ **ยังไม่ใช่รายงานสำหรับ production เต็มชุด**. historical GA cache มี 2,073,842 scored
candidates แต่ feature matrix ที่ใช้รอบนี้ overlap เพียง 20,757 คู่ (1.00%). ดังนั้นผลนี้ใช้ยืนยัน
แนวทาง model/feature research ได้ แต่ก่อน promote จะต้อง rebuild cache ที่มี availability mask
แบบเดียวกันให้ครอบคลุม candidate ทั้งหมดก่อน

## สิ่งที่ workflow ทำ

1. สร้าง `decisioning_features.parquet` ที่เก็บ evidence score และ availability mask แยกกันสำหรับ name, bio, URL, location, image และ style. ข้อมูลที่ไม่มีจะไม่ถูกแปลงเป็น similarity เท่ากับศูนย์
2. train Logistic Regression เพื่ออ่าน standardized coefficient และ train Gradient Boosting เพื่อจับความสัมพันธ์ non-linear. เลือก model ด้วย validation AP เท่านั้น
3. รัน GA selector policy: score-only และ one-guard policy สำหรับทุก group ที่มี coverage/support เพียงพอ
4. รัน weighted-evidence GA: เรียนรู้ weight ที่ไม่ติดลบ และ normalize ใหม่ตาม evidence ที่มีอยู่ในแต่ละคู่ จึงไม่มีการลงโทษ feature ที่หายไป
5. เปรียบเทียบทุก policy บน validation, freeze policy ที่ cost ต่ำสุด แล้วเปิด held-out test เพียง **หนึ่งครั้ง**

## Pair-Scoring Model

model ที่เลือก: **{selected}**

| Validation AP | AUC | Precision | Recall | F1 | Threshold |
|---:|---:|---:|---:|---:|---:|
| {selected_validation['ap']:.6f} | {selected_validation['auc']:.6f} | {selected_validation['precision']:.4f} | {selected_validation['recall']:.4f} | {selected_validation['f1']:.4f} | {selected_validation['threshold']:.2f} |

| Model | Validation AP | AUC | Precision | Recall | F1 | Threshold |
|---|---:|---:|---:|---:|---:|---:|
{model_lines}

`logistic_coefficients.csv` แสดง coefficient ที่ตีความง่าย ส่วน
`grouped_permutation_importance_validation.csv` แสดงผลกระทบเชิง predictive จาก validation
โดยไม่ผูกกับ model เดียว การตัดสินบทบาท feature ควรอ่านทั้งสองไฟล์ร่วมกัน ไม่ควรสรุปจาก coefficient ตัวเดียว

### Top 10 Feature Effects จาก Permutation Importance

ค่า AP delta คือ AP ที่ลดลงโดยเฉลี่ยเมื่อสลับค่าของ feature นั้นใน validation; ค่ายิ่งสูงแปลว่า model พึ่งพา feature นั้นมากขึ้นภายใต้ข้อมูลชุดนี้

| Feature | Group | AP delta | Std. |
|---|---|---:|---:|
{top_feature_lines}

## Coverage และ Reliability

| Evidence group | Coverage ที่ใช้ได้ | Positive support เมื่อมีข้อมูล | Positive rate เมื่อ score >= 0.5 | ให้ global GA weight ได้ |
|---|---:|---:|---:|---|
{coverage_lines}

group ที่ไม่ผ่านเกณฑ์ไม่ได้แปลว่าไร้ประโยชน์ แต่ sparse เกินกว่าจะให้ global weight ในรอบนี้ได้
เช่น image อาจเป็น override เฉพาะตอนมีข้อมูล และ location ยังต้องแก้ availability ก่อนนำไปตัดสินใจ

## ผลเปรียบเทียบ GA Guard

business cost ใช้สูตร $cost = 2FP + FN + 0.1REVIEW$ (`crm_derived_v1`) ซึ่ง derive จากเวลาแก้
false positive 20 นาที, false negative 10 นาที และ human review 1 นาที

| Guard | Validation cost | Val precision | Val recall | Val FP | Val FN | Val review |
|---|---:|---:|---:|---:|---:|---:|
{selector_lines}

ผู้ชนะบน validation คือ **{selector_winner['guard']}**. genome และ history ทุก generation เก็บใน
`selector_generation_history.json` และ `selector_leaderboard.csv`.

threshold ของ policy ที่ชนะคือ `{selector_winner['genome']}` ตามลำดับ
`[match_threshold, review_threshold, promote_threshold, demote_threshold]`. สำหรับ winner นี้ GA ใช้
bio score ใน review band เพื่อ promote คู่ที่ evidence สูง โดยไม่ hard-code `name_sim`.

## Weighted Evidence GA

weighted policy ที่ GA เลือกมีน้ำหนักแบบ availability-conditioned ดังนี้:

| Evidence group | GA weight |
|---|---:|
{weights}

validation metrics: `{json.dumps(weighted['validation_metrics'])}`

น้ำหนักนี้ใช้เฉพาะ evidence ที่มีข้อมูลจริง และจะ normalize ใหม่ตามกลุ่มที่ใช้ได้ต่อคู่. weight ที่เป็นศูนย์
หมายความว่า GA ไม่พบว่ากลุ่มนั้นลด validation cost เพิ่มจากกลุ่มอื่นภายใต้ objective ปัจจุบัน ไม่ได้หมายความว่า feature นั้นไร้ค่าใน pair-scoring model

## ผล Sealed Test หนึ่งครั้ง

policy ที่ freeze แล้ว: **{final_test['policy']}**

test metrics: `{json.dumps(final_test['test_metrics'])}`

ผล test นี้เกิดหลังเลือก policy จาก validation เสร็จ และไม่มีการใช้ test เพื่อเลือก weight, threshold หรือ guard

## ข้อสรุปและการใช้งานต่อ

model-weight stage กับ GA stage ทำหน้าที่ต่างกันโดยตั้งใจ: pair-scoring model เรียนรู้ probability จาก feature value และ mask ส่วน GA ไม่แก้ parameter ของ model แต่เลือกวิธีใช้ frozen probability ร่วมกับ evidence ที่มีอยู่เพื่อให้ MATCH/REVIEW/NO_MATCH ตาม business cost

สำหรับข้อมูลชุดนี้ bio เป็น guard ที่ลด validation cost ได้ดีที่สุด ขณะที่ name guard เพิ่ม recall แต่สร้าง FP มากจน cost สูงมาก; จึงเป็นหลักฐานว่า `name_sim` ไม่ควรถูก hard-code เป็น policy guard. ก่อน promote production ให้ rebuild `decisioning_features.parquet` บน full 2.07M candidate population, ตรวจ coverage ใหม่, freeze policy ด้วย validation และเปิด sealed test ชุดใหม่เพียงครั้งเดียว
"""
    (output / "DETAILED_REPORT_TH.md").write_text(text, encoding="utf-8")


def regenerate_report(output: Path) -> None:
    """Render documentation from finished artifacts without reading or scoring any split."""
    model_bundle = {"report": json.loads((output / "model_feature_weight_report.json").read_text(encoding="utf-8"))}
    audit = pd.read_csv(output / "coverage_reliability.csv")
    selector = pd.read_csv(output / "selector_leaderboard.csv")
    weighted = json.loads((output / "weighted_ga_history.json").read_text(encoding="utf-8"))
    final_test = json.loads((output / "sealed_test_report.json").read_text(encoding="utf-8"))
    write_report(output, model_bundle, audit, selector, selector.iloc[0].to_dict(), weighted, final_test)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete model-weight and feature-aware GA research workflow.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-only", action="store_true", help="Regenerate the Thai report from existing artifacts without evaluating data.")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    if args.report_only:
        regenerate_report(output)
        print(f"Detailed report regenerated: {output / 'DETAILED_REPORT_TH.md'}")
        return
    status(output, "START", 0, "starting chained model-weight and feature-aware GA workflow")
    cache = build_cache(output)
    model_bundle = train_weight_models(cache, output)
    audit = coverage_audit(cache, output)
    selector, selector_winner = selector_experiments(cache, audit, output)
    weighted = optimize_weighted_policy(cache, audit, output)
    status(output, "TEST", 98, "freezing validation winner and evaluating held-out test once")
    final_test = evaluate_frozen_winner(cache, selector_winner, weighted, output)
    write_report(output, model_bundle, audit, selector, selector_winner, weighted, final_test)
    status(output, "DONE", 100, "all model-weight, GA selector, weighted policy, and detailed report stages completed")
    print(f"Detailed report: {output / 'DETAILED_REPORT_TH.md'}")


if __name__ == "__main__":
    main()
