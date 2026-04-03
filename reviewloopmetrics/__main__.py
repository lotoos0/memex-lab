from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CANDIDATES_PATH = Path("data/review_candidates_v2.jsonl")
OUTCOMES_PATH = Path("data/review_outcomes.jsonl")
OUTPUT_PATH = Path("data/reports/review_loop_metrics.json")

KNOWN_CANDIDATE_CLASSES = ("review_now", "review_if_time", "ignore_for_now")
KNOWN_OUTCOMES = ("useful", "noise", "needs_more_context")


def main() -> None:
    args = _build_parser().parse_args()
    candidates_path = Path(args.candidates_path)
    outcomes_path = Path(args.outcomes_path)
    output_path = Path(args.output_path)

    if not candidates_path.exists():
        raise SystemExit(f"Review loop metrics candidates file not found: {candidates_path}")

    candidate_records = read_jsonl(candidates_path)
    candidate_map = build_candidate_map(candidate_records)
    outcome_records = load_outcomes(outcomes_path)

    report_document = build_report_document(
        candidate_records=candidate_records,
        candidate_map=candidate_map,
        outcome_records=outcome_records,
        candidates_path=candidates_path,
        outcomes_path=outcomes_path,
    )
    write_json(output_path, report_document)
    print_summary(report_document, output_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build aggregate review loop metrics from existing review artifacts.",
    )
    parser.add_argument(
        "--candidates-path",
        default=str(CANDIDATES_PATH),
        help="Review candidates v2 JSONL input path.",
    )
    parser.add_argument(
        "--outcomes-path",
        default=str(OUTCOMES_PATH),
        help="Optional review outcomes JSONL input path.",
    )
    parser.add_argument(
        "--output-path",
        default=str(OUTPUT_PATH),
        help="Review loop metrics JSON output path.",
    )
    return parser


def build_report_document(
    *,
    candidate_records: list[dict[str, Any]],
    candidate_map: dict[str, dict[str, Any]],
    outcome_records: list[dict[str, Any]],
    candidates_path: Path,
    outcomes_path: Path,
) -> dict[str, Any]:
    candidate_funnel = build_candidate_funnel(candidate_records)
    review_coverage = build_review_coverage(
        candidate_map=candidate_map,
        outcome_records=outcome_records,
        candidate_funnel=candidate_funnel,
    )
    outcome_distribution = build_outcome_distribution(outcome_records)
    outcome_by_candidate_class = build_outcome_by_candidate_class(
        candidate_map=candidate_map,
        outcome_records=outcome_records,
    )
    label_interaction_summary = build_label_interaction_summary(
        candidate_map=candidate_map,
        outcome_records=outcome_records,
    )
    total_reviewed_records = review_coverage["total_reviewed_records"]

    return {
        "report_version": "v0",
        "candidates_input_path": str(candidates_path),
        "outcomes_input_path": str(outcomes_path),
        "candidate_funnel": candidate_funnel,
        "review_coverage": review_coverage,
        "outcome_distribution": outcome_distribution,
        "outcome_by_candidate_class": outcome_by_candidate_class,
        "label_interaction_summary": label_interaction_summary,
        "sample_size_note": build_sample_size_note(total_reviewed_records),
    }


def build_candidate_funnel(candidate_records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_candidate_records": len(candidate_records),
        "total_review_now": count_candidate_class(candidate_records, "review_now"),
        "total_review_if_time": count_candidate_class(candidate_records, "review_if_time"),
        "total_ignore_for_now": count_candidate_class(candidate_records, "ignore_for_now"),
    }


def build_review_coverage(
    *,
    candidate_map: dict[str, dict[str, Any]],
    outcome_records: list[dict[str, Any]],
    candidate_funnel: dict[str, int],
) -> dict[str, int | float | None]:
    reviewed_mints = {mint for mint in (read_string(record.get("mint")) for record in outcome_records) if mint}
    reviewed_review_now = 0
    reviewed_review_if_time = 0

    for mint in reviewed_mints:
        candidate_record = candidate_map.get(mint)
        if candidate_record is None:
            continue
        candidate_class = read_string(candidate_record.get("candidate_class"))
        if candidate_class == "review_now":
            reviewed_review_now += 1
        elif candidate_class == "review_if_time":
            reviewed_review_if_time += 1

    total_reviewed_records = len(outcome_records)
    return {
        "total_reviewed_records": total_reviewed_records,
        "reviewed_share_of_all_candidates": nullable_rate(
            total_reviewed_records,
            candidate_funnel["total_candidate_records"],
        ),
        "reviewed_share_of_review_now_candidates": nullable_rate(
            reviewed_review_now,
            candidate_funnel["total_review_now"],
        ),
        "reviewed_share_of_review_if_time_candidates": nullable_rate(
            reviewed_review_if_time,
            candidate_funnel["total_review_if_time"],
        ),
    }


def build_outcome_distribution(
    outcome_records: list[dict[str, Any]],
) -> dict[str, int | float | None]:
    useful_count = count_outcome(outcome_records, "useful")
    noise_count = count_outcome(outcome_records, "noise")
    needs_more_context_count = count_outcome(outcome_records, "needs_more_context")
    total_reviewed_records = len(outcome_records)
    return {
        "useful_count": useful_count,
        "noise_count": noise_count,
        "needs_more_context_count": needs_more_context_count,
        "useful_rate": nullable_rate(useful_count, total_reviewed_records),
        "noise_rate": nullable_rate(noise_count, total_reviewed_records),
    }


def build_outcome_by_candidate_class(
    *,
    candidate_map: dict[str, dict[str, Any]],
    outcome_records: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    table = {
        candidate_class: {outcome: 0 for outcome in KNOWN_OUTCOMES}
        for candidate_class in KNOWN_CANDIDATE_CLASSES
    }

    for outcome_record in outcome_records:
        mint = read_string(outcome_record.get("mint"))
        outcome = read_string(outcome_record.get("outcome"))
        candidate_class = resolve_candidate_class(
            candidate_map.get(mint) if mint else None,
            outcome_record,
        )
        if candidate_class in table and outcome in table[candidate_class]:
            table[candidate_class][outcome] += 1

    return table


def build_label_interaction_summary(
    *,
    candidate_map: dict[str, dict[str, Any]],
    outcome_records: list[dict[str, Any]],
) -> dict[str, Any]:
    reviewed_labeled_count = 0
    reviewed_unlabeled_count = 0
    outcomes_by_label: dict[str, dict[str, int]] = {}

    for outcome_record in outcome_records:
        mint = read_string(outcome_record.get("mint"))
        outcome = read_string(outcome_record.get("outcome"))
        if outcome not in KNOWN_OUTCOMES:
            continue

        label = None
        if mint:
            candidate_record = candidate_map.get(mint)
            if candidate_record is not None:
                label = read_string(candidate_record.get("label"))

        if label is None:
            reviewed_unlabeled_count += 1
            continue

        reviewed_labeled_count += 1
        outcomes_by_label.setdefault(
            label,
            {known_outcome: 0 for known_outcome in KNOWN_OUTCOMES},
        )[outcome] += 1

    return {
        "reviewed_labeled_count": reviewed_labeled_count,
        "reviewed_unlabeled_count": reviewed_unlabeled_count,
        "reviewed_outcomes_by_label": {
            label: outcomes_by_label[label] for label in sorted(outcomes_by_label)
        },
    }


def build_sample_size_note(total_reviewed_records: int) -> str:
    if total_reviewed_records < 10:
        return "low"
    if total_reviewed_records < 30:
        return "moderate"
    return "sufficient"


def build_candidate_map(
    candidate_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    candidate_map: dict[str, dict[str, Any]] = {}
    for record in candidate_records:
        mint = read_string(record.get("mint"))
        if mint is not None:
            candidate_map[mint] = record
    return candidate_map


def load_outcomes(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    indexed_outcomes: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(path):
        mint = read_string(record.get("mint"))
        candidate_class = read_string(record.get("candidate_class"))
        outcome = read_string(record.get("outcome"))
        reviewed_at = read_string(record.get("reviewed_at"))
        if mint and candidate_class and outcome in KNOWN_OUTCOMES and reviewed_at:
            indexed_outcomes[mint] = {
                "mint": mint,
                "candidate_class": candidate_class,
                "outcome": outcome,
                "reviewed_at": reviewed_at,
            }

    return [indexed_outcomes[mint] for mint in sorted(indexed_outcomes)]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(
                    f"Invalid JSON in {path} at line {line_number}: {exc}"
                ) from exc
            if not isinstance(record, dict):
                raise SystemExit(
                    f"Expected a JSON object in {path} at line {line_number}, got {type(record).__name__}."
                )
            records.append(record)
    return records


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def print_summary(report_document: dict[str, Any], output_path: Path) -> None:
    candidate_funnel = report_document["candidate_funnel"]
    review_coverage = report_document["review_coverage"]
    outcome_distribution = report_document["outcome_distribution"]

    print(f"Review loop metrics written to {output_path}")
    print(
        "candidates={total_candidate_records} review_now={total_review_now} review_if_time={total_review_if_time} ignore_for_now={total_ignore_for_now}".format(
            **candidate_funnel
        )
    )
    print(
        "reviewed={total_reviewed_records} useful={useful_count} noise={noise_count} needs_more_context={needs_more_context_count}".format(
            total_reviewed_records=review_coverage["total_reviewed_records"],
            useful_count=outcome_distribution["useful_count"],
            noise_count=outcome_distribution["noise_count"],
            needs_more_context_count=outcome_distribution["needs_more_context_count"],
        )
    )
    print(
        "useful_rate={useful_rate} sample_size_note={sample_size_note}".format(
            useful_rate=outcome_distribution["useful_rate"],
            sample_size_note=report_document["sample_size_note"],
        )
    )


def count_candidate_class(candidate_records: list[dict[str, Any]], target: str) -> int:
    return sum(
        1 for record in candidate_records if read_string(record.get("candidate_class")) == target
    )


def count_outcome(outcome_records: list[dict[str, Any]], target: str) -> int:
    return sum(1 for record in outcome_records if read_string(record.get("outcome")) == target)


def resolve_candidate_class(
    candidate_record: dict[str, Any] | None,
    outcome_record: dict[str, Any],
) -> str | None:
    if candidate_record is not None:
        candidate_class = read_string(candidate_record.get("candidate_class"))
        if candidate_class is not None:
            return candidate_class
    return read_string(outcome_record.get("candidate_class"))


def nullable_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


if __name__ == "__main__":
    main()
