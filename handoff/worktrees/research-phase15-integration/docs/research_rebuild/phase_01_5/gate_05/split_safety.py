"""Synthetic-only reference split/routing contract; never loads project data."""
from __future__ import annotations
import random

SEED = 20261010
FOLDS = 5
ROLES = ("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "TEST")


def assign_folds(profiles, seed=SEED):
    """Map entity IDs to folds; stratify by sorted unique-platform signature.

    Input is iterable of (entity_id, platform). Entity-level grouping prevents
    profiles of one entity crossing folds. Per-stratum shuffled round-robin
    gives deterministic approximate balance, not exact global platform balance.
    """
    signatures = {}
    for entity, platform in profiles:
        if not str(entity).strip() or not str(platform).strip():
            raise ValueError("entity/platform missing")
        signatures.setdefault(str(entity), set()).add(str(platform))
    strata = {}
    for entity, platforms in signatures.items():
        strata.setdefault(tuple(sorted(platforms)), []).append(entity)
    result = {}
    for signature in sorted(strata):
        entities = sorted(strata[signature])
        random.Random(f"{seed}:{signature}").shuffle(entities)
        for i, entity in enumerate(entities):
            result[entity] = i % FOLDS
    return result


def roles_for_fold(fold_map, heldout_fold):
    """Assign exact rotating outer roles for the five-fold protocol.

    TEST=i, CALIBRATION=(i+1)%5, POLICY_VALIDATION=(i+2)%5, and the two
    remaining folds are TRAIN. Every entity is assigned by its fold; there is
    no within-role entity hash split.
    """
    if heldout_fold not in range(FOLDS):
        raise ValueError("invalid held-out fold")
    calibration_fold = (heldout_fold + 1) % FOLDS
    validation_fold = (heldout_fold + 2) % FOLDS
    role_for_fold = {
        heldout_fold: "TEST",
        calibration_fold: "CALIBRATION",
        validation_fold: "POLICY_VALIDATION",
    }
    return {
        entity: role_for_fold.get(fold, "TRAIN")
        for entity, fold in fold_map.items()
    }


def route_pairs(pairs, profile_entities, entity_roles):
    """Keep only pairs whose two profile endpoints' entities share a role."""
    kept, dropped = [], 0
    for pair in pairs:
        a, b = pair
        if a not in profile_entities or b not in profile_entities:
            raise ValueError("unknown endpoint")
        ra = entity_roles[profile_entities[a]]
        rb = entity_roles[profile_entities[b]]
        if ra != rb:
            dropped += 1
        else:
            kept.append((a, b, ra))
    return kept, {"input_pairs": len(pairs), "same_role_pairs": len(kept), "cross_role_dropped": dropped}
