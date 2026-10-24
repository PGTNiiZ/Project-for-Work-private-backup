"""Domain primitives for merging matched profiles into entities."""

from __future__ import annotations

from collections import Counter

from .text import clean_text


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[int, int] = {}

    def find(self, item: int) -> int:
        if item not in self.parent:
            self.parent[item] = item
            return item
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            self.parent[right_root] = left_root
        else:
            self.parent[left_root] = right_root


def choose_canonical_name(names: list[str]) -> str:
    valid = [clean_text(name) for name in names if clean_text(name)]
    if not valid:
        return ""
    counts = Counter(valid)
    return max(valid, key=lambda name: (counts[name], len(name)))
