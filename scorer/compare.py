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
        description="Build an aggregate-only comparison report for scorer v0 and v1 outputs.",
    )
    parser.add_argument(
        "--v0-input-path",
        default=str(config.output_path_for("v0")),
        help="Scorer v0 JSONL input path.",
    )
    parser.add_argument(
        "--v1-input-path",
        default=str(config.output_path_for("v1")),
        help="Scorer v1 JSONL input path.",
    )
    parser.add_argument(
        "--output-path",
        default=str(config.comparison_output_path),
        help="Comparison JSON output path.",
    )
    args = parser.parse_args()

    comparison_report = build_comparison_report(
        v0_records=read_jsonl(Path(args.v0_input_path)),
        v1_records=read_jsonl(Path(args.v1_input_path)),
        v0_input_path=Path(args.v0_input_path),
        v1_input_path=Path(args.v1_input_path),
    )
    write_json(Path(args.output_path), comparison_report)
    print_summary(comparison_report, Path(args.output_path))


def build_comparison_report(
    *,
    v0_records: list[dict[str, Any]],
    v1_records: list[dict[str, Any]],
    v0_input_path: Path,
    v1_input_path: Path,
) -> dict[str, Any]:
    v0_by_mint = _index_by_mint(v0_records)
    v1_by_mint = _index_by_mint(v1_records)

    shared_mints = sorted(set(v0_by_mint) & set(v1_by_mint))
    v0_only_mints = sorted(set(v0_by_mint) - set(v1_by_mint))
    v1_only_mints = sorted(set(v1_by_mint) - set(v0_by_mint))

    changed_score_count = 0
    changed_flags_count = 0
    changed_score_band_count = 0
    score_delta_distribution: dict[str, int] = {}
    added_flag_counts: dict[str, int] = {}
    removed_flag_counts: dict[str, int] = {}
    v0_band_distribution: dict[str, int] = {}
    v1_band_distribution: dict[str, int] = {}

    for mint in shared_mints:
        v0_record = v0_by_mint[mint]
        v1_record = v1_by_mint[mint]

        v0_score_total = _read_int(v0_record.get("score_total"))
        v1_score_total = _read_int(v1_record.get("score_total"))
        score_delta = v1_score_total - v0_score_total
        score_delta_key = str(score_delta)
        score_delta_distribution[score_delta_key] = (
            score_delta_distribution.get(score_delta_key, 0) + 1
        )
        if score_delta != 0:
            changed_score_count += 1

        v0_flags = _read_string_set(v0_record.get("score_flags"))
        v1_flags = _read_string_set(v1_record.get("score_flags"))
        if v0_flags != v1_flags:
            changed_flags_count += 1

        for flag in sorted(v1_flags - v0_flags):
            added_flag_counts[flag] = added_flag_counts.get(flag, 0) + 1
        for flag in sorted(v0_flags - v1_flags):
            removed_flag_counts[flag] = removed_flag_counts.get(flag, 0) + 1

        v0_band = _score_band(v0_score_total, v0_flags)
        v1_band = _score_band(v1_score_total, v1_flags)
        v0_band_distribution[v0_band] = v0_band_distribution.get(v0_band, 0) + 1
        v1_band_distribution[v1_band] = v1_band_distribution.get(v1_band, 0) + 1
        if v0_band != v1_band:
            changed_score_band_count += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "v0_input_path": str(v0_input_path),
        "v1_input_path": str(v1_input_path),
        "overview": {
            "v0_record_count": len(v0_records),
            "v1_record_count": len(v1_records),
            "shared_record_count": len(shared_mints),
            "v0_only_record_count": len(v0_only_mints),
            "v1_only_record_count": len(v1_only_mints),
            "changed_score_count": changed_score_count,
            "changed_flags_count": changed_flags_count,
            "changed_score_band_count": changed_score_band_count,
        },
        "score_delta_distribution": {
            key: score_delta_distribution[key] for key in sorted(score_delta_distribution, key=int)
        },
        "score_band_distribution": {
            "v0": _sorted_band_distribution(v0_band_distribution),
            "v1": _sorted_band_distribution(v1_band_distribution),
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
