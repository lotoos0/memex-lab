from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class FilteredSnapshot:
    mint: str
    snapshot_built_at: str | None
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
    score_version: str
    score_total: int
    score_reasons: list[str]
    score_flags: list[str]
    scored_at: str
    quality_band: str
    is_complete_record: bool
    has_blocking_flags: bool
    filter_version: str
    filter_reasons: list[str]

    def to_record(self) -> dict[str, Any]:
        return asdict(self)
