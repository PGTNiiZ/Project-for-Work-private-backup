"""Production MATCH/REVIEW/NO_MATCH threshold policy."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ThresholdPolicy:
    match_threshold: float = 0.98
    review_threshold: float = 0.95

    def __post_init__(self) -> None:
        if not 0.0 <= self.review_threshold <= self.match_threshold <= 1.0:
            raise ValueError(
                "thresholds must satisfy 0 <= review_threshold <= "
                "match_threshold <= 1"
            )

    def decide(self, scores, *, no_match_label: str = "NO_MATCH") -> np.ndarray:
        values = np.asarray(scores, dtype=float)
        return np.where(
            values >= self.match_threshold,
            "MATCH",
            np.where(values >= self.review_threshold, "REVIEW", no_match_label),
        )

    @staticmethod
    def decision_sources(decisions) -> np.ndarray:
        values = np.asarray(decisions)
        return np.where(
            values == "MATCH",
            "AUTO_HIGH",
            np.where(values == "REVIEW", "AUTO_REVIEW", "AUTO_LOW"),
        )

    @staticmethod
    def review_statuses(decisions) -> np.ndarray:
        values = np.asarray(decisions)
        return np.where(
            values == "MATCH",
            "APPROVED",
            np.where(values == "REVIEW", "PENDING", "SKIPPED"),
        )
