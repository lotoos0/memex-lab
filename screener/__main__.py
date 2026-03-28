from __future__ import annotations

import logging

from screener.config import load_config
from screener.engine import run_filtering


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config()
    filtered_snapshots = run_filtering(config)

    weak_count = sum(
        1 for snapshot in filtered_snapshots if snapshot.quality_band == "weak"
    )
    partial_count = sum(
        1 for snapshot in filtered_snapshots if snapshot.quality_band == "partial"
    )
    strong_count = sum(
        1 for snapshot in filtered_snapshots if snapshot.quality_band == "strong"
    )
    blocking_count = sum(
        1 for snapshot in filtered_snapshots if snapshot.has_blocking_flags
    )

    logging.getLogger(__name__).info(
        "Processed %s records: weak=%s partial=%s strong=%s blocking=%s output=%s",
        len(filtered_snapshots),
        weak_count,
        partial_count,
        strong_count,
        blocking_count,
        config.output_path,
    )


if __name__ == "__main__":
    main()
