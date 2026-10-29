"""Process-wide sealed-label value guard and runtime access audit for v2r1.

The scientific invariant is defined precisely as:

    SEALED_TEST LABEL VALUES MATERIALIZED BEFORE FINAL_EVALUATION == 0

"Materialized" means the ground-truth ``actual`` column of a registered
sealed-label artifact is loaded into memory. Hashing bytes, reading parquet
footers/schema/row counts, or loading ONLY the safe ``pair_key`` column are
explicitly allowed pre-final and are audited as non-materializing events.

The guard patches ``pandas.read_parquet`` and ``pyarrow.parquet.read_table``
for the whole process, so every code path used by the scientific CLI is
covered — not only ``LazySealedLabelStore``.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

LABEL_COLUMN = "actual"


class SealedLabelViolation(RuntimeError):
    """Raised when sealed-test label values would be materialized pre-final."""


@dataclass
class SealedLabelGuard:
    """Singleton-style runtime guard over registered sealed-label artifacts."""

    sealed_paths: set[str] = field(default_factory=set)
    phase: str = "PREPARATION"
    events: list[dict[str, Any]] = field(default_factory=list)
    _installed: bool = False
    _original_pd_read: Any = None
    _original_pq_read: Any = None

    def register(self, path: str | Path) -> None:
        self.sealed_paths.add(str(Path(path).resolve()))

    def set_phase(self, phase: str) -> None:
        self.phase = phase
        self.events.append({"event": "phase_change", "phase": phase,
                            "order": len(self.events), "timestamp": time.time()})

    def _is_sealed(self, path: object) -> bool:
        try:
            return str(Path(str(path)).resolve()) in self.sealed_paths
        except (TypeError, ValueError, OSError):
            return False

    def _audit(self, *, resource: str, operation: str, columns: Any,
               materialized: bool, allowed: bool) -> None:
        self.events.append({
            "event": "sealed_artifact_access", "phase": self.phase,
            "resource": resource, "operation": operation,
            "requested_columns": list(columns) if columns is not None else None,
            "label_column_materialized": materialized, "allowed": allowed,
            "order": len(self.events), "timestamp": time.time(),
        })

    def _check(self, path: object, columns: Any, operation: str):
        if not self._is_sealed(path):
            return
        materializes = columns is None or LABEL_COLUMN in set(columns)
        allowed = (not materializes) or self.phase == "FINAL_EVALUATION"
        self._audit(resource=str(path), operation=operation, columns=columns,
                    materialized=materializes and allowed, allowed=allowed)
        if not allowed:
            raise SealedLabelViolation(
                f"sealed-test label values may not be materialized during "
                f"phase {self.phase!r} (path={path})")

    def install(self) -> None:
        if self._installed:
            return
        self._original_pd_read = pd.read_parquet
        self._original_pq_read = pq.read_table
        guard = self

        def guarded_pd_read(path, *args, **kwargs):
            guard._check(path, kwargs.get("columns"), "pandas.read_parquet")
            return guard._original_pd_read(path, *args, **kwargs)

        def guarded_pq_read(source, *args, **kwargs):
            guard._check(source, kwargs.get("columns"), "pyarrow.parquet.read_table")
            return guard._original_pq_read(source, *args, **kwargs)

        pd.read_parquet = guarded_pd_read
        pq.read_table = guarded_pq_read
        self._installed = True

    def uninstall(self) -> None:
        if self._installed:
            pd.read_parquet = self._original_pd_read
            pq.read_table = self._original_pq_read
            self._installed = False

    # ---- derived (never hard-coded) audit counts -------------------------
    def pre_final_materializations(self) -> int:
        return sum(1 for e in self.events
                   if e.get("event") == "sealed_artifact_access"
                   and e.get("label_column_materialized")
                   and e.get("phase") != "FINAL_EVALUATION")

    def final_materializations(self) -> int:
        return sum(1 for e in self.events
                   if e.get("event") == "sealed_artifact_access"
                   and e.get("label_column_materialized")
                   and e.get("phase") == "FINAL_EVALUATION")

    def report(self) -> dict[str, Any]:
        return {
            "invariant": "SEALED_TEST_LABEL_VALUES_MATERIALIZED_BEFORE_FINAL_EVALUATION == 0",
            "pre_final_label_value_materializations": self.pre_final_materializations(),
            "final_evaluation_label_value_materializations": self.final_materializations(),
            "events": self.events,
        }


GUARD = SealedLabelGuard()


# ---- label-free preflight validation helpers ----------------------------

def sealed_artifact_metadata(path: str | Path) -> dict[str, Any]:
    """Inspect a sealed-label parquet WITHOUT materializing label values."""
    parquet = pq.ParquetFile(str(path))
    schema_names = list(parquet.schema_arrow.names)
    if GUARD._is_sealed(path):
        GUARD._audit(resource=str(path), operation="parquet_footer_inspection",
                     columns=[], materialized=False, allowed=True)
    return {"columns": schema_names, "row_count": int(parquet.metadata.num_rows)}


def sealed_pair_keys(path: str | Path) -> pd.Series:
    """Load ONLY the safe pair_key column (label-free by construction)."""
    if GUARD._is_sealed(path):
        GUARD._audit(resource=str(path), operation="pair_key_only_read",
                     columns=["pair_key"], materialized=False, allowed=True)
    table = pq.ParquetFile(str(path)).read(columns=["pair_key"])
    return table.to_pandas()["pair_key"]
