from __future__ import annotations

from screener.config import ScreenerConfig
from screener.io import read_jsonl, write_jsonl_overwrite
from screener.models.filtered_snapshot import FilteredSnapshot
from screener.rules import filter_snapshot


def run_filtering(config: ScreenerConfig) -> list[FilteredSnapshot]:
    scored_records = read_jsonl(config.input_path)

    filtered_snapshots = [
        filter_snapshot(
            scored_record=record,
            filter_version=config.filter_version,
        )
        for record in sorted(scored_records, key=_sort_key)
    ]

    write_jsonl_overwrite(config.output_path, filtered_snapshots)
    return filtered_snapshots


def _sort_key(record: dict[str, object]) -> tuple[str, str]:
    mint = record.get("mint")
    scored_at = record.get("scored_at")
    return (
        mint if isinstance(mint, str) else "",
        scored_at if isinstance(scored_at, str) else "",
    )
