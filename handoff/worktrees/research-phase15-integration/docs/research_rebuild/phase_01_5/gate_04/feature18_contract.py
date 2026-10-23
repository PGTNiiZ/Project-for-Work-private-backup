"""Fail-closed, versioned Feature18 contract; never downloads model weights."""
from __future__ import annotations

import json
import re
import unicodedata
from numbers import Integral
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

CONTRACT = json.loads(Path(__file__).with_name("FEATURE18_CONTRACT_V1.json").read_text(encoding="utf-8"))
MODEL_IDENTIFIER = CONTRACT["model"]["identifier"]
MODEL_REVISION = CONTRACT["model"]["revision"]
MODEL_WEIGHT_SHA256 = CONTRACT["model"]["weights_sha256"]
TOKENIZER_BUNDLE_SHA256 = CONTRACT["model"]["tokenizer_bundle_sha256"]
EMBEDDING_DIMENSION = CONTRACT["model"]["embedding_dimension"]
TEXT_COMPOSITION = CONTRACT["text_composition"]
POOLING_CONTRACT = CONTRACT["model"]["pooling"]
CONTRACT_VERSION = CONTRACT["contract_version"]
FEATURE17_COLUMNS = json.loads(Path(__file__).with_name("FEATURE_REGISTRY.json").read_text(encoding="utf-8"))["ordered_columns"]
FEATURE18_COLUMN = "bert_cos"


class Feature18ContractError(ValueError):
    """Feature18 inputs lack verified lineage or violate the pair contract."""


def compose_profile_text(full_name: Any, bio: Any, location: Any) -> str:
    """Compose the versioned future-study MiniLM input deterministically."""
    fields = []
    for value in (full_name, bio, location):
        if value is None or (not isinstance(value, str) and bool(pd.isna(value))):
            text = ""
        else:
            text = " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())
        if text:
            fields.append(text)
    return " ".join(fields) if fields else "[empty]"


def _profile_id_sequence(values: Sequence[Any]) -> list[int]:
    parsed = []
    for value in values:
        if isinstance(value, Integral) and not isinstance(value, bool):
            identifier = int(value)
        elif isinstance(value, str) and value.isdigit() and (value == "0" or not value.startswith("0")):
            identifier = int(value)
        else:
            raise Feature18ContractError("profile IDs must be integer row identifiers")
        if identifier < 0:
            raise Feature18ContractError("profile IDs must be non-negative integer row identifiers")
        parsed.append(identifier)
    return parsed


def _require_digest(value: Any, name: str, length: int) -> str:
    if not isinstance(value, str) or re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None:
        raise Feature18ContractError(f"{name} must be lowercase {length}-character SHA-256/commit hex")
    return value


def _validate_metadata(metadata: Mapping[str, Any]) -> None:
    if metadata.get("model_identifier") != MODEL_IDENTIFIER:
        raise Feature18ContractError(f"model_identifier must be exactly {MODEL_IDENTIFIER}")
    revision = metadata.get("model_revision")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40,64}", revision) is None:
        raise Feature18ContractError("model_revision must be a pinned 40- or 64-character commit hash")
    _require_digest(metadata.get("model_weight_sha256"), "model_weight_sha256", 64)
    _require_digest(metadata.get("tokenizer_bundle_sha256"), "tokenizer_bundle_sha256", 64)
    if revision != MODEL_REVISION:
        raise Feature18ContractError("model_revision differs from the pinned Feature18 contract")
    if metadata["model_weight_sha256"] != MODEL_WEIGHT_SHA256:
        raise Feature18ContractError("model weight hash differs from the pinned Feature18 contract")
    if metadata["tokenizer_bundle_sha256"] != TOKENIZER_BUNDLE_SHA256:
        raise Feature18ContractError("tokenizer bundle hash differs from the pinned Feature18 contract")
    if metadata.get("text_composition") != TEXT_COMPOSITION:
        raise Feature18ContractError("text_composition differs from the versioned Feature18 contract")
    if metadata.get("pooling") != POOLING_CONTRACT:
        raise Feature18ContractError("pooling identity is missing or differs from the contract")


def build_feature18(
    feature17: pd.DataFrame,
    embedding_profile_ids: Sequence[int],
    embeddings: np.ndarray,
    *,
    expected_profile_ids: Sequence[int],
    metadata: Mapping[str, Any],
) -> pd.DataFrame:
    """Append normalized-embedding cosine after exact profile-ID alignment.

    This function consumes existing embeddings only. It does not instantiate a
    model, fetch weights, build text, or infer endpoint identities from row order.
    """
    _validate_metadata(metadata)
    required_pair_columns = {"profile_row_id_a", "profile_row_id_b"}
    if not required_pair_columns.issubset(feature17.columns):
        raise Feature18ContractError("Feature17 rows require explicit endpoint IDs")
    expected_columns = ["profile_row_id_a", "profile_row_id_b", *FEATURE17_COLUMNS]
    if list(feature17.columns) != expected_columns:
        raise Feature18ContractError("Feature17 columns/order do not match the registered 17-feature schema")
    if feature17.duplicated(["profile_row_id_a", "profile_row_id_b"]).any():
        raise Feature18ContractError("duplicate pair endpoints in Feature17 input")
    if FEATURE18_COLUMN in feature17.columns:
        raise Feature18ContractError("Feature17 input already contains bert_cos")
    profile_ids = _profile_id_sequence(embedding_profile_ids)
    expected_ids = _profile_id_sequence(expected_profile_ids)
    if len(set(profile_ids)) != len(profile_ids) or len(set(expected_ids)) != len(expected_ids):
        raise Feature18ContractError("embedding and expected profile IDs must be unique")
    if profile_ids != expected_ids:
        raise Feature18ContractError("embedding profile ID order does not exactly match the verified snapshot order")
    vectors = np.asarray(embeddings, dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(profile_ids):
        raise Feature18ContractError("embedding matrix shape does not align with profile IDs")
    if vectors.shape[1] != EMBEDDING_DIMENSION:
        raise Feature18ContractError(f"embedding matrix must be {EMBEDDING_DIMENSION}-dimensional")
    if not np.isfinite(vectors).all():
        raise Feature18ContractError("embedding matrix contains non-finite values")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, rtol=0.0, atol=1e-4):
        raise Feature18ContractError("embeddings must already be normalized; implicit renormalization is forbidden")
    row_by_profile_id = {profile_id: row for row, profile_id in enumerate(profile_ids)}
    try:
        left_ids = _profile_id_sequence(feature17.profile_row_id_a.tolist())
        right_ids = _profile_id_sequence(feature17.profile_row_id_b.tolist())
        left = [row_by_profile_id[identifier] for identifier in left_ids]
        right = [row_by_profile_id[identifier] for identifier in right_ids]
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise Feature18ContractError("pair endpoint has no aligned embedding profile ID") from exc
    cosine = np.einsum("ij,ij->i", vectors[left], vectors[right], dtype=np.float32)
    if not np.isfinite(cosine).all() or (cosine < -1.0001).any() or (cosine > 1.0001).any():
        raise Feature18ContractError("computed cosine is outside finite [-1,1]")
    result = feature17.copy()
    result[FEATURE18_COLUMN] = np.clip(cosine, -1.0, 1.0).astype(np.float32)
    if list(result.columns) != expected_columns + [FEATURE18_COLUMN]:
        raise Feature18ContractError("Feature18 must add exactly one final column over Feature17")
    result.attrs["feature18_contract_version"] = CONTRACT_VERSION
    result.attrs["model_identifier"] = MODEL_IDENTIFIER
    result.attrs["model_revision"] = metadata["model_revision"]
    result.attrs["model_weight_sha256"] = metadata["model_weight_sha256"]
    return result
