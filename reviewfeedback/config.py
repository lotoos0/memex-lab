from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_REVIEW_CANDIDATES_PATH = Path("data/review_candidates.jsonl")
DEFAULT_REVIEW_OUTCOMES_PATH = Path("data/review_outcomes.jsonl")
DEFAULT_REVIEW_FEEDBACK_REPORT_PATH = Path("data/reports/review_feedback_report.json")
DEFAULT_REPORT_VERSION = "v0"
ALLOWED_OUTCOMES = ("useful", "noise", "needs_more_context")
KNOWN_LABELS = ("interesting", "suspect", "review_later", "incomplete")
KNOWN_CANDIDATE_CLASSES = ("review_now", "review_if_time", "ignore_for_now")


@dataclass(frozen=True, slots=True)
class ReviewFeedbackConfig:
    candidates_path: Path = DEFAULT_REVIEW_CANDIDATES_PATH
    outcomes_path: Path = DEFAULT_REVIEW_OUTCOMES_PATH
    report_output_path: Path = DEFAULT_REVIEW_FEEDBACK_REPORT_PATH
    report_version: str = DEFAULT_REPORT_VERSION

