"""Versioned feature-set definitions for name-similarity experiments."""

from __future__ import annotations

from dataclasses import dataclass


SCHEMA_VERSION = "name-sim-v1"
EXPERIMENT_GROUPS = (
    "name_damerau",
    "name_char_ngram",
    "name_token_set",
    "name_handle",
    "name_cross_field",
    "name_phonetic",
)


@dataclass(frozen=True)
class FeatureSet:
    name: str
    extra_groups: tuple[str, ...] = ()


FEATURE_SETS = {
    "N0": FeatureSet("N0"),
    "N1": FeatureSet("N1", ("name_damerau",)),
    "N2": FeatureSet("N2", ("name_char_ngram",)),
    "N3": FeatureSet("N3", ("name_token_set",)),
    "N4": FeatureSet("N4", ("name_handle",)),
    "N5": FeatureSet("N5", ("name_cross_field",)),
    "N6": FeatureSet("N6"),
    "N7": FeatureSet("N7", ("name_phonetic",)),
}


def resolve_feature_set(name: str, include_groups: tuple[str, ...] = ()) -> FeatureSet:
    """Resolve a named experiment; N6 combines validation-selected extra groups."""
    try:
        feature_set = FEATURE_SETS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown feature set {name!r}; expected one of {sorted(FEATURE_SETS)}") from exc
    if name != "N6" or not include_groups:
        return feature_set
    invalid = sorted(set(include_groups) - set(EXPERIMENT_GROUPS))
    if invalid:
        raise ValueError(f"Unknown experimental feature groups: {invalid}")
    return FeatureSet("N6", tuple(dict.fromkeys(include_groups)))


def group_for_feature(column: str) -> str:
    """Return the evidence family used for grouped permutation importance."""
    if column in {
        "username_jaro", "username_lev", "username_token_sort",
        "fullname_jaro", "fullname_lev", "fullname_token_sort",
    }:
        return "name_existing"
    if column.startswith("name_damerau_"):
        return "name_damerau"
    if column.startswith("name_char_ngram_"):
        return "name_char_ngram"
    if column.startswith("name_token_set_"):
        return "name_token_set"
    if column.startswith("name_handle_"):
        return "name_handle"
    if column.startswith("name_cross_"):
        return "name_cross_field"
    if column.startswith("name_phonetic_"):
        return "name_phonetic"
    if column.startswith("image_"):
        return "image"
    if column.startswith("bio_") or column.startswith("mention_") or column.startswith("hashtag_"):
        return "bio"
    if column.startswith("domain_") or column.startswith("url_"):
        return "url"
    if column.startswith("location_"):
        return "location"
    if column.startswith("style_"):
        return "style"
    if column.startswith("platform_"):
        return "platform"
    return "other"