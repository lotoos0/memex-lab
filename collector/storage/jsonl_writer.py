from __future__ import annotations

import json
from pathlib import Path

from collector.models.token_event import TokenCreatedEvent


class JsonlWriter:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_event(self, event: TokenCreatedEvent) -> None:
        line = json.dumps(event.to_record(), ensure_ascii=False)
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.write("\n")
