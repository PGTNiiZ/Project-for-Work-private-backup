"""Stable pair identifiers for profile-row pairs."""

from __future__ import annotations


def pair_key(a: int, b: int) -> int:
    """Pack an unordered pair of non-negative 32-bit IDs into one integer."""
    x, y = (a, b) if a < b else (b, a)
    return (x << 32) | y


def unpack_pair_key(key: int) -> tuple[int, int]:
    return key >> 32, key & 0xFFFFFFFF
