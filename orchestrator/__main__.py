from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    command_args: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    purpose: str
    steps: tuple[WorkflowStep, ...]
    output_paths: tuple[str, ...]


WORKFLOWS: dict[str, WorkflowDefinition] = {
    "full_v2_review_flow": WorkflowDefinition(
        name="full_v2_review_flow",
        purpose=(
            "Run scorer v2, selector v2, candidate audit v2 outputs, and the "
            "review feedback report."
        ),
        steps=(
            WorkflowStep(
                name="Score snapshots with scorer v2",
                command_args=("-m", "scorer", "--score-version", "v2"),
            ),
            WorkflowStep(
                name="Build selector v2 candidates",
                command_args=("-m", "selector", "--selection-version", "v2"),
            ),
            WorkflowStep(
                name="Build candidate audit and review queues for v2 candidates",
                command_args=(
                    "-m",
                    "candidateaudit",
                    "--input-path",
                    "data/review_candidates_v2.jsonl",
                    "--report-output-path",
                    "data/reports/candidate_audit_v2.json",
                    "--queue-now-output-path",
                    "data/review_queue_now_v2.jsonl",
                    "--queue-if-time-output-path",
                    "data/review_queue_if_time_v2.jsonl",
                ),
            ),
            WorkflowStep(
                name="Build review feedback report",
                command_args=("-m", "reviewfeedback.report"),
            ),
        ),
        output_paths=(
            "data/scored_snapshots_v2.jsonl",
            "data/review_candidates_v2.jsonl",
            "data/reports/candidate_audit_v2.json",
            "data/review_queue_now_v2.jsonl",
            "data/review_queue_if_time_v2.jsonl",
            "data/reports/review_feedback_report.json",
        ),
    ),
    "refresh_candidates_only": WorkflowDefinition(
        name="refresh_candidates_only",
        purpose="Refresh selector v2 candidates and their audit outputs without rescoring.",
        steps=(
            WorkflowStep(
                name="Build selector v2 candidates",
                command_args=("-m", "selector", "--selection-version", "v2"),
            ),
            WorkflowStep(
                name="Build candidate audit and review queues for v2 candidates",
                command_args=(
                    "-m",
                    "candidateaudit",
                    "--input-path",
                    "data/review_candidates_v2.jsonl",
                    "--report-output-path",
                    "data/reports/candidate_audit_v2.json",
                    "--queue-now-output-path",
                    "data/review_queue_now_v2.jsonl",
                    "--queue-if-time-output-path",
                    "data/review_queue_if_time_v2.jsonl",
                ),
            ),
        ),
        output_paths=(
            "data/review_candidates_v2.jsonl",
            "data/reports/candidate_audit_v2.json",
            "data/review_queue_now_v2.jsonl",
            "data/review_queue_if_time_v2.jsonl",
        ),
    ),
    "feedback_report_only": WorkflowDefinition(
        name="feedback_report_only",
        purpose="Regenerate the review feedback report only.",
        steps=(
            WorkflowStep(
                name="Build review feedback report",
                command_args=("-m", "reviewfeedback.report"),
            ),
        ),
        output_paths=("data/reports/review_feedback_report.json",),
    ),
}


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list:
        _print_workflow_list()
        return

    if args.workflow is None:
        parser.print_help()
        raise SystemExit(2)

    _ensure_project_root()
    definition = WORKFLOWS[args.workflow]
    success, passed_steps, failed_step, failed_command = _run_workflow(definition)
    _print_workflow_summary(
        definition=definition,
        success=success,
        passed_steps=passed_steps,
        failed_step=failed_step,
        failed_command=failed_command,
    )
    if not success:
        raise SystemExit(1)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a predefined offline memex-lab workflow.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the available predefined workflows.",
    )
    parser.add_argument(
        "--workflow",
        choices=tuple(WORKFLOWS),
        help="Run one predefined workflow.",
    )
    return parser


def _ensure_project_root() -> None:
    current_directory = Path.cwd()
    if not (current_directory / "pyproject.toml").is_file() or not (
        current_directory / "orchestrator"
    ).is_dir():
        raise SystemExit(
            "Run orchestrator from the project root directory containing "
            f"pyproject.toml and orchestrator/. Current working directory: {current_directory}"
        )


def _print_workflow_list() -> None:
    print("Available workflows:")
    for definition in WORKFLOWS.values():
        print(
            f"- {definition.name}: {definition.purpose} "
            f"(steps={len(definition.steps)})"
        )


def _run_workflow(
    definition: WorkflowDefinition,
) -> tuple[bool, int, WorkflowStep | None, str | None]:
    print(f"Running workflow: {definition.name}")
    print(f"Purpose: {definition.purpose}")

    passed_steps = 0
    for step_index, step in enumerate(definition.steps, start=1):
        command = [sys.executable, *step.command_args]
        rendered_command = _render_command(command)
        print(f"[{step_index}/{len(definition.steps)}] {step.name}")
        print(f"command: {rendered_command}")
        result = subprocess.run(command, cwd=Path.cwd(), check=False)
        if result.returncode != 0:
            print(f"step_failed: {step.name}")
            print(f"failing_command: {rendered_command}")
            print(f"exit_code: {result.returncode}")
            return False, passed_steps, step, rendered_command
        passed_steps += 1
        print(f"step_passed: {step.name}")

    return True, passed_steps, None, None


def _print_workflow_summary(
    *,
    definition: WorkflowDefinition,
    success: bool,
    passed_steps: int,
    failed_step: WorkflowStep | None,
    failed_command: str | None,
) -> None:
    print(f"workflow={definition.name}")
    print(f"total_steps={len(definition.steps)} passed_steps={passed_steps}")
    if failed_step is not None and failed_command is not None:
        print(f"failed_step={failed_step.name}")
        print(f"failed_command={failed_command}")
    else:
        print("failed_step=none")
    print(
        "outputs={outputs}".format(
            outputs=", ".join(definition.output_paths) if definition.output_paths else "none"
        )
    )
    print(f"status={'success' if success else 'failure'}")


def _render_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


if __name__ == "__main__":
    main()
