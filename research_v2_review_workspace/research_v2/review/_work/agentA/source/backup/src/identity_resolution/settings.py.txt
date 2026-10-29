"""Central paths and production defaults for the ML system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    root: Path = PROJECT_ROOT

    @property
    def profiles(self) -> Path:
        return self.root / "data_for_project" / "normalized_profiles_with_profile_id.csv"

    @property
    def train_data(self) -> Path:
        return self.root / "train_data"

    @property
    def feature_run(self) -> Path:
        return self.train_data / "stage9_pipeline_chunked"

    @property
    def multimodal_run(self) -> Path:
        return self.train_data / "stage7_13_multimodal_suite"

    @property
    def production_model_run(self) -> Path:
        return self.multimodal_run / "runs" / "image_context_r075_h20_s42"

    @property
    def prediction_run(self) -> Path:
        return self.train_data / "stage7_14_full_candidate_pipeline"

    @property
    def resolution_run(self) -> Path:
        return self.train_data / "stage15_crm_entity_pipeline"

    @property
    def decision_artifacts(self) -> Path:
        return self.root / "artifacts" / "decisioning"

    @property
    def evaluation_artifacts(self) -> Path:
        return self.root / "artifacts" / "evaluation"


PATHS = Paths()
