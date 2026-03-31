from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from selector.config import SelectorConfig
from selector.io import read_jsonl

BAND_ORDER = ("weak", "partial", "strong")
CANDIDATE_CLASS_ORDER = ("review_now", "review_if_time", "ignore_for_now")

# This mirrors the screener blocking flag set and must stay in sync with
# `screener.rules` and `scorer.compare`.
SCREENING_BLOCKING_FLAGS = frozenset(
    {
        "missing_create_event",
        "lifecycle_order_invalid",
        "missing_mint",
    }
)


def main() -> None:
    config = SelectorConfig()
    parser = argparse.ArgumentParser(
        description="Build an aggregate-only selector/scorer alignment report.",
    )
    parser.add_argument(
        "--scored-input-path",
        default=str(config.alignment_scored_input_path),
        help="Scored snapshots JSONL input path for alignment.",
    )
    parser.add_argument(
        "--candidate-input-path",
        default=str(config.alignment_candidate_input_path),
        help="Selector candidates JSONL input path for alignment.",
    )
    parser.add_argument(
        "--output-path",
        default=str(config.alignment_output_path),
        help="Alignment JSON output path.",
    )
    args = parser.parse_args()

    report = build_alignment_report(
        scored_records=read_jsonl(Path(args.scored_input_path)),
        candidate_records=read_jsonl(Path(args.candidate_input_path)),
        scored_input_path=Path(args.scored_input_path),
        candidate_input_path=Path(args.candidate_input_path),
    )
    write_json(Path(args.output_path), report)
    print_summary(report, Path(args.output_path))


def build_alignment_report(
    *,
    scored_records: list[dict[str, Any]],
    candidate_records: list[dict[str, Any]],
    scored_input_path: Path,
    candidate_input_path: Path,
) -> dict[str, Any]:
    scored_by_mint = _index_by_mint(scored_records)
    candidate_by_mint = _index_by_mint(candidate_records)

    shared_mints = sorted(set(scored_by_mint) & set(candidate_by_mint))
    scored_only_mints = sorted(set(scored_by_mint) - set(candidate_by_mint))
    candidate_only_mints = sorted(set(candidate_by_mint) - set(scored_by_mint))

    shared_scorer_band_from_scores_distribution = _empty_band_counts()
    shared_selector_candidate_class_distribution = _empty_candidate_class_counts()
    shared_scorer_band_from_scores_by_selector_candidate_class = _empty_band_by_candidate_class()
    shared_selector_candidate_class_by_scorer_band_from_scores = _empty_candidate_class_by_band()
    selector_v2_reason_distribution: dict[str, int] = {}

    # "scorer_band_from_scores" is derived locally from scorer output by mirroring
    # screener band logic. "selector_candidate_class" comes directly from selector output.
    for mint in shared_mints:
        scorer_band_from_scores = _score_band_from_scored_snapshot(scored_by_mint[mint])
        selector_candidate_record = candidate_by_mint[mint]
        selector_candidate_class = _read_string(
            selector_candidate_record.get("candidate_class")
        )

        if selector_candidate_class not in CANDIDATE_CLASS_ORDER:
            continue

        for reason in _read_string_list(selector_candidate_record.get("candidate_reasons")):
            selector_v2_reason_distribution[reason] = (
                selector_v2_reason_distribution.get(reason, 0) + 1
            )

        shared_scorer_band_from_scores_distribution[scorer_band_from_scores] += 1
        shared_selector_candidate_class_distribution[selector_candidate_class] += 1
        shared_scorer_band_from_scores_by_selector_candidate_class[scorer_band_from_scores][
            selector_candidate_class
        ] += 1
        shared_selector_candidate_class_by_scorer_band_from_scores[selector_candidate_class][
            scorer_band_from_scores
        ] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scored_input_path": str(scored_input_path),
        "candidate_input_path": str(candidate_input_path),
        "overview": {
            "scored_record_count": len(scored_records),
            "candidate_record_count": len(candidate_records),
            "shared_record_count": len(shared_mints),
            "scored_only_record_count": len(scored_only_mints),
            "candidate_only_record_count": len(candidate_only_mints),
        },
        "shared_scorer_band_from_scores_distribution": (
            shared_scorer_band_from_scores_distribution
        ),
        "shared_selector_candidate_class_distribution": (
            shared_selector_candidate_class_distribution
        ),
        "shared_scorer_band_from_scores_by_selector_candidate_class": (
            shared_scorer_band_from_scores_by_selector_candidate_class
        ),
        "shared_selector_candidate_class_by_scorer_band_from_scores": (
            shared_selector_candidate_class_by_scorer_band_from_scores
        ),
        "selector_v2_reason_distribution": {
            reason: selector_v2_reason_distribution[reason]
            for reason in sorted(selector_v2_reason_distribution)
        },
    }


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def print_summary(report: dict[str, Any], output_path: Path) -> None:
    overview = report["overview"]
    band_distribution = report["shared_scorer_band_from_scores_distribution"]

    print(f"Selector alignment written to {output_path}")
    print(
        "shared={shared_record_count} scored_only={scored_only_record_count} candidate_only={candidate_only_record_count}".format(
            **overview
        )
    )
    print(
        "bands weak={weak} partial={partial} strong={strong}".format(
            **band_distribution
        )
    )


def _score_band_from_scored_snapshot(scored_record: dict[str, Any]) -> str:
    # This mirrors screener band thresholds locally for alignment reporting and
    # must stay in sync with `screener.rules`.
    score_total = _read_int(scored_record.get("score_total"))
    score_flags = _read_string_set(scored_record.get("score_flags"))
    has_blocking_flags = any(flag in SCREENING_BLOCKING_FLAGS for flag in score_flags)
    if score_total >= 7 and not has_blocking_flags:
        return "strong"
    if score_total <= 3:
        return "weak"
    return "partial"


def _index_by_mint(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed_records: dict[str, dict[str, Any]] = {}
    for record in records:
        mint = _read_string(record.get("mint"))
        if mint is not None:
            indexed_records[mint] = record
    return indexed_records


def _empty_band_counts() -> dict[str, int]:
    return {band: 0 for band in BAND_ORDER}


def _empty_candidate_class_counts() -> dict[str, int]:
    return {candidate_class: 0 for candidate_class in CANDIDATE_CLASS_ORDER}


def _empty_band_by_candidate_class() -> dict[str, dict[str, int]]:
    return {
        band: _empty_candidate_class_counts()
        for band in BAND_ORDER
    }


def _empty_candidate_class_by_band() -> dict[str, dict[str, int]]:
    return {
        candidate_class: _empty_band_counts()
        for candidate_class in CANDIDATE_CLASS_ORDER
    }


def _read_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0


def _read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _read_string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str) and item}


def _read_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


if __name__ == "__main__":
    main()
