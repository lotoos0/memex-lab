from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SNAPSHOT_INPUT_PATH = Path("data/snapshots.jsonl")
DEFAULT_SCORED_SNAPSHOT_V0_OUTPUT_PATH = Path("data/scored_snapshots.jsonl")
DEFAULT_SCORED_SNAPSHOT_V1_OUTPUT_PATH = Path("data/scored_snapshots_v1.jsonl")
DEFAULT_SCORER_COMPARISON_OUTPUT_PATH = Path("data/reports/scorer_v0_vs_v1.json")
DEFAULT_SCORE_VERSION = "v0"


@dataclass(frozen=True, slots=True)
class ScorerConfig:
    input_path: Path = DEFAULT_SNAPSHOT_INPUT_PATH
    output_v0_path: Path = DEFAULT_SCORED_SNAPSHOT_V0_OUTPUT_PATH
    output_v1_path: Path = DEFAULT_SCORED_SNAPSHOT_V1_OUTPUT_PATH
    comparison_output_path: Path = DEFAULT_SCORER_COMPARISON_OUTPUT_PATH
    score_version: str = DEFAULT_SCORE_VERSION

    def output_path_for(self, score_version: str) -> Path:
        if score_version == "v0":
            return self.output_v0_path
        if score_version == "v1":
            return self.output_v1_path
        raise ValueError(f"Unsupported score version: {score_version}")


def load_config() -> ScorerConfig:
    input_path_value = os.getenv("SCORER_INPUT_PATH", str(DEFAULT_SNAPSHOT_INPUT_PATH))
    output_v0_path_value = os.getenv(
        "SCORER_OUTPUT_PATH",
        str(DEFAULT_SCORED_SNAPSHOT_V0_OUTPUT_PATH),
    )
    output_v1_path_value = os.getenv(
        "SCORER_V1_OUTPUT_PATH",
        str(DEFAULT_SCORED_SNAPSHOT_V1_OUTPUT_PATH),
    )
    comparison_output_path_value = os.getenv(
        "SCORER_COMPARE_OUTPUT_PATH",
        str(DEFAULT_SCORER_COMPARISON_OUTPUT_PATH),
    )

    return ScorerConfig(
        input_path=Path(input_path_value),
        output_v0_path=Path(output_v0_path_value),
        output_v1_path=Path(output_v1_path_value),
        comparison_output_path=Path(comparison_output_path_value),
    )
