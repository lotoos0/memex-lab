from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class TokenCreatedEvent:
    observed_at: str
    source: str
    event_type: str
    signature: str | None
    slot: int | None
    instruction_name: str
    name: str
    symbol: str
    uri: str
    mint: str
    bonding_curve: str
    user: str
    creator: str
    token_standard: str
    is_mayhem_mode: bool
    raw_data_base64: str
    raw_logs: list[str]

    def to_record(self) -> dict[str, Any]:
        return asdict(self)
