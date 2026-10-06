"""Versioned CRM business-cost policy shared by decision experiments."""

from __future__ import annotations

from dataclasses import dataclass


CRM_COST_POLICY_VERSION = "crm_derived_v1"


@dataclass(frozen=True)
class CostWeights:
    """Normalized costs derived from 100 THB/hour CRM operations."""

    fp: float = 2.0
    fn: float = 1.0
    review: float = 0.1

    def __post_init__(self) -> None:
        if min(self.fp, self.fn, self.review) < 0.0:
            raise ValueError("cost weights must be non-negative")

    def as_dict(self) -> dict[str, float]:
        return {"W_FP": self.fp, "W_FN": self.fn, "W_REV": self.review}

    def cost(self, *, fp: int, fn: int, review: int) -> float:
        return self.fp * fp + self.fn * fn + self.review * review


CRM_COST_WEIGHTS = CostWeights()