from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "data" / "reports" / "pipeline_health.json"
# This is an offline research workflow, so the threshold should warn about
# genuinely stale state without permanently forcing degraded status on
# normally-aged artifacts.
STALE_CORE_ARTIFACT_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class ArtifactSpec:
    key: str
    relative_path: str
    required: bool


ARTIFACT_SPECS = (
    ArtifactSpec("scored_snapshots_v2", "data/scored_snapshots_v2.jsonl", True),
    ArtifactSpec("review_candidates_v2", "data/review_candidates_v2.jsonl", True),
    ArtifactSpec("candidate_audit_v2", "data/reports/candidate_audit_v2.json", True),
    ArtifactSpec("review_loop_metrics", "data/reports/review_loop_metrics.json", True),
    ArtifactSpec("operator_snapshot", "data/reports/operator_snapshot.json", True),
    ArtifactSpec(
        "selector_scorer_alignment_v2",
        "data/reports/selector_scorer_alignment_v2.json",
        False,
    ),
    ArtifactSpec("review_feedback_report", "data/reports/review_feedback_report.json", False),
)


def main() -> None:
    now = datetime.now(timezone.utc)
    artifact_status = build_artifact_status(now)
    ordering_checks = build_ordering_checks(artifact_status)
    missing_artifacts = [
        status["path"]
        for status in artifact_status
        if status["required"] and not status["present"]
    ]
    warnings = build_warnings(artifact_status, ordering_checks)
    readiness_state = build_readiness_state(missing_artifacts, warnings)

    report = {
        "generated_at": now.isoformat(),
        "overall_status": {
            "readiness_state": readiness_state,
            "warning_count": len(warnings),
            "error_count": len(missing_artifacts),
        },
        "artifact_status": artifact_status,
        "ordering_checks": ordering_checks,
        "missing_artifacts": missing_artifacts,
        "warnings": warnings,
    }
    write_json(OUTPUT_PATH, report)
    print_summary(report)


def build_artifact_status(now: datetime) -> list[dict[str, Any]]:
    statuses: list[dict[str, Any]] = []
    for spec in ARTIFACT_SPECS:
        path = REPO_ROOT / spec.relative_path
        if not path.exists():
            statuses.append(
                {
                    "key": spec.key,
                    "path": spec.relative_path,
                    "required": spec.required,
                    "present": False,
                    "modified_at": None,
                    "age_seconds": None,
                }
            )
            continue

        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        age_seconds = int((now - modified_at).total_seconds())
        statuses.append(
            {
                "key": spec.key,
                "path": spec.relative_path,
                "required": spec.required,
                "present": True,
                "modified_at": modified_at.isoformat(),
                "age_seconds": age_seconds,
            }
        )
    return statuses


def build_ordering_checks(
    artifact_status: list[dict[str, Any]],
) -> list[dict[str, str | bool | None]]:
    indexed = {status["key"]: status for status in artifact_status}
    return [
        build_ordering_check(
            name="candidates_after_scored",
            earlier=indexed["scored_snapshots_v2"],
            later=indexed["review_candidates_v2"],
            reason="Candidates should be newer than scorer output.",
        ),
        build_ordering_check(
            name="candidate_audit_after_candidates",
            earlier=indexed["review_candidates_v2"],
            later=indexed["candidate_audit_v2"],
            reason="Candidate audit should be newer than candidate output.",
        ),
        build_ordering_check(
            name="operator_snapshot_after_candidate_audit",
            earlier=indexed["candidate_audit_v2"],
            later=indexed["operator_snapshot"],
            reason="Operator snapshot should be newer than candidate audit.",
        ),
        build_ordering_check(
            name="operator_snapshot_after_review_loop_metrics",
            earlier=indexed["review_loop_metrics"],
            later=indexed["operator_snapshot"],
            reason="Operator snapshot should be newer than review loop metrics.",
        ),
        build_ordering_check(
            name="operator_snapshot_after_alignment",
            earlier=indexed["selector_scorer_alignment_v2"],
            later=indexed["operator_snapshot"],
            reason="Operator snapshot should be newer than alignment report.",
        ),
        build_ordering_check(
            name="operator_snapshot_after_feedback",
            earlier=indexed["review_feedback_report"],
            later=indexed["operator_snapshot"],
            reason="Operator snapshot should be newer than feedback report.",
        ),
    ]


def build_ordering_check(
    *,
    name: str,
    earlier: dict[str, Any],
    later: dict[str, Any],
    reason: str,
) -> dict[str, str | bool | None]:
    if not earlier["present"] or not later["present"]:
        return {
            "name": name,
            "passed": None,
            "reason": "Skipped because one or more artifacts are missing.",
        }

    earlier_modified = earlier["modified_at"]
    later_modified = later["modified_at"]
    if not isinstance(earlier_modified, str) or not isinstance(later_modified, str):
        return {
            "name": name,
            "passed": None,
            "reason": "Skipped because modified times are unavailable.",
        }

    passed = later_modified > earlier_modified
    return {
        "name": name,
        "passed": passed,
        "reason": reason if not passed else "Passed.",
    }


def build_warnings(
    artifact_status: list[dict[str, Any]],
    ordering_checks: list[dict[str, str | bool | None]],
) -> list[str]:
    warnings: list[str] = []

    for status in artifact_status:
        if not status["required"] or not status["present"]:
            continue
        age_seconds = status["age_seconds"]
        if isinstance(age_seconds, int) and age_seconds > STALE_CORE_ARTIFACT_SECONDS:
            warnings.append(f"Stale core artifact: {status['path']}")

    for check in ordering_checks:
        if check["passed"] is False:
            warnings.append(f"Ordering check failed: {check['name']}")

    return warnings


def build_readiness_state(
    missing_artifacts: list[str],
    warnings: list[str],
) -> str:
    if missing_artifacts:
        return "not_ready"
    if warnings:
        return "degraded"
    return "ready"


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def print_summary(report: dict[str, Any]) -> None:
    overall_status = report["overall_status"]
    warnings = report["warnings"]
    top_issue = warnings[0] if warnings else "none"

    print(f"Pipeline health written to {OUTPUT_PATH}")
    print(
        "state={readiness_state} missing_required={error_count} warnings={warning_count}".format(
            **overall_status
        )
    )
    print(f"top_issue={top_issue}")


if __name__ == "__main__":
    main()
