from __future__ import annotations

from datetime import datetime, timezone

from scorer.config import ScorerConfig
from scorer.io import read_jsonl, write_jsonl_overwrite
from scorer.models.scored_snapshot import ScoredSnapshot
from scorer.rules import score_snapshot


def run_scoring(config: ScorerConfig) -> list[ScoredSnapshot]:
    scored_at = _utc_now()
    snapshot_records = read_jsonl(config.input_path)

    scored_snapshots = [
        score_snapshot(
            snapshot_record=record,
            score_version=config.score_version,
            scored_at=scored_at,
        )
        for record in sorted(snapshot_records, key=_sort_key)
    ]

    write_jsonl_overwrite(config.output_path, scored_snapshots)
    return scored_snapshots


def _sort_key(record: dict[str, object]) -> tuple[str, str]:
    mint = record.get("mint")
    snapshot_built_at = record.get("snapshot_built_at")
    return (
        mint if isinstance(mint, str) else "",
        snapshot_built_at if isinstance(snapshot_built_at, str) else "",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
