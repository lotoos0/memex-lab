from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from reviewkit.config import ALLOWED_LABELS, ReviewkitPaths
from reviewkit.io import read_jsonl, write_jsonl_overwrite


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = _build_parser()
    args = parser.parse_args()

    if not _has_at_least_one_filter(args):
        parser.error("At least one explicit filter is required.")

    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    labels_path = Path(args.labels_path)
    label_map = _load_label_map(labels_path) if args.label else {}

    records = read_jsonl(input_path)
    exported_records = [
        record
        for record in records
        if _matches_filters(
            record=record,
            quality_band=args.quality_band,
            has_migrated=_parse_optional_bool(args.has_migrated),
            has_blocking_flags=_parse_optional_bool(args.has_blocking_flags),
            label=args.label,
            min_score=args.min_score,
            label_map=label_map,
        )
    ]
    if args.limit is not None:
        exported_records = exported_records[: args.limit]

    write_jsonl_overwrite(output_path, exported_records)

    logging.getLogger(__name__).info(
        "Exported %s records from %s to %s with filters quality_band=%s has_migrated=%s has_blocking_flags=%s label=%s min_score=%s limit=%s",
        len(exported_records),
        input_path,
        output_path,
        args.quality_band,
        args.has_migrated,
        args.has_blocking_flags,
        args.label,
        args.min_score,
        args.limit,
    )


def _build_parser() -> argparse.ArgumentParser:
    paths = ReviewkitPaths()
    parser = argparse.ArgumentParser(
        description="Export a deterministic JSONL subset of filtered snapshots.",
    )
    parser.add_argument(
        "--input-path",
        default=str(paths.filtered_snapshots_path),
        help="Filtered snapshots JSONL input path.",
    )
    parser.add_argument(
        "--labels-path",
        default=str(paths.labels_path),
        help="Labels JSONL input path used only when --label is set.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="JSONL output path for the exported subset.",
    )
    parser.add_argument(
        "--quality-band",
        choices=("weak", "partial", "strong"),
        help="Filter by quality_band.",
    )
    parser.add_argument(
        "--has-migrated",
        choices=("true", "false"),
        help="Filter by has_migrated.",
    )
    parser.add_argument(
        "--has-blocking-flags",
        choices=("true", "false"),
        help="Filter by has_blocking_flags.",
    )
    parser.add_argument(
        "--label",
        choices=ALLOWED_LABELS,
        help="Filter by stored manual label.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        help="Filter by score_total >= N.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the exported records after applying all active filters.",
    )
    return parser


def _has_at_least_one_filter(args: argparse.Namespace) -> bool:
    return any(
        [
            args.quality_band,
            args.has_migrated is not None,
            args.has_blocking_flags is not None,
            args.label,
            args.min_score is not None,
            args.limit is not None,
        ]
    )


def _load_label_map(path: Path) -> dict[str, str]:
    label_map: dict[str, str] = {}
    for record in read_jsonl(path):
        mint = _read_string(record.get("mint"))
        label = _read_string(record.get("label"))
        if mint and label in ALLOWED_LABELS:
            label_map[mint] = label
    return label_map


def _matches_filters(
    *,
    record: dict[str, Any],
    quality_band: str | None,
    has_migrated: bool | None,
    has_blocking_flags: bool | None,
    label: str | None,
    min_score: int | None,
    label_map: dict[str, str],
) -> bool:
    if quality_band is not None and record.get("quality_band") != quality_band:
        return False

    if has_migrated is not None and bool(record.get("has_migrated")) != has_migrated:
        return False

    if (
        has_blocking_flags is not None
        and bool(record.get("has_blocking_flags")) != has_blocking_flags
    ):
        return False

    if label is not None:
        mint = _read_string(record.get("mint")) or ""
        if label_map.get(mint) != label:
            return False

    if min_score is not None and _read_int(record.get("score_total")) < min_score:
        return False

    return True


def _parse_optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value == "true"


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _read_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0


if __name__ == "__main__":
    main()
