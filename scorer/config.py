from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SNAPSHOT_INPUT_PATH = Path("data/snapshots.jsonl")
DEFAULT_SCORED_SNAPSHOT_OUTPUT_PATH = Path("data/scored_snapshots.jsonl")
DEFAULT_SCORE_VERSION = "v0"


@dataclass(frozen=True, slots=True)
class ScorerConfig:
    input_path: Path = DEFAULT_SNAPSHOT_INPUT_PATH
    output_path: Path = DEFAULT_SCORED_SNAPSHOT_OUTPUT_PATH
    score_version: str = DEFAULT_SCORE_VERSION


def load_config() -> ScorerConfig:
    input_path_value = os.getenv("SCORER_INPUT_PATH", str(DEFAULT_SNAPSHOT_INPUT_PATH))
    output_path_value = os.getenv(
        "SCORER_OUTPUT_PATH",
        str(DEFAULT_SCORED_SNAPSHOT_OUTPUT_PATH),
    )

    return ScorerConfig(
        input_path=Path(input_path_value),
        output_path=Path(output_path_value),
    )
