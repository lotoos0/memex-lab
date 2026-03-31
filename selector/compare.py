from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from selector.config import SelectorConfig
from selector.io import read_jsonl

CANDIDATE_CLASS_ORDER = ("review_now", "review_if_time", "ignore_for_now")


def main() -> None:
    config = SelectorConfig()
    parser = argparse.ArgumentParser(
        description="Build an aggregate-only comparison report for selector v1 and v2 outputs.",
    )
    parser.add_argument(
        "--v1-input-path",
        default=str(config.output_path_for("v1")),
        help="Selector v1 JSONL input path.",
    )
    parser.add_argument(
        "--v2-input-path",
        default=str(config.output_path_for("v2")),
        help="Selector v2 JSONL input path.",
    )
    parser.add_argument(
        "--output-path",
        default=str(config.comparison_output_path),
        help="Comparison JSON output path.",
    )
    args = parser.parse_args()

    comparison_report = build_comparison_report(
        v1_records=read_jsonl(Path(args.v1_input_path)),
        v2_records=read_jsonl(Path(args.v2_input_path)),
        v1_input_path=Path(args.v1_input_path),
        v2_input_path=Path(args.v2_input_path),
    )
    write_json(Path(args.output_path), comparison_report)
    print_summary(comparison_report, Path(args.output_path))


def build_comparison_report(
    *,
    v1_records: list[dict[str, Any]],
    v2_records: list[dict[str, Any]],
    v1_input_path: Path,
    v2_input_path: Path,
) -> dict[str, Any]:
    v1_by_mint = _index_by_mint(v1_records)
    v2_by_mint = _index_by_mint(v2_records)

    shared_mints = sorted(set(v1_by_mint) & set(v2_by_mint))
    v1_only_mints = sorted(set(v1_by_mint) - set(v2_by_mint))
    v2_only_mints = sorted(set(v2_by_mint) - set(v1_by_mint))

    changed_class_count = 0
    class_transition_distribution: dict[str, int] = {}
    v2_rule_impact_summary = {
        "non_migrated_partial_default_ignore_count": 0,
        "interesting_rescue_to_review_if_time_count": 0,
        "review_later_rescue_to_review_if_time_count": 0,
        "migrated_partial_review_now_count": 0,
    }

    v1_distribution = _class_distribution(v1_records)
    v2_distribution = _class_distribution(v2_records)
    _populate_rule_impact_summary(v2_records, v2_rule_impact_summary)

    for mint in shared_mints:
        v1_record = v1_by_mint[mint]
        v2_record = v2_by_mint[mint]

        v1_class = _read_string(v1_record.get("candidate_class")) or "unknown"
        v2_class = _read_string(v2_record.get("candidate_class")) or "unknown"

        transition_key = f"{v1_class}->{v2_class}"
        class_transition_distribution[transition_key] = (
            class_transition_distribution.get(transition_key, 0) + 1
        )
        if v1_class != v2_class:
            changed_class_count += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "v1_input_path": str(v1_input_path),
        "v2_input_path": str(v2_input_path),
        "overview": {
            "v1_record_count": len(v1_records),
            "v2_record_count": len(v2_records),
            "shared_record_count": len(shared_mints),
            "v1_only_record_count": len(v1_only_mints),
            "v2_only_record_count": len(v2_only_mints),
            "changed_class_count": changed_class_count,
        },
        "candidate_class_distribution": {
            "v1": v1_distribution,
            "v2": v2_distribution,
        },
        "class_transition_distribution": {
            key: class_transition_distribution[key]
            for key in sorted(class_transition_distribution)
        },
        "v2_rule_impact_summary": v2_rule_impact_summary,
    }


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def print_summary(report: dict[str, Any], output_path: Path) -> None:
    overview = report["overview"]
    distributions = report["candidate_class_distribution"]

    print(f"Selector comparison written to {output_path}")
    print(
        "shared={shared_record_count} changed_classes={changed_class_count}".format(
            **overview
        )
    )
    print(
        "v1 review_now={v1_review_now} review_if_time={v1_review_if_time} ignore_for_now={v1_ignore_for_now}".format(
            v1_review_now=distributions["v1"]["review_now"],
            v1_review_if_time=distributions["v1"]["review_if_time"],
            v1_ignore_for_now=distributions["v1"]["ignore_for_now"],
        )
    )
    print(
        "v2 review_now={v2_review_now} review_if_time={v2_review_if_time} ignore_for_now={v2_ignore_for_now}".format(
            v2_review_now=distributions["v2"]["review_now"],
            v2_review_if_time=distributions["v2"]["review_if_time"],
            v2_ignore_for_now=distributions["v2"]["ignore_for_now"],
        )
    )


def _index_by_mint(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed_records: dict[str, dict[str, Any]] = {}
    for record in records:
        mint = _read_string(record.get("mint"))
        if mint is not None:
            indexed_records[mint] = record
    return indexed_records


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _read_string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str) and item}


def _class_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    distribution = {candidate_class: 0 for candidate_class in CANDIDATE_CLASS_ORDER}
    for record in records:
        candidate_class = _read_string(record.get("candidate_class"))
        if candidate_class in distribution:
            distribution[candidate_class] += 1
    return distribution


def _populate_rule_impact_summary(
    records: list[dict[str, Any]],
    summary: dict[str, int],
) -> None:
    for record in records:
        reasons = _read_string_set(record.get("candidate_reasons"))
        if "non_migrated_partial_default_ignore" in reasons:
            summary["non_migrated_partial_default_ignore_count"] += 1
        if "interesting_label_rescue" in reasons:
            summary["interesting_rescue_to_review_if_time_count"] += 1
        if "review_later_label_rescue" in reasons:
            summary["review_later_rescue_to_review_if_time_count"] += 1
        if "migrated_partial" in reasons:
            summary["migrated_partial_review_now_count"] += 1


if __name__ == "__main__":
    main()
