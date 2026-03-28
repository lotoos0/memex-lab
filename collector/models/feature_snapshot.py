from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class FeatureSnapshot:
    mint: str
    snapshot_built_at: str
    first_seen_at: str | None
    created_at: str | None
    migrated_at: str | None
    has_migrated: bool
    token_standard: str | None
    creator: str | None
    bonding_curve: str | None
    migration_target: str | None
    source_count: int
    event_count: int

    def to_record(self) -> dict[str, Any]:
        return asdict(self)
