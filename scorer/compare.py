from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scorer.config import load_config
from scorer.io import read_jsonl

# This mirrors the screener blocking flag set and must be kept manually in sync.
SCREENING_BLOCKING_FLAGS = frozenset(
    {
        "missing_create_event",
        "lifecycle_order_invalid",
        "missing_mint",
    }
)


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(
        description="Build an aggregate-only comparison report for scorer outputs.",
    )
    parser.add_argument(
        "--left-version",
        choices=("v0", "v1", "v2"),
        default="v0",
        help="Left scorer version.",
    )
    parser.add_argument(
        "--right-version",
        choices=("v0", "v1", "v2"),
        default="v1",
        help="Right scorer version.",
    )
    parser.add_argument(
        "--left-input-path",
        default=None,
        help="Left scorer JSONL input path.",
    )
    parser.add_argument(
        "--right-input-path",
        default=None,
        help="Right scorer JSONL input path.",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="Comparison JSON output path.",
    )
    args = parser.parse_args()

    left_input_path = Path(args.left_input_path or str(config.output_path_for(args.left_version)))
    right_input_path = Path(
        args.right_input_path or str(config.output_path_for(args.right_version))
    )
    output_path = Path(
        args.output_path
        or str(config.comparison_output_path_for(args.left_version, args.right_version))
    )

    comparison_report = build_comparison_report(
        left_records=read_jsonl(left_input_path),
        right_records=read_jsonl(right_input_path),
        left_version=args.left_version,
        right_version=args.right_version,
        left_input_path=left_input_path,
        right_input_path=right_input_path,
    )
    write_json(output_path, comparison_report)
    print_summary(comparison_report, output_path)


def build_comparison_report(
    *,
    left_records: list[dict[str, Any]],
    right_records: list[dict[str, Any]],
    left_version: str,
    right_version: str,
    left_input_path: Path,
    right_input_path: Path,
) -> dict[str, Any]:
    left_by_mint = _index_by_mint(left_records)
    right_by_mint = _index_by_mint(right_records)

    shared_mints = sorted(set(left_by_mint) & set(right_by_mint))
    left_only_mints = sorted(set(left_by_mint) - set(right_by_mint))
    right_only_mints = sorted(set(right_by_mint) - set(left_by_mint))

    changed_score_count = 0
    changed_flags_count = 0
    changed_score_band_count = 0
    score_delta_distribution: dict[str, int] = {}
    added_flag_counts: dict[str, int] = {}
    removed_flag_counts: dict[str, int] = {}
    left_band_distribution: dict[str, int] = {}
    right_band_distribution: dict[str, int] = {}

    for mint in shared_mints:
        left_record = left_by_mint[mint]
        right_record = right_by_mint[mint]

        left_score_total = _read_int(left_record.get("score_total"))
        right_score_total = _read_int(right_record.get("score_total"))
        score_delta = right_score_total - left_score_total
        score_delta_key = str(score_delta)
        score_delta_distribution[score_delta_key] = (
            score_delta_distribution.get(score_delta_key, 0) + 1
        )
        if score_delta != 0:
            changed_score_count += 1

        left_flags = _read_string_set(left_record.get("score_flags"))
        right_flags = _read_string_set(right_record.get("score_flags"))
        if left_flags != right_flags:
            changed_flags_count += 1

        for flag in sorted(right_flags - left_flags):
            added_flag_counts[flag] = added_flag_counts.get(flag, 0) + 1
        for flag in sorted(left_flags - right_flags):
            removed_flag_counts[flag] = removed_flag_counts.get(flag, 0) + 1

        left_band = _score_band(left_score_total, left_flags)
        right_band = _score_band(right_score_total, right_flags)
        left_band_distribution[left_band] = left_band_distribution.get(left_band, 0) + 1
        right_band_distribution[right_band] = right_band_distribution.get(right_band, 0) + 1
        if left_band != right_band:
            changed_score_band_count += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        f"{left_version}_input_path": str(left_input_path),
        f"{right_version}_input_path": str(right_input_path),
        "overview": {
            f"{left_version}_record_count": len(left_records),
            f"{right_version}_record_count": len(right_records),
            "shared_record_count": len(shared_mints),
            f"{left_version}_only_record_count": len(left_only_mints),
            f"{right_version}_only_record_count": len(right_only_mints),
            "changed_score_count": changed_score_count,
            "changed_flags_count": changed_flags_count,
            "changed_score_band_count": changed_score_band_count,
        },
        "score_delta_distribution": {
            key: score_delta_distribution[key] for key in sorted(score_delta_distribution, key=int)
        },
        "score_band_distribution": {
            left_version: _sorted_band_distribution(left_band_distribution),
            right_version: _sorted_band_distribution(right_band_distribution),
        },
        "flag_delta_summary": {
            "added_flag_counts": {
                key: added_flag_counts[key] for key in sorted(added_flag_counts)
            },
            "removed_flag_counts": {
                key: removed_flag_counts[key] for key in sorted(removed_flag_counts)
            },
        },
    }


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def print_summary(report: dict[str, Any], output_path: Path) -> None:
    overview = report["overview"]
    score_deltas = report["score_delta_distribution"]

    print(f"Comparison written to {output_path}")
    print(
        "shared={shared_record_count} changed_scores={changed_score_count} changed_flags={changed_flags_count} changed_bands={changed_score_band_count}".format(
            **overview
        )
    )
    print(
        "score_deltas {score_deltas}".format(
            score_deltas=" ".join(f"{delta}={count}" for delta, count in score_deltas.items())
        )
    )


def _index_by_mint(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed_records: dict[str, dict[str, Any]] = {}
    for record in records:
        mint = record.get("mint")
        if isinstance(mint, str) and mint:
            indexed_records[mint] = record
    return indexed_records


def _score_band(score_total: int, score_flags: set[str]) -> str:
    has_blocking_flags = any(flag in SCREENING_BLOCKING_FLAGS for flag in score_flags)
    if score_total >= 7 and not has_blocking_flags:
        return "strong"
    if score_total <= 3:
        return "weak"
    return "partial"


def _sorted_band_distribution(counts: dict[str, int]) -> dict[str, int]:
    return {
        "weak": counts.get("weak", 0),
        "partial": counts.get("partial", 0),
        "strong": counts.get("strong", 0),
    }


def _read_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0


def _read_string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str) and item}


if __name__ == "__main__":
    main()
