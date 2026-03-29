from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_FILTERED_SNAPSHOTS_PATH = Path("data/filtered_snapshots.jsonl")
DEFAULT_LABELS_PATH = Path("data/labels/review_labels.jsonl")
DEFAULT_AUDIT_OUTPUT_PATH = Path("data/reports/dataset_audit.json")
DEFAULT_AUDIT_VERSION = "v0"
AUDIT_FIELDS = (
    "created_at",
    "creator",
    "token_standard",
    "bonding_curve",
    "migration_target",
    "snapshot_built_at",
)


@dataclass(frozen=True, slots=True)
class AuditConfig:
    input_path: Path = DEFAULT_FILTERED_SNAPSHOTS_PATH
    labels_path: Path = DEFAULT_LABELS_PATH
    output_path: Path = DEFAULT_AUDIT_OUTPUT_PATH
    audit_version: str = DEFAULT_AUDIT_VERSION


def load_config() -> AuditConfig:
    input_path = Path(os.getenv("AUDIT_INPUT_PATH", str(DEFAULT_FILTERED_SNAPSHOTS_PATH)))
    labels_path = Path(os.getenv("AUDIT_LABELS_PATH", str(DEFAULT_LABELS_PATH)))
    output_path = Path(os.getenv("AUDIT_REPORT_PATH", str(DEFAULT_AUDIT_OUTPUT_PATH)))

    return AuditConfig(
        input_path=input_path,
        labels_path=labels_path,
        output_path=output_path,
    )
