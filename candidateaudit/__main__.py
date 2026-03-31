from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from candidateaudit.config import CandidateAuditConfig
from candidateaudit.io import read_jsonl, write_json, write_jsonl_overwrite
from candidateaudit.sections import (
    candidate_class_distribution,
    candidate_totals,
    class_label_alignment,
    class_quality_context,
    queue_sizes,
    queue_usefulness_notes,
)


def main() -> None:
    config = _build_config(_build_parser().parse_args())

    if not config.input_path.exists():
        raise SystemExit(f"Candidate input file not found: {config.input_path}")

    candidate_records = read_jsonl(config.input_path)
    if not candidate_records:
        raise SystemExit(
            f"Candidate input file is empty or contains no valid records: {config.input_path}"
        )

    review_now_records = [
        record
        for record in candidate_records
        if record.get("candidate_class") == "review_now"
    ]
    review_if_time_records = [
        record
        for record in candidate_records
        if record.get("candidate_class") == "review_if_time"
    ]

    # Embedded candidate `label` is the only label source of truth in M9.
    # If labels change, rerun `selector` before `candidateaudit`.
    audit_document = {
        "audit_version": config.audit_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_path": str(config.input_path),
        "candidate_totals": candidate_totals(candidate_records),
        "candidate_class_distribution": candidate_class_distribution(candidate_records),
        "class_label_alignment": class_label_alignment(candidate_records),
        "class_quality_context": class_quality_context(candidate_records),
        "queue_sizes": queue_sizes(review_now_records, review_if_time_records),
        "queue_usefulness_notes": queue_usefulness_notes(
            candidate_records,
            review_now_records,
            review_if_time_records,
        ),
    }

    write_json(config.audit_output_path, audit_document)
    write_jsonl_overwrite(config.review_queue_now_path, review_now_records)
    write_jsonl_overwrite(config.review_queue_if_time_path, review_if_time_records)
    _print_summary(audit_document, config)


def _build_parser() -> argparse.ArgumentParser:
    config = CandidateAuditConfig()
    parser = argparse.ArgumentParser(
        description="Build a candidate audit report and pass-through review queues.",
    )
    parser.add_argument(
        "--input-path",
        default=str(config.input_path),
        help="Review candidates JSONL input path.",
    )
    parser.add_argument(
        "--report-output-path",
        default=str(config.audit_output_path),
        help="Candidate audit JSON output path.",
    )
    parser.add_argument(
        "--queue-now-output-path",
        default=str(config.review_queue_now_path),
        help="Review-now queue JSONL output path.",
    )
    parser.add_argument(
        "--queue-if-time-output-path",
        default=str(config.review_queue_if_time_path),
        help="Review-if-time queue JSONL output path.",
    )
    return parser


def _build_config(args: argparse.Namespace) -> CandidateAuditConfig:
    return CandidateAuditConfig(
        input_path=Path(args.input_path),
        audit_output_path=Path(args.report_output_path),
        review_queue_now_path=Path(args.queue_now_output_path),
        review_queue_if_time_path=Path(args.queue_if_time_output_path),
    )


def _print_summary(
    audit_document: dict[str, object],
    config: CandidateAuditConfig,
) -> None:
    totals = audit_document["candidate_totals"]
    alignment = audit_document["class_label_alignment"]
    sizes = audit_document["queue_sizes"]
    notes = audit_document["queue_usefulness_notes"]

    print(f"Candidate audit written to {config.audit_output_path}")
    print(
        "records={total_records} review_now={total_review_now} review_if_time={total_review_if_time} ignore_for_now={total_ignore_for_now}".format(
            **totals
        )
    )
    print(
        "labels interesting_in_review_now={interesting_in_review_now} suspect_in_ignore_for_now={suspect_in_ignore_for_now} unlabeled_in_review_now={unlabeled_in_review_now}".format(
            **alignment
        )
    )
    print(
        "queues review_now={review_queue_now_count} review_if_time={review_queue_if_time_count}".format(
            **sizes
        )
    )
    print("notes={notes}".format(notes=" ".join(notes) if notes else "none"))


if __name__ == "__main__":
    main()
