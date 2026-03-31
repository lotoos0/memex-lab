from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StatusRow:
    label: str
    relative_path: str
    exists: bool
    size_bytes: int | None
    modified_at: str | None


TRACKED_PATHS = (
    ("Create events", "data/events.jsonl"),
    ("Migration events", "data/migration_events.jsonl"),
    ("Snapshots", "data/snapshots.jsonl"),
    ("Scored snapshots v0", "data/scored_snapshots.jsonl"),
    ("Scored snapshots v1", "data/scored_snapshots_v1.jsonl"),
    ("Scorer compare report", "data/reports/scorer_v0_vs_v1.json"),
    ("Filtered snapshots", "data/filtered_snapshots.jsonl"),
    ("Labels", "data/labels/review_labels.jsonl"),
    ("Dataset audit", "data/reports/dataset_audit.json"),
    ("Review candidates", "data/review_candidates.jsonl"),
    ("Candidate audit", "data/reports/candidate_audit.json"),
    ("Review queue now", "data/review_queue_now.jsonl"),
    ("Review queue if time", "data/review_queue_if_time.jsonl"),
    ("Review outcomes", "data/review_outcomes.jsonl"),
    ("Review feedback report", "data/reports/review_feedback_report.json"),
)


def collect_status_rows(repo_root: Path) -> list[StatusRow]:
    rows: list[StatusRow] = []
    for label, relative_path in TRACKED_PATHS:
        target = repo_root / relative_path
        if target.exists():
            stat = target.stat()
            rows.append(
                StatusRow(
                    label=label,
                    relative_path=relative_path,
                    exists=True,
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )
            continue

        rows.append(
            StatusRow(
                label=label,
                relative_path=relative_path,
                exists=False,
                size_bytes=None,
                modified_at=None,
            )
        )
    return rows


def format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "-"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"
