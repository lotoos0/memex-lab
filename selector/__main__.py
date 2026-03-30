from __future__ import annotations

import argparse
from pathlib import Path

from selector.config import SelectorConfig
from selector.io import read_jsonl, write_jsonl_overwrite
from selector.rules import build_candidate_record, build_label_map, sort_key


def main() -> None:
    config = _build_config(_build_parser().parse_args())
    filtered_records = read_jsonl(config.input_path)

    if not config.input_path.exists():
        raise SystemExit(f"Primary input file not found: {config.input_path}")
    if not filtered_records:
        raise SystemExit(
            f"Primary input file is empty or contains no valid records: {config.input_path}"
        )

    label_map = build_label_map(read_jsonl(config.labels_path))
    label_influenced_count = 0
    candidate_records: list[dict[str, object]] = []

    for filtered_record in filtered_records:
        mint = filtered_record.get("mint")
        label_record = label_map.get(mint) if isinstance(mint, str) else None
        candidate_record, label_influenced = build_candidate_record(
            filtered_record,
            label_record=label_record,
            selection_version=config.selection_version,
        )
        candidate_records.append(candidate_record)
        if label_influenced:
            label_influenced_count += 1

    candidate_records.sort(key=sort_key)
    write_jsonl_overwrite(config.output_path, candidate_records)
    _print_summary(candidate_records, label_influenced_count, config.output_path)


def _build_parser() -> argparse.ArgumentParser:
    config = SelectorConfig()
    parser = argparse.ArgumentParser(
        description="Build offline review candidates from filtered v1 snapshots.",
    )
    parser.add_argument(
        "--input-path",
        default=str(config.input_path),
        help="Filtered snapshots v1 JSONL input path.",
    )
    parser.add_argument(
        "--labels-path",
        default=str(config.labels_path),
        help="Optional review labels JSONL input path.",
    )
    parser.add_argument(
        "--output-path",
        default=str(config.output_path),
        help="Review candidates JSONL output path.",
    )
    return parser


def _build_config(args: argparse.Namespace) -> SelectorConfig:
    return SelectorConfig(
        input_path=Path(args.input_path),
        labels_path=Path(args.labels_path),
        output_path=Path(args.output_path),
    )


def _print_summary(
    candidate_records: list[dict[str, object]],
    label_influenced_count: int,
    output_path: Path,
) -> None:
    review_now_count = sum(
        1 for record in candidate_records if record.get("candidate_class") == "review_now"
    )
    review_if_time_count = sum(
        1
        for record in candidate_records
        if record.get("candidate_class") == "review_if_time"
    )
    ignore_for_now_count = sum(
        1
        for record in candidate_records
        if record.get("candidate_class") == "ignore_for_now"
    )

    print(f"Candidates written to {output_path}")
    print(
        "records={records} review_now={review_now} review_if_time={review_if_time} ignore_for_now={ignore_for_now}".format(
            records=len(candidate_records),
            review_now=review_now_count,
            review_if_time=review_if_time_count,
            ignore_for_now=ignore_for_now_count,
        )
    )
    print(f"label_influenced={label_influenced_count}")


if __name__ == "__main__":
    main()
