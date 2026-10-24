"""Physical sealed-label boundary for authoritative v2."""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field


class LabelAccessError(RuntimeError):
    """Raised when sealed labels are requested outside final evaluation."""


@dataclass
class SealedLabels:
    """Label store whose only allowed read phase is ``final_evaluation``."""

    _values: dict[str, int]
    audit: list[dict[str, object]] = field(default_factory=list)

    def join(self, pair_keys: list[str], *, phase: str) -> list[int]:
        allowed = phase == "final_evaluation"
        entry = {
            "phase": phase,
            "resource": "sealed_test_labels",
            "allowed": allowed,
            "source": f"{inspect.getmodule(self).__name__}.SealedLabels.join",
        }
        self.audit.append(entry)
        if not allowed:
            raise LabelAccessError(
                f"sealed_test_labels cannot be accessed during {phase}; "
                "only final_evaluation may join them"
            )
        return [self._values[key] for key in pair_keys]

    @property
    def pre_final_reads(self) -> int:
        return sum(not bool(entry["allowed"]) for entry in self.audit)
