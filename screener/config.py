from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCORED_SNAPSHOT_INPUT_PATH = Path("data/scored_snapshots.jsonl")
DEFAULT_FILTERED_SNAPSHOT_OUTPUT_PATH = Path("data/filtered_snapshots.jsonl")
DEFAULT_FILTER_VERSION = "v0"


@dataclass(frozen=True, slots=True)
class ScreenerConfig:
    input_path: Path = DEFAULT_SCORED_SNAPSHOT_INPUT_PATH
    output_path: Path = DEFAULT_FILTERED_SNAPSHOT_OUTPUT_PATH
    filter_version: str = DEFAULT_FILTER_VERSION


def load_config() -> ScreenerConfig:
    input_path = Path(
        os.getenv("SCREENER_INPUT_PATH", str(DEFAULT_SCORED_SNAPSHOT_INPUT_PATH))
    )
    output_path = Path(
        os.getenv("SCREENER_OUTPUT_PATH", str(DEFAULT_FILTERED_SNAPSHOT_OUTPUT_PATH))
    )

    return ScreenerConfig(
        input_path=input_path,
        output_path=output_path,
    )
