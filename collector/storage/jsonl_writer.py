from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any


class JsonlWriter:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_event(self, event: Any) -> None:
        self._write_items([event], mode="a")

    def overwrite_items(self, items: Iterable[Any]) -> None:
        self._write_items(items, mode="w")

    def _write_items(self, items: Iterable[Any], mode: str) -> None:
        with self.output_path.open(mode, encoding="utf-8") as handle:
            for item in items:
                line = json.dumps(self._serialize_item(item), ensure_ascii=False)
                handle.write(line)
                handle.write("\n")

    def _serialize_item(self, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return item

        if hasattr(item, "to_record"):
            return item.to_record()

        raise TypeError(f"Unsupported JSONL item type: {type(item)!r}")
