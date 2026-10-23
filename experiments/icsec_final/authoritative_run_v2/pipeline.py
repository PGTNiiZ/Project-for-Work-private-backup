"""Phase boundary preventing sealed labels entering pre-final data frames."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .label_sealing import SealedLabels


@dataclass(frozen=True)
class PublicPairData:
    """Pair/profile/features data; labels are intentionally not a field."""

    rows: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        forbidden = {"actual", "label", "ground_truth", "user_folder"}
        found = forbidden.intersection(*(row.keys() for row in self.rows)) if self.rows else set()
        if found:
            raise ValueError(f"pre-final data contains forbidden label/entity fields: {sorted(found)}")


@dataclass
class V2EvaluationBoundary:
    """Owns public data during selection and opens labels only for final evaluation."""

    public_data: PublicPairData
    sealed_labels: SealedLabels
    phase: str = "training"

    def set_phase(self, phase: str) -> None:
        self.phase = phase

    def final_join(self, pair_keys: list[str]) -> list[dict[str, Any]]:
        if self.phase != "final_evaluation":
            raise RuntimeError("final_join is only available in final_evaluation phase")
        values = self.sealed_labels.join(pair_keys, phase=self.phase)
        return [{**row, "actual": value} for row, value in zip(self.public_data.rows, values)]
