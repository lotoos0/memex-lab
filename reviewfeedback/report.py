from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from reviewfeedback.config import (
    ALLOWED_OUTCOMES,
    KNOWN_CANDIDATE_CLASSES,
    KNOWN_LABELS,
    ReviewFeedbackConfig,
)
from reviewfeedback.io import read_jsonl, write_json


def main() -> None:
    args = _build_parser().parse_args()
    config = _build_config(args)

    candidate_map = _build_candidate_map(_load_candidate_records(config.candidates_path))
    label_fallback_map = _build_label_fallback_map(Path(args.labels_path))
    outcome_records = _load_outcomes(config.outcomes_path)

    report_document = _build_report_document(
        config=config,
        candidate_map=candidate_map,
        label_fallback_map=label_fallback_map,
        outcome_records=outcome_records,
    )
    write_json(config.report_output_path, report_document)
    _print_summary(report_document, config.report_output_path)


def _build_parser() -> argparse.ArgumentParser:
    config = ReviewFeedbackConfig()
    parser = argparse.ArgumentParser(
        description="Build a descriptive feedback report from recorded review outcomes.",
    )
    parser.add_argument(
        "--candidates-path",
        default=str(config.candidates_path),
        help="Review candidates JSONL input path.",
    )
    parser.add_argument(
        "--outcomes-path",
        default=str(config.outcomes_path),
        help="Review outcomes JSONL input path.",
    )
    parser.add_argument(
        "--labels-path",
        default="data/labels/review_labels.jsonl",
        help="Optional labels JSONL input path used only as a fallback by mint.",
    )
    parser.add_argument(
        "--output-path",
        default=str(config.report_output_path),
        help="Review feedback report JSON output path.",
    )
    return parser


def _build_config(args: argparse.Namespace) -> ReviewFeedbackConfig:
    return ReviewFeedbackConfig(
        candidates_path=Path(args.candidates_path),
        outcomes_path=Path(args.outcomes_path),
        report_output_path=Path(args.output_path),
    )


def _build_report_document(
    *,
    config: ReviewFeedbackConfig,
    candidate_map: dict[str, dict[str, Any]],
    label_fallback_map: dict[str, str],
    outcome_records: list[dict[str, Any]],
) -> dict[str, Any]:
    class_outcome = _empty_candidate_class_outcome_table()
    reviewed_label_table: dict[str, dict[str, int]] = {}
    total_useful = 0
    total_noise = 0
    total_needs_more_context = 0
    unlabeled_reviewed_count = 0

    for outcome_record in outcome_records:
        mint = _read_string(outcome_record.get("mint"))
        candidate_class = _read_string(outcome_record.get("candidate_class"))
        outcome = _read_string(outcome_record.get("outcome"))
        if mint is None or candidate_class is None or outcome is None:
            continue

        if candidate_class in class_outcome and outcome in class_outcome[candidate_class]:
            class_outcome[candidate_class][outcome] += 1

        if outcome == "useful":
            total_useful += 1
        elif outcome == "noise":
            total_noise += 1
        elif outcome == "needs_more_context":
            total_needs_more_context += 1

        label = _candidate_label(candidate_map.get(mint), label_fallback_map.get(mint))
        if label is None:
            unlabeled_reviewed_count += 1
        elif label in KNOWN_LABELS:
            reviewed_label_table.setdefault(label, _empty_outcome_counts())[outcome] += 1

    review_now_total = sum(class_outcome["review_now"].values())
    review_if_time_total = sum(class_outcome["review_if_time"].values())

    return {
        "report_version": config.report_version,
        "candidates_input_path": str(config.candidates_path),
        "outcomes_input_path": str(config.outcomes_path),
        "totals": {
            "total_reviewed_records": len(outcome_records),
            "total_useful": total_useful,
            "total_noise": total_noise,
            "total_needs_more_context": total_needs_more_context,
        },
        "candidate_class_by_outcome": class_outcome,
        "label_by_outcome": {
            label: reviewed_label_table[label] for label in KNOWN_LABELS if label in reviewed_label_table
        },
        "effectiveness_indicators": {
            "useful_rate_in_review_now": _nullable_rate(
                class_outcome["review_now"]["useful"],
                review_now_total,
            ),
            "noise_rate_in_review_if_time": _nullable_rate(
                class_outcome["review_if_time"]["noise"],
                review_if_time_total,
            ),
            "unlabeled_reviewed_count": unlabeled_reviewed_count,
        },
    }


def _print_summary(report_document: dict[str, Any], output_path: Path) -> None:
    totals = report_document["totals"]
    indicators = report_document["effectiveness_indicators"]

    print(f"Review feedback report written to {output_path}")
    print(
        "reviewed={total_reviewed_records} useful={total_useful} noise={total_noise} needs_more_context={total_needs_more_context}".format(
            **totals
        )
    )
    print(
        "rates useful_in_review_now={useful_rate_in_review_now} noise_in_review_if_time={noise_rate_in_review_if_time} unlabeled_reviewed={unlabeled_reviewed_count}".format(
            **indicators
        )
    )


def _build_candidate_map(candidate_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    candidate_map: dict[str, dict[str, Any]] = {}
    for record in candidate_records:
        mint = _read_string(record.get("mint"))
        if mint is not None:
            candidate_map[mint] = record
    return candidate_map


def _load_candidate_records(path: Path) -> list[dict[str, Any]]:
    # The report can run without the selector output. When the candidates file is
    # absent, we fall back to stored outcomes plus optional labels by mint.
    return read_jsonl(path)


def _build_label_fallback_map(path: Path) -> dict[str, str]:
    label_map: dict[str, str] = {}
    for record in read_jsonl(path):
        mint = _read_string(record.get("mint"))
        label = _read_string(record.get("label"))
        if mint is not None and label is not None:
            label_map[mint] = label
    return label_map


def _load_outcomes(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    indexed_outcomes: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(path):
        mint = _read_string(record.get("mint"))
        candidate_class = _read_string(record.get("candidate_class"))
        outcome = _read_string(record.get("outcome"))
        reviewed_at = _read_string(record.get("reviewed_at"))
        if mint and candidate_class and outcome in ALLOWED_OUTCOMES and reviewed_at:
            indexed_outcomes[mint] = {
                "mint": mint,
                "candidate_class": candidate_class,
                "outcome": outcome,
                "note": _read_string(record.get("note")),
                "reviewed_at": reviewed_at,
            }
    return [indexed_outcomes[mint] for mint in sorted(indexed_outcomes)]


def _empty_candidate_class_outcome_table() -> dict[str, dict[str, int]]:
    return {
        candidate_class: _empty_outcome_counts() for candidate_class in KNOWN_CANDIDATE_CLASSES
    }


def _empty_outcome_counts() -> dict[str, int]:
    return {outcome: 0 for outcome in ALLOWED_OUTCOMES}


def _candidate_label(candidate_record: dict[str, Any] | None, fallback_label: str | None) -> str | None:
    if candidate_record is not None:
        label = _read_string(candidate_record.get("label"))
        if label is not None:
            return label
    return fallback_label


def _nullable_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


if __name__ == "__main__":
    main()
