from __future__ import annotations

from dataclasses import dataclass


LABEL_CHOICES = ("interesting", "suspect", "review_later", "incomplete")
OUTCOME_CHOICES = ("useful", "noise", "needs_more_context")


@dataclass(frozen=True, slots=True)
class CommandSpec:
    label: str
    module: str
    args: tuple[str, ...] = ()


def build_command_sections() -> tuple[tuple[str, tuple[CommandSpec, ...]], ...]:
    return (
        (
            "Pipeline",
            (
                CommandSpec("Build snapshots", "collector.snapshots"),
                CommandSpec("Score v0", "scorer"),
                CommandSpec("Score v1", "scorer", ("--score-version", "v1")),
                CommandSpec("Run pipeline health", "pipelinehealth"),
                CommandSpec("Compare v0 vs v1", "scorer", ("compare",)),
                CommandSpec(
                    "Run screener",
                    "screener",
                    (
                        "--input-path",
                        "data/scored_snapshots_v1.jsonl",
                        "--output-path",
                        "data/filtered_snapshots_v1.jsonl",
                    ),
                ),
            ),
        ),
        (
            "Review",
            (
                CommandSpec("Review report", "reviewkit.report"),
                CommandSpec("Dataset audit", "audit"),
                CommandSpec("Select candidates", "selector"),
                CommandSpec("Candidate audit", "candidateaudit"),
                CommandSpec("Feedback report", "reviewfeedback.report"),
            ),
        ),
        (
            "Workflows",
            (
                CommandSpec(
                    "full_v2_review_flow",
                    "orchestrator",
                    ("--workflow", "full_v2_review_flow"),
                ),
                CommandSpec(
                    "refresh_candidates_only",
                    "orchestrator",
                    ("--workflow", "refresh_candidates_only"),
                ),
                CommandSpec(
                    "feedback_report_only",
                    "orchestrator",
                    ("--workflow", "feedback_report_only"),
                ),
            ),
        ),
    )
