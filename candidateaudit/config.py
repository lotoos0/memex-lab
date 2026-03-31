from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_REVIEW_CANDIDATES_PATH = Path("data/review_candidates.jsonl")
DEFAULT_CANDIDATE_AUDIT_OUTPUT_PATH = Path("data/reports/candidate_audit.json")
DEFAULT_REVIEW_QUEUE_NOW_PATH = Path("data/review_queue_now.jsonl")
DEFAULT_REVIEW_QUEUE_IF_TIME_PATH = Path("data/review_queue_if_time.jsonl")
DEFAULT_AUDIT_VERSION = "v0"


@dataclass(frozen=True, slots=True)
class CandidateAuditConfig:
    input_path: Path = DEFAULT_REVIEW_CANDIDATES_PATH
    audit_output_path: Path = DEFAULT_CANDIDATE_AUDIT_OUTPUT_PATH
    review_queue_now_path: Path = DEFAULT_REVIEW_QUEUE_NOW_PATH
    review_queue_if_time_path: Path = DEFAULT_REVIEW_QUEUE_IF_TIME_PATH
    audit_version: str = DEFAULT_AUDIT_VERSION

