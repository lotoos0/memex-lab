from __future__ import annotations

from typing import Any

from selector.rules import CANDIDATE_CLASS_ORDER, build_label_map


def build_candidate_record(
    filtered_record: dict[str, Any],
    *,
    label_record: dict[str, str] | None,
    selection_version: str,
) -> tuple[dict[str, Any], bool]:
    mint = _read_string(filtered_record.get("mint")) or ""
    score_flags = _read_string_list(filtered_record.get("score_flags"))
    quality_band = _read_string(filtered_record.get("quality_band")) or "unknown"
    label = label_record["label"] if label_record is not None else None
    label_note = label_record.get("note") if label_record is not None else None
    label_labeled_at = (
        label_record.get("labeled_at") if label_record is not None else None
    )

    candidate_class, candidate_reasons, label_influenced = classify_candidate(
        quality_band=quality_band,
        has_migrated=bool(filtered_record.get("has_migrated")),
        has_blocking_flags=bool(filtered_record.get("has_blocking_flags")),
        has_migration_only_flag="migration_only" in score_flags,
        created_at=_read_string(filtered_record.get("created_at")),
        migrated_at=_read_string(filtered_record.get("migrated_at")),
        label=label,
    )

    return (
        {
            "mint": mint,
            "candidate_class": candidate_class,
            "candidate_reasons": candidate_reasons,
            "selection_version": selection_version,
            "quality_band": quality_band,
            "score_version": _read_string(filtered_record.get("score_version")),
            "score_total": _read_int(filtered_record.get("score_total")),
            "score_reasons": _read_string_list(filtered_record.get("score_reasons")),
            "score_flags": score_flags,
            "filter_reasons": _read_string_list(filtered_record.get("filter_reasons")),
            "has_migrated": bool(filtered_record.get("has_migrated")),
            "has_blocking_flags": bool(filtered_record.get("has_blocking_flags")),
            "is_complete_record": bool(filtered_record.get("is_complete_record")),
            "created_at": _read_string(filtered_record.get("created_at")),
            "migrated_at": _read_string(filtered_record.get("migrated_at")),
            "token_standard": _read_string(filtered_record.get("token_standard")),
            "creator": _read_string(filtered_record.get("creator")),
            "migration_target": _read_string(filtered_record.get("migration_target")),
            "label": label,
            "label_labeled_at": label_labeled_at,
            "label_note": label_note,
        },
        label_influenced,
    )


def classify_candidate(
    *,
    quality_band: str,
    has_migrated: bool,
    has_blocking_flags: bool,
    has_migration_only_flag: bool,
    created_at: str | None,
    migrated_at: str | None,
    label: str | None,
) -> tuple[str, list[str], bool]:
    if label == "suspect":
        return "ignore_for_now", ["label_suspect"], True

    if has_blocking_flags:
        return "ignore_for_now", ["blocking_flags_present"], False

    if has_migration_only_flag:
        return "ignore_for_now", ["migration_only"], False

    if created_at is None and migrated_at is None:
        return "ignore_for_now", ["missing_lifecycle_coverage"], False

    if quality_band == "strong":
        return "review_now", ["quality_band_strong"], False

    if quality_band == "partial":
        if has_migrated:
            return "review_now", ["quality_band_partial", "migrated_partial"], False
        if label == "interesting":
            return (
                "review_if_time",
                ["quality_band_partial", "interesting_label_rescue"],
                True,
            )
        if label == "review_later":
            return (
                "review_if_time",
                ["quality_band_partial", "review_later_label_rescue"],
                True,
            )
        return (
            "ignore_for_now",
            ["quality_band_partial", "non_migrated_partial_default_ignore"],
            False,
        )

    return "ignore_for_now", ["quality_band_not_reviewable"], False


def sort_key(candidate_record: dict[str, Any]) -> tuple[int, str]:
    candidate_class = candidate_record.get("candidate_class")
    mint = candidate_record.get("mint")
    return (
        CANDIDATE_CLASS_ORDER.get(candidate_class, 99),
        mint if isinstance(mint, str) else "",
    )


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _read_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _read_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0
