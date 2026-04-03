from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_AUDIT_PATH = REPO_ROOT / "data" / "reports" / "candidate_audit_v2.json"
REVIEW_LOOP_METRICS_PATH = REPO_ROOT / "data" / "reports" / "review_loop_metrics.json"
ALIGNMENT_PATH = REPO_ROOT / "data" / "reports" / "selector_scorer_alignment_v2.json"
FEEDBACK_PATH = REPO_ROOT / "data" / "reports" / "review_feedback_report.json"
OUTPUT_PATH = REPO_ROOT / "data" / "reports" / "operator_snapshot.json"


def main() -> None:
    candidate_audit = load_optional_report(CANDIDATE_AUDIT_PATH)
    review_loop_metrics = load_optional_report(REVIEW_LOOP_METRICS_PATH)
    alignment_report = load_optional_report(ALIGNMENT_PATH)
    feedback_report = load_optional_report(FEEDBACK_PATH)

    snapshot = build_snapshot(
        candidate_audit=candidate_audit,
        review_loop_metrics=review_loop_metrics,
        alignment_report=alignment_report,
        feedback_report=feedback_report,
    )
    write_json(OUTPUT_PATH, snapshot)
    print_summary(snapshot)


def build_snapshot(
    *,
    candidate_audit: dict[str, Any] | None,
    review_loop_metrics: dict[str, Any] | None,
    alignment_report: dict[str, Any] | None,
    feedback_report: dict[str, Any] | None,
) -> dict[str, Any]:
    completeness = {
        "candidate_audit_present": candidate_audit is not None,
        "review_loop_metrics_present": review_loop_metrics is not None,
        "alignment_report_present": alignment_report is not None,
        "feedback_report_present": feedback_report is not None,
    }

    return {
        "snapshot_version": "v0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_paths": {
            "candidate_audit_path": str(CANDIDATE_AUDIT_PATH),
            "review_loop_metrics_path": str(REVIEW_LOOP_METRICS_PATH),
            "alignment_report_path": str(ALIGNMENT_PATH),
            "feedback_report_path": str(FEEDBACK_PATH),
        },
        "snapshot_completeness": completeness,
        "candidate_state": build_candidate_state(candidate_audit),
        "review_loop_state": build_review_loop_state(review_loop_metrics),
        "alignment_state": build_alignment_state(alignment_report),
        "feedback_state": build_feedback_state(feedback_report),
    }


def build_candidate_state(candidate_audit: dict[str, Any] | None) -> dict[str, int | None]:
    if candidate_audit is None:
        return {
            "total_candidates": None,
            "review_now": None,
            "review_if_time": None,
            "ignore_for_now": None,
            "labeled_count": None,
        }

    totals = read_dict(candidate_audit.get("candidate_totals"))
    return {
        "total_candidates": read_int(totals.get("total_records")),
        "review_now": read_int(totals.get("total_review_now")),
        "review_if_time": read_int(totals.get("total_review_if_time")),
        "ignore_for_now": read_int(totals.get("total_ignore_for_now")),
        "labeled_count": read_int(totals.get("total_labeled_records")),
    }


def build_review_loop_state(
    review_loop_metrics: dict[str, Any] | None,
) -> dict[str, int | float | str | None]:
    if review_loop_metrics is None:
        return {
            "total_reviewed": None,
            "useful_count": None,
            "noise_count": None,
            "needs_more_context_count": None,
            "useful_rate": None,
            "sample_size_note": None,
        }

    review_coverage = read_dict(review_loop_metrics.get("review_coverage"))
    outcome_distribution = read_dict(review_loop_metrics.get("outcome_distribution"))
    return {
        "total_reviewed": read_int(review_coverage.get("total_reviewed_records")),
        "useful_count": read_int(outcome_distribution.get("useful_count")),
        "noise_count": read_int(outcome_distribution.get("noise_count")),
        "needs_more_context_count": read_int(
            outcome_distribution.get("needs_more_context_count")
        ),
        "useful_rate": read_float_or_none(outcome_distribution.get("useful_rate")),
        "sample_size_note": read_string(review_loop_metrics.get("sample_size_note")),
    }


def build_alignment_state(
    alignment_report: dict[str, Any] | None,
) -> dict[str, dict[str, int | None] | int | None]:
    if alignment_report is None:
        return {
            "scorer_band_distribution": {
                "weak": None,
                "partial": None,
                "strong": None,
            },
            "selector_candidate_class_distribution": {
                "review_now": None,
                "review_if_time": None,
                "ignore_for_now": None,
            },
            "weak_to_ignore_for_now_count": None,
        }

    scorer_band_distribution = read_dict(
        alignment_report.get("shared_scorer_band_from_scores_distribution")
    )
    selector_candidate_class_distribution = read_dict(
        alignment_report.get("shared_selector_candidate_class_distribution")
    )
    band_by_class = read_dict(
        alignment_report.get("shared_scorer_band_from_scores_by_selector_candidate_class")
    )
    weak_row = read_dict(band_by_class.get("weak"))

    return {
        "scorer_band_distribution": {
            "weak": read_int(scorer_band_distribution.get("weak")),
            "partial": read_int(scorer_band_distribution.get("partial")),
            "strong": read_int(scorer_band_distribution.get("strong")),
        },
        "selector_candidate_class_distribution": {
            "review_now": read_int(selector_candidate_class_distribution.get("review_now")),
            "review_if_time": read_int(
                selector_candidate_class_distribution.get("review_if_time")
            ),
            "ignore_for_now": read_int(
                selector_candidate_class_distribution.get("ignore_for_now")
            ),
        },
        "weak_to_ignore_for_now_count": read_int(weak_row.get("ignore_for_now")),
    }


def build_feedback_state(
    feedback_report: dict[str, Any] | None,
) -> dict[str, int | None]:
    if feedback_report is None:
        return {
            "reviewed_labeled_count": None,
            "reviewed_unlabeled_count": None,
            "review_now_useful_count": None,
            "review_if_time_noise_count": None,
        }

    totals = read_dict(feedback_report.get("totals"))
    indicators = read_dict(feedback_report.get("effectiveness_indicators"))
    candidate_class_by_outcome = read_dict(feedback_report.get("candidate_class_by_outcome"))
    review_now_outcomes = read_dict(candidate_class_by_outcome.get("review_now"))
    review_if_time_outcomes = read_dict(candidate_class_by_outcome.get("review_if_time"))

    total_reviewed_records = read_int(totals.get("total_reviewed_records"))
    reviewed_unlabeled_count = read_int(indicators.get("unlabeled_reviewed_count"))
    reviewed_labeled_count = None
    if total_reviewed_records is not None and reviewed_unlabeled_count is not None:
        reviewed_labeled_count = total_reviewed_records - reviewed_unlabeled_count

    return {
        "reviewed_labeled_count": reviewed_labeled_count,
        "reviewed_unlabeled_count": reviewed_unlabeled_count,
        "review_now_useful_count": read_int(review_now_outcomes.get("useful")),
        "review_if_time_noise_count": read_int(review_if_time_outcomes.get("noise")),
    }


def load_optional_report(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in report {path}: {exc}") from exc

    if not isinstance(document, dict):
        raise SystemExit(f"Expected a JSON object in report {path}.")
    return document


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def print_summary(snapshot: dict[str, Any]) -> None:
    candidate_state = snapshot["candidate_state"]
    review_loop_state = snapshot["review_loop_state"]
    alignment_state = snapshot["alignment_state"]
    completeness = snapshot["snapshot_completeness"]

    print(f"Operator snapshot written to {OUTPUT_PATH}")
    print(
        "candidates={total_candidates} review_now={review_now} review_if_time={review_if_time} ignore_for_now={ignore_for_now}".format(
            **candidate_state
        )
    )
    print(
        "reviewed={total_reviewed} useful={useful_count} noise={noise_count} needs_more_context={needs_more_context_count}".format(
            **review_loop_state
        )
    )
    print(
        "alignment weak={weak} partial={partial} strong={strong}".format(
            **alignment_state["scorer_band_distribution"]
        )
    )
    print(
        "reports candidate_audit={candidate_audit_present} review_loop_metrics={review_loop_metrics_present} alignment={alignment_report_present} feedback={feedback_report_present}".format(
            **{
                key: "present" if value else "missing"
                for key, value in completeness.items()
            }
        )
    )


def read_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def read_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    return None


def read_float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    return None


def read_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


if __name__ == "__main__":
    main()
