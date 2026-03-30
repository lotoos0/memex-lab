from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_FILTERED_SNAPSHOTS_V1_PATH = Path("data/filtered_snapshots_v1.jsonl")
DEFAULT_LABELS_PATH = Path("data/labels/review_labels.jsonl")
DEFAULT_REVIEW_CANDIDATES_PATH = Path("data/review_candidates.jsonl")
DEFAULT_SELECTION_VERSION = "v0"


@dataclass(frozen=True, slots=True)
class SelectorConfig:
    input_path: Path = DEFAULT_FILTERED_SNAPSHOTS_V1_PATH
    labels_path: Path = DEFAULT_LABELS_PATH
    output_path: Path = DEFAULT_REVIEW_CANDIDATES_PATH
    selection_version: str = DEFAULT_SELECTION_VERSION

