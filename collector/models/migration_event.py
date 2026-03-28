from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class MigrationEvent:
    observed_at: str
    source: str
    event_type: str
    signature: str | None
    slot: int | None
    instruction_name: str
    migration_timestamp: int
    migration_index: int
    creator: str
    mint: str
    quote_mint: str
    base_mint_decimals: int
    quote_mint_decimals: int
    base_amount_in: int
    quote_amount_in: int
    pool_base_amount: int
    pool_quote_amount: int
    minimum_liquidity: int
    initial_liquidity: int
    lp_token_amount_out: int
    pool_bump: int
    pool: str
    lp_mint: str
    user_base_token_account: str
    user_quote_token_account: str
    raw_data_base64: str
    raw_logs: list[str]

    def to_record(self) -> dict[str, Any]:
        return asdict(self)
