from __future__ import annotations

import logging

from scorer.config import load_config
from scorer.engine import run_scoring


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config()
    scored_snapshots = run_scoring(config)

    if scored_snapshots:
        scores = [snapshot.score_total for snapshot in scored_snapshots]
        logging.getLogger(__name__).info(
            "Wrote %s scored snapshots to %s (min=%s, max=%s)",
            len(scored_snapshots),
            config.output_path,
            min(scores),
            max(scores),
        )
    else:
        logging.getLogger(__name__).info(
            "Wrote 0 scored snapshots to %s",
            config.output_path,
        )


if __name__ == "__main__":
    main()
