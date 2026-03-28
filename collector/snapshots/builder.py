from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

from collector.config import DEFAULT_SNAPSHOT_OUTPUT_PATH, load_storage_config
from collector.models.feature_snapshot import FeatureSnapshot
from collector.storage.jsonl_writer import JsonlWriter

logger = logging.getLogger(__name__)


def build_snapshots(
    create_events_path: Path,
    migration_events_path: Path,
    snapshot_output_path: Path = DEFAULT_SNAPSHOT_OUTPUT_PATH,
) -> list[FeatureSnapshot]:
    states: dict[str, dict[str, Any]] = {}
    snapshot_built_at = _utc_now()

    for record in _read_jsonl(create_events_path):
        mint = _read_string(record.get("mint"))
        if not mint:
            continue

        state = states.setdefault(mint, _new_state(mint))
        observed_at = _read_string(record.get("observed_at"))
        state["first_seen_at"] = _earliest_timestamp(state["first_seen_at"], observed_at)
        state["created_at"] = _earliest_timestamp(state["created_at"], observed_at)
        state["token_standard"] = state["token_standard"] or _read_string(
            record.get("token_standard")
        )
        state["creator"] = state["creator"] or _read_string(record.get("creator"))
        state["bonding_curve"] = state["bonding_curve"] or _read_string(
            record.get("bonding_curve")
        )
        _add_source(state, record.get("source"))
        state["event_count"] += 1

    for record in _read_jsonl(migration_events_path):
        mint = _read_string(record.get("mint"))
        if not mint:
            continue

        state = states.setdefault(mint, _new_state(mint))
        observed_at = _read_string(record.get("observed_at"))
        state["first_seen_at"] = _earliest_timestamp(state["first_seen_at"], observed_at)
        state["migrated_at"] = _earliest_timestamp(state["migrated_at"], observed_at)
        state["has_migrated"] = True
        state["creator"] = state["creator"] or _read_string(record.get("creator"))
        state["migration_target"] = state["migration_target"] or _read_string(
            record.get("pool")
        )
        _add_source(state, record.get("source"))
        state["event_count"] += 1

    snapshots = [
        FeatureSnapshot(
            mint=state["mint"],
            snapshot_built_at=snapshot_built_at,
            first_seen_at=state["first_seen_at"],
            created_at=state["created_at"],
            migrated_at=state["migrated_at"],
            has_migrated=state["has_migrated"],
            token_standard=state["token_standard"],
            creator=state["creator"],
            bonding_curve=state["bonding_curve"],
            migration_target=state["migration_target"],
            source_count=len(state["sources"]),
            event_count=state["event_count"],
        )
        for state in sorted(states.values(), key=lambda item: item["mint"])
    ]

    JsonlWriter(snapshot_output_path).overwrite_items(snapshots)
    return snapshots


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    storage_config = load_storage_config()
    snapshots = build_snapshots(
        create_events_path=storage_config.output_path,
        migration_events_path=storage_config.migration_output_path,
        snapshot_output_path=storage_config.snapshot_output_path,
    )
    logger.info(
        "Wrote %s snapshots to %s",
        len(snapshots),
        storage_config.snapshot_output_path,
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        logger.info("JSONL input not found, treating as empty: %s", path)
        return []

    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            try:
                record = json.loads(stripped_line)
            except json.JSONDecodeError as error:
                logger.warning(
                    "Skipping malformed JSONL line %s in %s: %s",
                    line_number,
                    path,
                    error,
                )
                continue

            if not isinstance(record, dict):
                logger.warning(
                    "Skipping non-object JSONL line %s in %s",
                    line_number,
                    path,
                )
                continue

            records.append(record)

    return records


def _new_state(mint: str) -> dict[str, Any]:
    return {
        "mint": mint,
        "first_seen_at": None,
        "created_at": None,
        "migrated_at": None,
        "has_migrated": False,
        "token_standard": None,
        "creator": None,
        "bonding_curve": None,
        "migration_target": None,
        "sources": set(),
        "event_count": 0,
    }


def _read_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _earliest_timestamp(
    current_value: str | None,
    candidate_value: str | None,
) -> str | None:
    if current_value is None:
        return candidate_value
    if candidate_value is None:
        return current_value
    return min(current_value, candidate_value)


def _add_source(state: dict[str, Any], value: Any) -> None:
    source = _read_string(value)
    if source is not None:
        state["sources"].add(source)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
