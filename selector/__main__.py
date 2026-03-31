from __future__ import annotations

import argparse
from pathlib import Path

from selector.config import SelectorConfig
from selector.compare import (
    build_comparison_report,
    print_summary as print_comparison_summary,
    write_json,
)
from selector.io import read_jsonl, write_jsonl_overwrite
from selector.rules import build_candidate_record, build_label_map, sort_key
from selector.rules_v2 import (
    build_candidate_record as build_candidate_record_v2,
    sort_key as sort_key_v2,
)


def main() -> None:
    config = SelectorConfig()
    parser = argparse.ArgumentParser(
        description="Build selector v1/v2 outputs or compare them.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("select", "compare"),
        default="select",
        help="Choose selection or comparison mode.",
    )
    parser.add_argument(
        "--selection-version",
        choices=("v1", "v2"),
        default="v1",
        help="Selection rules version to run in select mode.",
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
        default=None,
        help="Review candidates JSONL output path for select mode.",
    )
    parser.add_argument(
        "--v1-input-path",
        default=str(config.output_path_for("v1")),
        help="Selector v1 JSONL input path for compare mode.",
    )
    parser.add_argument(
        "--v2-input-path",
        default=str(config.output_path_for("v2")),
        help="Selector v2 JSONL input path for compare mode.",
    )
    parser.add_argument(
        "--compare-output-path",
        default=str(config.comparison_output_path),
        help="Comparison JSON output path for compare mode.",
    )
    args = parser.parse_args()

    if args.command == "compare":
        v1_input_path = Path(args.v1_input_path)
        v2_input_path = Path(args.v2_input_path)
        compare_output_path = Path(args.compare_output_path)
        comparison_report = build_comparison_report(
            v1_records=read_jsonl(v1_input_path),
            v2_records=read_jsonl(v2_input_path),
            v1_input_path=v1_input_path,
            v2_input_path=v2_input_path,
        )
        write_json(compare_output_path, comparison_report)
        print_comparison_summary(comparison_report, compare_output_path)
        return

    run_selection(
        config=_build_config(args, config),
        selector_version=args.selection_version,
    )


def run_selection(*, config: SelectorConfig, selector_version: str) -> None:
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
    build_record = build_candidate_record_v2 if selector_version == "v2" else build_candidate_record
    candidate_sort_key = sort_key_v2 if selector_version == "v2" else sort_key
    output_path = config.output_path_for(selector_version)
    selection_marker = config.selection_marker_for(selector_version)

    for filtered_record in filtered_records:
        mint = filtered_record.get("mint")
        label_record = label_map.get(mint) if isinstance(mint, str) else None
        candidate_record, label_influenced = build_record(
            filtered_record,
            label_record=label_record,
            selection_version=selection_marker,
        )
        candidate_records.append(candidate_record)
        if label_influenced:
            label_influenced_count += 1

    candidate_records.sort(key=candidate_sort_key)
    write_jsonl_overwrite(output_path, candidate_records)
    _print_summary(candidate_records, label_influenced_count, output_path)


def _build_config(args: argparse.Namespace, config: SelectorConfig) -> SelectorConfig:
    output_path = config.output_path
    output_path_v2 = config.output_path_v2
    if args.output_path:
        if args.selection_version == "v2":
            output_path_v2 = Path(args.output_path)
        else:
            output_path = Path(args.output_path)

    return SelectorConfig(
        input_path=Path(args.input_path),
        labels_path=Path(args.labels_path),
        output_path=output_path,
        output_path_v2=output_path_v2,
        comparison_output_path=config.comparison_output_path,
        selection_version=config.selection_version,
        selection_version_v2=config.selection_version_v2,
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
