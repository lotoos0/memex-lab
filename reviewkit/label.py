from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
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
    _validate_args(parser, args)

    labels_path = Path(args.labels_path)

    if args.list:
        _list_labels(labels_path)
        return

    if args.remove:
        _remove_label(labels_path, args.remove)
        return

    input_path = Path(args.input_path)
    _validate_mint_exists(input_path, args.mint)
    _set_label(labels_path, args.mint, args.label, args.note)


def _build_parser() -> argparse.ArgumentParser:
    paths = ReviewkitPaths()
    parser = argparse.ArgumentParser(
        description="Manage separate JSONL labels for filtered snapshots.",
    )
    parser.add_argument(
        "--input-path",
        default=str(paths.filtered_snapshots_path),
        help="Filtered snapshots JSONL input path used for mint validation on label set.",
    )
    parser.add_argument(
        "--labels-path",
        default=str(paths.labels_path),
        help="Labels JSONL path.",
    )
    parser.add_argument(
        "--mint",
        help="Mint to label when used with --label.",
    )
    parser.add_argument(
        "--label",
        choices=ALLOWED_LABELS,
        help="Label value to set for --mint.",
    )
    parser.add_argument(
        "--note",
        help="Optional note stored alongside the label when setting a label.",
    )
    parser.add_argument(
        "--remove",
        metavar="MINT",
        help="Remove the stored label for a mint.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print stored labels as JSONL to stdout.",
    )
    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    is_set_mode = bool(args.mint or args.label)
    selected_modes = sum(
        [
            int(args.list),
            int(bool(args.remove)),
            int(is_set_mode),
        ]
    )

    if selected_modes != 1:
        parser.error("Choose exactly one label action: set, --remove, or --list.")

    if is_set_mode and (not args.mint or not args.label):
        parser.error("--mint and --label are required when setting a label.")


def _list_labels(labels_path: Path) -> None:
    label_records = sorted(
        _load_label_records(labels_path),
        key=lambda record: record["mint"],
    )
    for record in label_records:
        print(json.dumps(record, ensure_ascii=False))


def _remove_label(labels_path: Path, mint: str) -> None:
    label_records = {
        record["mint"]: record for record in _load_label_records(labels_path)
    }
    removed = label_records.pop(mint, None) is not None
    if removed or label_records or labels_path.exists():
        write_jsonl_overwrite(
            labels_path,
            [label_records[key] for key in sorted(label_records)],
        )
    logging.getLogger(__name__).info(
        "Removed label for mint=%s removed=%s labels_path=%s",
        mint,
        removed,
        labels_path,
    )


def _set_label(
    labels_path: Path,
    mint: str,
    label: str,
    note: str | None,
) -> None:
    label_records = {
        record["mint"]: record for record in _load_label_records(labels_path)
    }
    label_record = {
        "mint": mint,
        "label": label,
        "labeled_at": datetime.now(timezone.utc).isoformat(),
    }
    if note:
        label_record["note"] = note
    label_records[mint] = label_record
    write_jsonl_overwrite(
        labels_path,
        [label_records[key] for key in sorted(label_records)],
    )
    logging.getLogger(__name__).info(
        "Stored label mint=%s label=%s note_present=%s labels_path=%s",
        mint,
        label,
        bool(note),
        labels_path,
    )


def _validate_mint_exists(input_path: Path, mint: str) -> None:
    records = read_jsonl(input_path)
    if any(_read_string(record.get("mint")) == mint for record in records):
        return
    raise SystemExit(
        f"Mint not found in filtered snapshots input: mint={mint} input_path={input_path}"
    )


def _load_label_records(labels_path: Path) -> list[dict[str, str]]:
    label_records: list[dict[str, str]] = []
    for record in read_jsonl(labels_path):
        mint = _read_string(record.get("mint"))
        label = _read_string(record.get("label"))
        labeled_at = _read_string(record.get("labeled_at"))
        if mint and label in ALLOWED_LABELS and labeled_at:
            label_record = {
                "mint": mint,
                "label": label,
                "labeled_at": labeled_at,
            }
            note = _read_string(record.get("note"))
            if note:
                label_record["note"] = note
            label_records.append(label_record)
    return label_records


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


if __name__ == "__main__":
    main()
