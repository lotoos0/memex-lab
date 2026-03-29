from __future__ import annotations

from collections import Counter
from typing import Any


def build_overview(
    records: list[dict[str, Any]],
    label_records: list[dict[str, Any]],
) -> dict[str, int]:
    label_map = _build_label_map(label_records)
    labeled_record_count = _count_labeled_records(records, label_map)

    record_mints = {
        mint
        for record in records
        if (mint := _read_non_empty_string(record.get("mint")))
    }
    orphan_label_count = sum(1 for mint in label_map if mint not in record_mints)
    migrated_record_count = sum(1 for record in records if bool(record.get("has_migrated")))
    blocking_record_count = sum(
        1 for record in records if bool(record.get("has_blocking_flags"))
    )
    complete_record_count = sum(
        1 for record in records if bool(record.get("is_complete_record"))
    )

    return {
        "total_records": len(records),
        "total_labeled_records": labeled_record_count,
        "total_migrated_records": migrated_record_count,
        "total_blocking_records": blocking_record_count,
        "total_complete_records": complete_record_count,
        "orphan_label_count": orphan_label_count,
    }


def quality_band_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(
        _read_non_empty_string(record.get("quality_band")) or "unknown"
        for record in records
    )
    return {key: counts[key] for key in sorted(counts)}


def has_migrated_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(bool(record.get("has_migrated")) for record in records)
    return {
        "false": counts.get(False, 0),
        "true": counts.get(True, 0),
    }


def has_blocking_flags_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(bool(record.get("has_blocking_flags")) for record in records)
    return {
        "false": counts.get(False, 0),
        "true": counts.get(True, 0),
    }


def score_total_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(_read_int(record.get("score_total")) for record in records)
    return {str(key): counts[key] for key in sorted(counts)}


def label_distribution(
    records: list[dict[str, Any]],
    label_records: list[dict[str, Any]],
) -> dict[str, Any]:
    label_map = _build_label_map(label_records)
    counts_by_label: Counter[str] = Counter()
    quality_band_crosstab: dict[str, Counter[str]] = {}
    has_migrated_crosstab: dict[str, Counter[str]] = {}

    for record in records:
        mint = _read_non_empty_string(record.get("mint"))
        if not mint:
            continue
        label = label_map.get(mint)
        if label:
            counts_by_label[label] += 1
            quality_band = _read_non_empty_string(record.get("quality_band")) or "unknown"
            has_migrated = "true" if bool(record.get("has_migrated")) else "false"
            quality_band_crosstab.setdefault(label, Counter())[quality_band] += 1
            has_migrated_crosstab.setdefault(label, Counter())[has_migrated] += 1

    return {
        "counts_by_label": {key: counts_by_label[key] for key in sorted(counts_by_label)},
        "label_by_quality_band": {
            label: {band: quality_band_crosstab[label][band] for band in sorted(quality_band_crosstab[label])}
            for label in sorted(quality_band_crosstab)
        },
        "label_by_has_migrated": {
            label: {
                "false": has_migrated_crosstab[label].get("false", 0),
                "true": has_migrated_crosstab[label].get("true", 0),
            }
            for label in sorted(has_migrated_crosstab)
        },
    }


def lifecycle_coverage(records: list[dict[str, Any]]) -> dict[str, int]:
    created_present = 0
    created_missing = 0
    migrated_present = 0
    migrated_missing = 0
    full_lifecycle = 0
    create_only = 0
    migration_only = 0

    for record in records:
        has_created_at = not _is_missing_field(record, "created_at")
        has_migrated_at = not _is_missing_field(record, "migrated_at")

        if has_created_at:
            created_present += 1
        else:
            created_missing += 1

        if has_migrated_at:
            migrated_present += 1
        else:
            migrated_missing += 1

        if has_created_at and has_migrated_at:
            full_lifecycle += 1
        elif has_created_at:
            create_only += 1
        elif has_migrated_at:
            migration_only += 1

    return {
        "created_at_present": created_present,
        "created_at_missing": created_missing,
        "migrated_at_present": migrated_present,
        "migrated_at_missing": migrated_missing,
        "full_lifecycle": full_lifecycle,
        "create_only": create_only,
        "migration_only": migration_only,
    }


def flag_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()

    for record in records:
        score_flags = record.get("score_flags")
        if not isinstance(score_flags, list):
            continue

        for flag in score_flags:
            if isinstance(flag, str) and flag != "":
                counts[flag] += 1

    top_flags = [
        {"flag": flag, "count": count}
        for flag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]

    return {
        "counts_by_flag": {flag: counts[flag] for flag in sorted(counts)},
        "top_flags": top_flags,
    }


def missing_field_distribution(
    records: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for field in fields:
        missing_count = sum(1 for record in records if _is_missing_field(record, field))
        counts[field] = missing_count

    return counts


def _build_label_map(label_records: list[dict[str, Any]]) -> dict[str, str]:
    label_map: dict[str, str] = {}
    for record in label_records:
        mint = _read_non_empty_string(record.get("mint"))
        label = _read_non_empty_string(record.get("label"))
        if mint and label:
            label_map[mint] = label
    return label_map


def _count_labeled_records(
    records: list[dict[str, Any]],
    label_map: dict[str, str],
) -> int:
    count = 0
    for record in records:
        mint = _read_non_empty_string(record.get("mint"))
        if mint and mint in label_map:
            count += 1
    return count


def _is_missing_field(record: dict[str, Any], field: str) -> bool:
    if field not in record:
        return True

    value = record[field]
    return value is None or (isinstance(value, str) and value == "")


def _read_non_empty_string(value: Any) -> str | None:
    if isinstance(value, str) and value != "":
        return value
    return None


def _read_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0
