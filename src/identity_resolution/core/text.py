"""Normalization helpers used at production workflow boundaries."""

from __future__ import annotations

import json
import math


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def lower_text(value: object) -> str:
    return clean_text(value).lower()


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)
