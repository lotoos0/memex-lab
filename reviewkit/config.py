from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_FILTERED_SNAPSHOTS_PATH = Path("data/filtered_snapshots.jsonl")
DEFAULT_EXPORTS_DIR = Path("data/exports")
DEFAULT_LABELS_PATH = Path("data/labels/review_labels.jsonl")
ALLOWED_LABELS = (
    "interesting",
    "incomplete",
    "suspect",
    "review_later",
)


@dataclass(frozen=True, slots=True)
class ReviewkitPaths:
    filtered_snapshots_path: Path = DEFAULT_FILTERED_SNAPSHOTS_PATH
    exports_dir: Path = DEFAULT_EXPORTS_DIR
    labels_path: Path = DEFAULT_LABELS_PATH

