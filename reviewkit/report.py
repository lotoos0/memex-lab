from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from reviewkit.config import ALLOWED_LABELS, ReviewkitPaths
from reviewkit.io import read_jsonl


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args = _build_parser().parse_args()
    input_path = Path(args.input_path)
    labels_path = Path(args.labels_path)

    records = read_jsonl(input_path)
    label_map = _load_label_map(labels_path)

    quality_band_counts = Counter(_read_string(record.get("quality_band")) or "unknown" for record in records)
    has_migrated_counts = Counter(bool(record.get("has_migrated")) for record in records)
    has_blocking_flag_counts = Counter(bool(record.get("has_blocking_flags")) for record in records)
    score_total_counts = Counter(_read_int(record.get("score_total")) for record in records)
    label_counts, unlabeled_count, orphan_labels = _count_labels(records, label_map)

    logger = logging.getLogger(__name__)
    logger.info("input_path=%s", input_path)
    logger.info("labels_path=%s", labels_path)
    logger.info("total_records=%s", len(records))
    logger.info(
        "quality_band_counts weak=%s partial=%s strong=%s",
        quality_band_counts.get("weak", 0),
        quality_band_counts.get("partial", 0),
        quality_band_counts.get("strong", 0),
    )
    logger.info(
        "has_migrated_counts false=%s true=%s",
        has_migrated_counts.get(False, 0),
        has_migrated_counts.get(True, 0),
    )
    logger.info(
        "has_blocking_flags_counts false=%s true=%s",
        has_blocking_flag_counts.get(False, 0),
        has_blocking_flag_counts.get(True, 0),
    )
    logger.info(
        "label_counts unlabeled=%s interesting=%s incomplete=%s suspect=%s review_later=%s orphan_labels=%s",
        unlabeled_count,
        label_counts.get("interesting", 0),
        label_counts.get("incomplete", 0),
        label_counts.get("suspect", 0),
        label_counts.get("review_later", 0),
        orphan_labels,
    )
    logger.info(
        "score_total_counts %s",
        " ".join(
            f"{score_total}={count}"
            for score_total, count in sorted(score_total_counts.items())
        ),
    )


def _build_parser() -> argparse.ArgumentParser:
    paths = ReviewkitPaths()
    parser = argparse.ArgumentParser(
        description="Print a concise summary report for filtered snapshots and labels.",
    )
    parser.add_argument(
        "--input-path",
        default=str(paths.filtered_snapshots_path),
        help="Filtered snapshots JSONL input path.",
    )
    parser.add_argument(
        "--labels-path",
        default=str(paths.labels_path),
        help="Labels JSONL input path.",
    )
    return parser


def _load_label_map(path: Path) -> dict[str, str]:
    label_map: dict[str, str] = {}
    for record in read_jsonl(path):
        mint = _read_string(record.get("mint"))
        label = _read_string(record.get("label"))
        if mint and label in ALLOWED_LABELS:
            label_map[mint] = label
    return label_map


def _count_labels(
    records: list[dict[str, Any]],
    label_map: dict[str, str],
) -> tuple[Counter[str], int, int]:
    record_mints = {
        mint
        for record in records
        if (mint := _read_string(record.get("mint")))
    }
    label_counts: Counter[str] = Counter()
    unlabeled_count = 0

    for record in records:
        mint = _read_string(record.get("mint"))
        label = label_map.get(mint or "")
        if label is None:
            unlabeled_count += 1
            continue
        label_counts[label] += 1

    orphan_labels = sum(1 for mint in label_map if mint not in record_mints)
    return label_counts, unlabeled_count, orphan_labels


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

