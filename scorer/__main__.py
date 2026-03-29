from __future__ import annotations

import argparse
import logging
from pathlib import Path

from scorer.config import load_config
from scorer.compare import build_comparison_report, print_summary as print_comparison_summary, write_json
from scorer.engine import get_output_path, run_scoring
from scorer.io import read_jsonl


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config()
    parser = argparse.ArgumentParser(
        description="Run scorer v0/v1 or compare scorer outputs.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("score", "compare"),
        default="score",
        help="Choose scoring or comparison mode.",
    )
    parser.add_argument(
        "--score-version",
        choices=("v0", "v1"),
        default=config.score_version,
        help="Score version to write in score mode.",
    )
    parser.add_argument(
        "--v0-input-path",
        default=get_output_path(config, score_version="v0"),
        help="Scorer v0 JSONL input path for compare mode.",
    )
    parser.add_argument(
        "--v1-input-path",
        default=get_output_path(config, score_version="v1"),
        help="Scorer v1 JSONL input path for compare mode.",
    )
    parser.add_argument(
        "--output-path",
        default=str(config.comparison_output_path),
        help="Comparison JSON output path for compare mode.",
    )
    args = parser.parse_args()

    if args.command == "compare":
        v0_input_path = Path(args.v0_input_path)
        v1_input_path = Path(args.v1_input_path)
        compare_output_path = Path(args.output_path)
        comparison_report = build_comparison_report(
            v0_records=read_jsonl(v0_input_path),
            v1_records=read_jsonl(v1_input_path),
            v0_input_path=v0_input_path,
            v1_input_path=v1_input_path,
        )
        write_json(compare_output_path, comparison_report)
        print_comparison_summary(comparison_report, compare_output_path)
        return

    scored_snapshots = run_scoring(config, score_version=args.score_version)
    output_path = get_output_path(config, score_version=args.score_version)

    if scored_snapshots:
        scores = [snapshot.score_total for snapshot in scored_snapshots]
        logging.getLogger(__name__).info(
            "Wrote %s %s scored snapshots to %s (min=%s, max=%s)",
            len(scored_snapshots),
            args.score_version,
            output_path,
            min(scores),
            max(scores),
        )
    else:
        logging.getLogger(__name__).info(
            "Wrote 0 %s scored snapshots to %s",
            args.score_version,
            output_path,
        )


if __name__ == "__main__":
    main()
