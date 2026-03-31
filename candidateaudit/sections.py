from __future__ import annotations

from typing import Any

CANDIDATE_CLASSES = ("review_now", "review_if_time", "ignore_for_now")


def candidate_totals(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_records": len(records),
        "total_review_now": _count_by_candidate_class(records, "review_now"),
        "total_review_if_time": _count_by_candidate_class(records, "review_if_time"),
        "total_ignore_for_now": _count_by_candidate_class(records, "ignore_for_now"),
        "total_labeled_records": sum(1 for record in records if _read_string(record.get("label"))),
    }


def candidate_class_distribution(records: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    total_records = len(records)
    counts = {
        candidate_class: _count_by_candidate_class(records, candidate_class)
        for candidate_class in CANDIDATE_CLASSES
    }
    percentages = {
        candidate_class: _percentage(count, total_records)
        for candidate_class, count in counts.items()
    }
    return {
        "counts": counts,
        "percentages": percentages,
    }


def class_label_alignment(records: list[dict[str, Any]]) -> dict[str, Any]:
    labels_by_class = {
        candidate_class: _count_labels_within_class(records, candidate_class)
        for candidate_class in CANDIDATE_CLASSES
    }
    return {
        "labels_within_candidate_class": labels_by_class,
        "interesting_in_review_now": _count_matching_label(records, "review_now", "interesting"),
        "suspect_in_ignore_for_now": _count_matching_label(records, "ignore_for_now", "suspect"),
        "unlabeled_in_review_now": _count_unlabeled(records, "review_now"),
    }


def class_quality_context(records: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, int]]]:
    return {
        "candidate_class_by_quality_band": _cross_tab(
            records,
            value_getter=lambda record: _read_string(record.get("quality_band")) or "unknown",
        ),
        "candidate_class_by_has_blocking_flags": _cross_tab(
            records,
            value_getter=lambda record: _bool_key(record.get("has_blocking_flags")),
        ),
        "candidate_class_by_has_migrated": _cross_tab(
            records,
            value_getter=lambda record: _bool_key(record.get("has_migrated")),
        ),
    }


def queue_sizes(
    review_now_records: list[dict[str, Any]],
    review_if_time_records: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "review_queue_now_count": len(review_now_records),
        "review_queue_if_time_count": len(review_if_time_records),
    }


def queue_usefulness_notes(
    records: list[dict[str, Any]],
    review_now_records: list[dict[str, Any]],
    review_if_time_records: list[dict[str, Any]],
) -> list[str]:
    notes: list[str] = []
    total_records = len(records)
    labeled_record_count = sum(1 for record in records if _read_string(record.get("label")))
    ignored_record_count = _count_by_candidate_class(records, "ignore_for_now")

    if not review_now_records:
        notes.append("review_now_queue_is_empty")
    if len(review_now_records) > 20:
        notes.append("review_now_queue_is_large")
    if review_if_time_records and len(review_if_time_records) > (total_records / 2):
        notes.append("review_if_time_dominates")
    if labeled_record_count == 0:
        notes.append("no_labels_present")
    if total_records > 0 and ignored_record_count == total_records:
        notes.append("all_records_ignored")

    return notes


def _count_by_candidate_class(records: list[dict[str, Any]], candidate_class: str) -> int:
    return sum(
        1 for record in records if _read_string(record.get("candidate_class")) == candidate_class
    )


def _count_labels_within_class(
    records: list[dict[str, Any]],
    candidate_class: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        if _read_string(record.get("candidate_class")) != candidate_class:
            continue
        label = _read_string(record.get("label"))
        if label is None:
            continue
        counts[label] = counts.get(label, 0) + 1
    return {label: counts[label] for label in sorted(counts)}


def _count_matching_label(
    records: list[dict[str, Any]],
    candidate_class: str,
    label: str,
) -> int:
    return sum(
        1
        for record in records
        if _read_string(record.get("candidate_class")) == candidate_class
        and _read_string(record.get("label")) == label
    )


def _count_unlabeled(records: list[dict[str, Any]], candidate_class: str) -> int:
    return sum(
        1
        for record in records
        if _read_string(record.get("candidate_class")) == candidate_class
        and _read_string(record.get("label")) is None
    )


def _cross_tab(
    records: list[dict[str, Any]],
    *,
    value_getter,
) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {
        candidate_class: {} for candidate_class in CANDIDATE_CLASSES
    }
    for record in records:
        candidate_class = _read_string(record.get("candidate_class"))
        if candidate_class not in table:
            continue
        value = value_getter(record)
        table[candidate_class][value] = table[candidate_class].get(value, 0) + 1

    return {
        candidate_class: {
            value: table[candidate_class][value] for value in sorted(table[candidate_class])
        }
        for candidate_class in CANDIDATE_CLASSES
    }


def _percentage(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((count / total) * 100, 2)


def _bool_key(value: Any) -> str:
    return "true" if bool(value) else "false"


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
