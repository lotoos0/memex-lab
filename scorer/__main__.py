from __future__ import annotations

import argparse
import logging
from pathlib import Path

from scorer.config import load_config
from scorer.compare import (
    build_comparison_report,
    print_summary as print_comparison_summary,
    write_json,
)
from scorer.engine import get_output_path, run_scoring
from scorer.io import read_jsonl


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config()
    parser = argparse.ArgumentParser(
        description="Run scorer v0/v1/v2 or compare scorer outputs.",
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
        choices=("v0", "v1", "v2"),
        default=config.score_version,
        help="Score version to write in score mode.",
    )
    parser.add_argument(
        "--left-version",
        choices=("v0", "v1", "v2"),
        default="v0",
        help="Left score version for compare mode.",
    )
    parser.add_argument(
        "--right-version",
        choices=("v0", "v1", "v2"),
        default="v1",
        help="Right score version for compare mode.",
    )
    parser.add_argument(
        "--left-input-path",
        default=None,
        help="Left scorer JSONL input path for compare mode.",
    )
    parser.add_argument(
        "--right-input-path",
        default=None,
        help="Right scorer JSONL input path for compare mode.",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="Comparison JSON output path for compare mode.",
    )
    args = parser.parse_args()

    if args.command == "compare":
        left_input_path = Path(args.left_input_path or get_output_path(config, score_version=args.left_version))
        right_input_path = Path(
            args.right_input_path or get_output_path(config, score_version=args.right_version)
        )
        compare_output_path = Path(
            args.output_path
            or config.comparison_output_path_for(args.left_version, args.right_version)
        )
        comparison_report = build_comparison_report(
            left_records=read_jsonl(left_input_path),
            right_records=read_jsonl(right_input_path),
            left_version=args.left_version,
            right_version=args.right_version,
            left_input_path=left_input_path,
            right_input_path=right_input_path,
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
