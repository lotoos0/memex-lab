from __future__ import annotations

from typing import Any

from scorer.models.scored_snapshot import ScoredSnapshot

KNOWN_TOKEN_STANDARDS = {"legacy", "token2022"}


def score_snapshot(
    snapshot_record: dict[str, Any],
    *,
    score_version: str,
    scored_at: str,
) -> ScoredSnapshot:
    mint = _read_string(snapshot_record.get("mint")) or ""
    snapshot_built_at = _read_string(snapshot_record.get("snapshot_built_at"))
    first_seen_at = _read_string(snapshot_record.get("first_seen_at"))
    created_at = _read_string(snapshot_record.get("created_at"))
    migrated_at = _read_string(snapshot_record.get("migrated_at"))
    has_migrated = bool(snapshot_record.get("has_migrated"))
    token_standard = _read_string(snapshot_record.get("token_standard"))
    creator = _read_string(snapshot_record.get("creator"))
    bonding_curve = _read_string(snapshot_record.get("bonding_curve"))
    migration_target = _read_string(snapshot_record.get("migration_target"))
    source_count = _read_non_negative_int(snapshot_record.get("source_count"))
    event_count = _read_non_negative_int(snapshot_record.get("event_count"))
    has_migration_data = has_migrated or migrated_at is not None

    score_total = 0
    score_reasons: list[str] = []
    score_flags: list[str] = []

    if created_at is not None:
        score_total += 2
        score_reasons.append("has_create_event (+2)")
    else:
        score_flags.append("missing_create_event")

    if creator is not None:
        score_total += 1
        score_reasons.append("creator_present (+1)")
    else:
        score_flags.append("missing_creator")

    if token_standard in KNOWN_TOKEN_STANDARDS:
        score_total += 1
        score_reasons.append("token_standard_known (+1)")
    else:
        score_flags.append("token_standard_unknown")

    if bonding_curve is not None:
        score_total += 1
        score_reasons.append("bonding_curve_present (+1)")
    else:
        score_flags.append("missing_bonding_curve")

    if has_migration_data:
        score_total += 2
        score_reasons.append("has_migration_event (+2)")

    if migration_target is not None:
        score_total += 1
        score_reasons.append("migration_target_present (+1)")
    elif has_migration_data:
        score_flags.append("missing_migration_target")

    lifecycle_order_valid = _is_lifecycle_order_valid(
        created_at=created_at,
        migrated_at=migrated_at,
        has_migration_data=has_migration_data,
    )
    if lifecycle_order_valid:
        score_total += 1
        score_reasons.append("lifecycle_order_valid (+1)")
    elif created_at is not None and has_migration_data:
        score_flags.append("lifecycle_order_invalid")

    if created_at is None or event_count < 1:
        score_flags.append("create_event_count_unexpected")

    if has_migration_data and event_count < 2:
        score_flags.append("migration_event_count_unexpected")

    if source_count < 1:
        score_flags.append("source_count_unexpected")
    elif source_count > event_count and event_count > 0:
        score_flags.append("source_count_exceeds_event_count")

    if first_seen_at is None:
        score_flags.append("missing_first_seen_at")

    if snapshot_built_at is None:
        score_flags.append("missing_snapshot_built_at")

    if not mint:
        score_flags.append("missing_mint")

    return ScoredSnapshot(
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
    )


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _read_non_negative_int(value: Any) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _is_lifecycle_order_valid(
    created_at: str | None,
    migrated_at: str | None,
    has_migration_data: bool,
) -> bool:
    if created_at is None:
        return not has_migration_data
    if not has_migration_data or migrated_at is None:
        return True
    return created_at <= migrated_at
