from __future__ import annotations

from datetime import datetime, timezone

from scorer.config import ScorerConfig
from scorer.io import read_jsonl, write_jsonl_overwrite
from scorer.models.scored_snapshot import ScoredSnapshot
from scorer.rules import score_snapshot as score_snapshot_v0
from scorer.rules_v1 import score_snapshot as score_snapshot_v1
from scorer.rules_v2 import score_snapshot as score_snapshot_v2


def run_scoring(
    config: ScorerConfig,
    *,
    score_version: str | None = None,
) -> list[ScoredSnapshot]:
    resolved_score_version = score_version or config.score_version
    scored_at = _utc_now()
    snapshot_records = read_jsonl(config.input_path)
    score_snapshot = _get_score_snapshot_function(resolved_score_version)

    scored_snapshots = [
        score_snapshot(
            snapshot_record=record,
            score_version=resolved_score_version,
            scored_at=scored_at,
        )
        for record in sorted(snapshot_records, key=_sort_key)
    ]

    write_jsonl_overwrite(config.output_path_for(resolved_score_version), scored_snapshots)
    return scored_snapshots


def get_output_path(config: ScorerConfig, *, score_version: str | None = None) -> str:
    resolved_score_version = score_version or config.score_version
    return str(config.output_path_for(resolved_score_version))


def _get_score_snapshot_function(score_version: str):
    if score_version == "v0":
        return score_snapshot_v0
    if score_version == "v1":
        return score_snapshot_v1
    if score_version == "v2":
        return score_snapshot_v2
    raise ValueError(f"Unsupported score version: {score_version}")


def _sort_key(record: dict[str, object]) -> tuple[str, str]:
    mint = record.get("mint")
    snapshot_built_at = record.get("snapshot_built_at")
    return (
        mint if isinstance(mint, str) else "",
        snapshot_built_at if isinstance(snapshot_built_at, str) else "",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
