from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from reviewfeedback.config import ALLOWED_OUTCOMES, ReviewFeedbackConfig
from reviewfeedback.io import read_jsonl, write_jsonl_overwrite


def main() -> None:
    args = _build_parser().parse_args()
    config = _build_config(args)

    if not config.candidates_path.exists():
        raise SystemExit(f"Candidate input file not found: {config.candidates_path}")

    candidate_records = read_jsonl(config.candidates_path)
    if not candidate_records:
        raise SystemExit(
            f"Candidate input file is empty or contains no valid records: {config.candidates_path}"
        )

    candidate_record = _find_candidate_record(candidate_records, args.mint)
    if candidate_record is None:
        raise SystemExit(
            f"Mint not found in review candidates input: mint={args.mint} input_path={config.candidates_path}"
        )
    candidate_class = _read_string(candidate_record.get("candidate_class"))
    if candidate_class is None:
        raise SystemExit(
            f"Candidate record is missing candidate_class: mint={args.mint} input_path={config.candidates_path}"
        )

    outcome_records = _load_outcomes(config.outcomes_path)
    outcome_record = {
        "mint": args.mint,
        "candidate_class": candidate_class,
        "outcome": args.outcome,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    if isinstance(args.note, str) and args.note:
        outcome_record["note"] = args.note
    outcome_records[args.mint] = outcome_record
    write_jsonl_overwrite(
        config.outcomes_path,
        [outcome_records[mint] for mint in sorted(outcome_records)],
    )

    print(
        "Stored review outcome mint={mint} outcome={outcome} candidate_class={candidate_class} output={output}".format(
            mint=args.mint,
            outcome=args.outcome,
            candidate_class=outcome_records[args.mint]["candidate_class"],
            output=config.outcomes_path,
        )
    )


def _build_parser() -> argparse.ArgumentParser:
    config = ReviewFeedbackConfig()
    parser = argparse.ArgumentParser(
        description="Record a manual review outcome for a candidate mint.",
    )
    parser.add_argument("--mint", required=True, help="Candidate mint to update.")
    parser.add_argument(
        "--outcome",
        required=True,
        choices=ALLOWED_OUTCOMES,
        help="Review outcome value.",
    )
    parser.add_argument("--note", help="Optional short review note.")
    parser.add_argument(
        "--candidates-path",
        default=str(config.candidates_path),
        help="Review candidates JSONL input path.",
    )
    parser.add_argument(
        "--outcomes-path",
        default=str(config.outcomes_path),
        help="Review outcomes JSONL output path.",
    )
    return parser


def _build_config(args: argparse.Namespace) -> ReviewFeedbackConfig:
    return ReviewFeedbackConfig(
        candidates_path=Path(args.candidates_path),
        outcomes_path=Path(args.outcomes_path),
    )


def _find_candidate_record(
    candidate_records: list[dict[str, object]],
    mint: str,
) -> dict[str, object] | None:
    for record in candidate_records:
        if _read_string(record.get("mint")) == mint:
            return record
    return None


def _load_outcomes(path: Path) -> dict[str, dict[str, object]]:
    outcomes: dict[str, dict[str, object]] = {}
    for record in read_jsonl(path):
        mint = _read_string(record.get("mint"))
        candidate_class = _read_string(record.get("candidate_class"))
        outcome = _read_string(record.get("outcome"))
        reviewed_at = _read_string(record.get("reviewed_at"))
        if mint and candidate_class and outcome and reviewed_at:
            outcome_record = {
                "mint": mint,
                "candidate_class": candidate_class,
                "outcome": outcome,
                "reviewed_at": reviewed_at,
            }
            note = _read_string(record.get("note"))
            if note is not None:
                outcome_record["note"] = note
            outcomes[mint] = outcome_record
    return outcomes


def _read_string(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


if __name__ == "__main__":
    main()
