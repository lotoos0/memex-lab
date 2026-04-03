from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

SOURCE_PATHS = {
    "queue-now": Path("data/review_queue_now_v2.jsonl"),
    "queue-if-time": Path("data/review_queue_if_time_v2.jsonl"),
    "candidates": Path("data/review_candidates_v2.jsonl"),
}

LIST_FIELDS = ("candidate_reasons", "score_flags")
EXPORT_FIELDS = (
    "review_source",
    "mint",
    "candidate_class",
    "quality_band",
    "score_version",
    "score_total",
    "has_migrated",
    "has_blocking_flags",
    "token_standard",
    "creator",
    "migration_target",
    "created_at",
    "migrated_at",
    "label",
    "label_note",
    "candidate_reasons",
    "score_flags",
)


def main() -> None:
    args = _build_parser().parse_args()
    _validate_args(args)

    input_path = SOURCE_PATHS[args.source]
    if not input_path.exists():
        raise SystemExit(f"Review export source file not found: {input_path}")

    output_path = Path(
        args.output_path
        or _default_output_path(
            source=args.source,
            export_format=args.format,
            candidate_class=args.candidate_class,
        )
    )

    records = read_jsonl(input_path)
    compact_records = build_export_records(
        source=args.source,
        records=records,
        candidate_class=args.candidate_class,
    )

    if args.format == "csv":
        write_csv(output_path, compact_records)
    else:
        write_jsonl(output_path, compact_records)

    print(f"Review export written to {output_path}")
    print(
        "source={source} format={format} records={records}".format(
            source=args.source,
            format=args.format,
            records=len(compact_records),
        )
    )
    if args.candidate_class:
        print(f"candidate_class={args.candidate_class}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export compact review-ready records from existing v2 queue or candidate files.",
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=tuple(SOURCE_PATHS),
        help="Source to export from.",
    )
    parser.add_argument(
        "--format",
        choices=("jsonl", "csv"),
        default="jsonl",
        help="Output format. JSONL is the primary format.",
    )
    parser.add_argument(
        "--candidate-class",
        choices=("review_now", "review_if_time", "ignore_for_now"),
        help="Optional candidate class filter, supported only for --source candidates.",
    )
    parser.add_argument(
        "--output-path",
        help="Optional output path. Defaults to data/exports/review_<source>[...].<ext>.",
    )
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    if args.candidate_class and args.source != "candidates":
        raise SystemExit(
            "--candidate-class is supported only when --source candidates is used."
        )


def _default_output_path(
    *,
    source: str,
    export_format: str,
    candidate_class: str | None,
) -> Path:
    source_suffix = source.replace("-", "_")
    class_suffix = f"_{candidate_class}" if candidate_class else ""
    extension = "csv" if export_format == "csv" else "jsonl"
    return Path(f"data/exports/review_{source_suffix}{class_suffix}.{extension}")


def build_export_records(
    *,
    source: str,
    records: list[dict[str, Any]],
    candidate_class: str | None,
) -> list[dict[str, Any]]:
    compact_records: list[dict[str, Any]] = []

    for record in records:
        if candidate_class and record.get("candidate_class") != candidate_class:
            continue
        compact_records.append(build_compact_record(source=source, record=record))

    compact_records.sort(key=lambda record: str(record["mint"]))
    return compact_records


def build_compact_record(*, source: str, record: dict[str, Any]) -> dict[str, Any]:
    compact_record = {
        "review_source": source,
        "mint": read_string(record.get("mint")),
        "candidate_class": read_string(record.get("candidate_class")),
        "quality_band": read_string(record.get("quality_band")),
        "score_version": read_string(record.get("score_version")),
        "score_total": record.get("score_total"),
        "has_migrated": record.get("has_migrated"),
        "has_blocking_flags": record.get("has_blocking_flags"),
        "token_standard": read_string(record.get("token_standard")),
        "creator": read_string(record.get("creator")),
        "migration_target": read_string(record.get("migration_target")),
        "created_at": read_string(record.get("created_at")),
        "migrated_at": read_string(record.get("migrated_at")),
        "label": read_string(record.get("label")),
        "label_note": read_string(record.get("label_note")),
        "candidate_reasons": read_string_list(record.get("candidate_reasons")),
        "score_flags": read_string_list(record.get("score_flags")),
    }
    return {field: compact_record[field] for field in EXPORT_FIELDS}


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
                raise SystemExit(f"Invalid JSON in {path} at line {line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise SystemExit(
                    f"Expected a JSON object in {path} at line {line_number}, got {type(record).__name__}."
                )
            records.append(record)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(EXPORT_FIELDS))
        writer.writeheader()
        for record in records:
            writer.writerow(serialize_csv_record(record))


def serialize_csv_record(record: dict[str, Any]) -> dict[str, str]:
    csv_record: dict[str, str] = {}
    for field in EXPORT_FIELDS:
        value = record.get(field)
        if field in LIST_FIELDS:
            csv_record[field] = "|".join(value) if isinstance(value, list) else ""
        elif value is None:
            csv_record[field] = ""
        else:
            csv_record[field] = str(value)
    return csv_record


def read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def read_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


if __name__ == "__main__":
    main()
