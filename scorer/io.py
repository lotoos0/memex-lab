from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        logger.info("JSONL input not found, treating as empty: %s", path)
        return []

    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            try:
                record = json.loads(stripped_line)
            except json.JSONDecodeError as error:
                logger.warning(
                    "Skipping malformed JSONL line %s in %s: %s",
                    line_number,
                    path,
                    error,
                )
                continue

            if not isinstance(record, dict):
                logger.warning(
                    "Skipping non-object JSONL line %s in %s",
                    line_number,
                    path,
                )
                continue

            records.append(record)

    return records


def write_jsonl_overwrite(path: Path, items: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            line = json.dumps(_serialize_item(item), ensure_ascii=False)
            handle.write(line)
            handle.write("\n")


def _serialize_item(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item

    if hasattr(item, "to_record"):
        return item.to_record()

    raise TypeError(f"Unsupported JSONL item type: {type(item)!r}")
