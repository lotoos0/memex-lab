from __future__ import annotations

from typing import Any

from screener.models.filtered_snapshot import FilteredSnapshot

BLOCKING_FLAGS = frozenset(
    {
        "missing_create_event",
        "lifecycle_order_invalid",
        "missing_mint",
    }
)


def filter_snapshot(
    scored_record: dict[str, Any],
    *,
    filter_version: str,
) -> FilteredSnapshot:
    mint = _read_string(scored_record.get("mint")) or ""
    snapshot_built_at = _read_string(scored_record.get("snapshot_built_at"))
    first_seen_at = _read_string(scored_record.get("first_seen_at"))
    created_at = _read_string(scored_record.get("created_at"))
    migrated_at = _read_string(scored_record.get("migrated_at"))
    has_migrated = bool(scored_record.get("has_migrated"))
    token_standard = _read_string(scored_record.get("token_standard"))
    creator = _read_string(scored_record.get("creator"))
    bonding_curve = _read_string(scored_record.get("bonding_curve"))
    migration_target = _read_string(scored_record.get("migration_target"))
    source_count = _read_non_negative_int(scored_record.get("source_count"))
    event_count = _read_non_negative_int(scored_record.get("event_count"))
    score_version = _read_string(scored_record.get("score_version")) or ""
    score_total = _read_int(scored_record.get("score_total"))
    score_reasons = _read_string_list(scored_record.get("score_reasons"))
    score_flags = _read_string_list(scored_record.get("score_flags"))
    scored_at = _read_string(scored_record.get("scored_at")) or ""
    has_blocking_flags = any(flag in BLOCKING_FLAGS for flag in score_flags)
    is_complete_record = _is_complete_record(
        created_at=created_at,
        creator=creator,
        bonding_curve=bonding_curve,
        has_migrated=has_migrated,
        migration_target=migration_target,
    )
    quality_band, filter_reasons = _classify_record(
        score_total=score_total,
        has_blocking_flags=has_blocking_flags,
        is_complete_record=is_complete_record,
    )

    return FilteredSnapshot(
        mint=mint,
        snapshot_built_at=snapshot_built_at,
        first_seen_at=first_seen_at,
        created_at=created_at,
        migrated_at=migrated_at,
        has_migrated=has_migrated,
        token_standard=token_standard,
        creator=creator,
        bonding_curve=bonding_curve,
        migration_target=migration_target,
        source_count=source_count,
        event_count=event_count,
        score_version=score_version,
        score_total=score_total,
        score_reasons=score_reasons,
        score_flags=score_flags,
        scored_at=scored_at,
        quality_band=quality_band,
        is_complete_record=is_complete_record,
        has_blocking_flags=has_blocking_flags,
        filter_version=filter_version,
        filter_reasons=filter_reasons,
    )


def _classify_record(
    *,
    score_total: int,
    has_blocking_flags: bool,
    is_complete_record: bool,
) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if score_total >= 7 and not has_blocking_flags:
        reasons.append("score_total>=7")
        reasons.append("no_blocking_flags")
        if is_complete_record:
            reasons.append("complete_record")
        return "strong", reasons

    if score_total <= 3:
        reasons.append("score_total<=3")
        if has_blocking_flags:
            reasons.append("blocking_flags_present")
        return "weak", reasons

    if 4 <= score_total <= 6:
        reasons.append("score_total_between_4_and_6")
    else:
        reasons.append("score_total>=7")
        reasons.append("blocking_flags_present")

    if not is_complete_record:
        reasons.append("incomplete_record")

    return "partial", reasons


def _is_complete_record(
    *,
    created_at: str | None,
    creator: str | None,
    bonding_curve: str | None,
    has_migrated: bool,
    migration_target: str | None,
) -> bool:
    return all(
        [
            created_at,
            creator,
            bonding_curve,
            has_migrated,
            migration_target,
        ]
    )


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _read_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0


def _read_non_negative_int(value: Any) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _read_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
