from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_FILTERED_SNAPSHOTS_V1_PATH = Path("data/filtered_snapshots_v1.jsonl")
DEFAULT_LABELS_PATH = Path("data/labels/review_labels.jsonl")
DEFAULT_REVIEW_CANDIDATES_PATH = Path("data/review_candidates.jsonl")
DEFAULT_REVIEW_CANDIDATES_V2_PATH = Path("data/review_candidates_v2.jsonl")
DEFAULT_COMPARISON_OUTPUT_PATH = Path("data/reports/selector_v1_vs_v2.json")
DEFAULT_SELECTION_VERSION = "v0"
DEFAULT_SELECTION_VERSION_V2 = "v2"


@dataclass(frozen=True, slots=True)
class SelectorConfig:
    input_path: Path = DEFAULT_FILTERED_SNAPSHOTS_V1_PATH
    labels_path: Path = DEFAULT_LABELS_PATH
    output_path: Path = DEFAULT_REVIEW_CANDIDATES_PATH
    output_path_v2: Path = DEFAULT_REVIEW_CANDIDATES_V2_PATH
    comparison_output_path: Path = DEFAULT_COMPARISON_OUTPUT_PATH
    selection_version: str = DEFAULT_SELECTION_VERSION
    selection_version_v2: str = DEFAULT_SELECTION_VERSION_V2

    def output_path_for(self, selector_version: str) -> Path:
        if selector_version == "v2":
            return self.output_path_v2
        return self.output_path

    def selection_marker_for(self, selector_version: str) -> str:
        if selector_version == "v2":
            return self.selection_version_v2
        return self.selection_version
