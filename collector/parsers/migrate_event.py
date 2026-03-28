from __future__ import annotations

import base64
import binascii
import logging
import struct
from datetime import datetime, timezone

import base58

from collector.models.migration_event import MigrationEvent

logger = logging.getLogger(__name__)

MIGRATE_INSTRUCTION_NAME = "Migrate"
MIGRATION_EVENT_TYPE = "token_migrated"
LEADING_BYTES_LENGTH = 8
MIGRATION_EVENT_MIN_LENGTH = (
    LEADING_BYTES_LENGTH
    + 8
    + 2
    + (3 * 32)
    + 1
    + 1
    + (7 * 8)
    + 1
    + (4 * 32)
)


def parse_migrate_event(
    *,
    encoded_data: str,
    source: str,
    signature: str | None,
    slot: int | None,
    instruction_name: str,
    logs: list[str],
) -> MigrationEvent | None:
    if instruction_name != MIGRATE_INSTRUCTION_NAME:
        logger.warning("Skipping unsupported migration instruction: %s", instruction_name)
        return None

    try:
        raw_data = base64.b64decode(encoded_data, validate=True)
    except (ValueError, binascii.Error) as error:
        logger.warning(
            "Skipping malformed migration event for signature %s: invalid base64 (%s)",
            signature,
            error,
        )
        return None

    # The reference parser skips the first 8 bytes before reading fields.
    # A stable discriminator is not confirmed in the reference code, so we only
    # enforce the minimum length required by that byte layout.
    if len(raw_data) < MIGRATION_EVENT_MIN_LENGTH:
        logger.warning(
            "Skipping malformed migration event for signature %s: expected at least %s bytes, got %s",
            signature,
            MIGRATION_EVENT_MIN_LENGTH,
            len(raw_data),
        )
        return None

    try:
        fields = _parse_event_fields(raw_data)
    except ValueError as error:
        logger.warning(
            "Skipping malformed migration event for signature %s: %s",
            signature,
            error,
        )
        return None

    return MigrationEvent(
        observed_at=_utc_now(),
        source=source,
        event_type=MIGRATION_EVENT_TYPE,
        signature=signature,
        slot=slot,
        instruction_name=instruction_name,
        migration_timestamp=fields["migration_timestamp"],
        migration_index=fields["migration_index"],
        creator=fields["creator"],
        mint=fields["mint"],
        quote_mint=fields["quote_mint"],
        base_mint_decimals=fields["base_mint_decimals"],
        quote_mint_decimals=fields["quote_mint_decimals"],
        base_amount_in=fields["base_amount_in"],
        quote_amount_in=fields["quote_amount_in"],
        pool_base_amount=fields["pool_base_amount"],
        pool_quote_amount=fields["pool_quote_amount"],
        minimum_liquidity=fields["minimum_liquidity"],
        initial_liquidity=fields["initial_liquidity"],
        lp_token_amount_out=fields["lp_token_amount_out"],
        pool_bump=fields["pool_bump"],
        pool=fields["pool"],
        lp_mint=fields["lp_mint"],
        user_base_token_account=fields["user_base_token_account"],
        user_quote_token_account=fields["user_quote_token_account"],
        raw_data_base64=encoded_data,
        raw_logs=list(logs),
    )


def _parse_event_fields(raw_data: bytes) -> dict[str, str | int]:
    offset = LEADING_BYTES_LENGTH

    migration_timestamp, offset = _read_i64(raw_data, offset, "timestamp")
    migration_index, offset = _read_u16(raw_data, offset, "index")
    creator, offset = _read_pubkey(raw_data, offset, "creator")
    mint, offset = _read_pubkey(raw_data, offset, "baseMint")
    quote_mint, offset = _read_pubkey(raw_data, offset, "quoteMint")
    base_mint_decimals, offset = _read_u8(raw_data, offset, "baseMintDecimals")
    quote_mint_decimals, offset = _read_u8(raw_data, offset, "quoteMintDecimals")
    base_amount_in, offset = _read_u64(raw_data, offset, "baseAmountIn")
    quote_amount_in, offset = _read_u64(raw_data, offset, "quoteAmountIn")
    pool_base_amount, offset = _read_u64(raw_data, offset, "poolBaseAmount")
    pool_quote_amount, offset = _read_u64(raw_data, offset, "poolQuoteAmount")
    minimum_liquidity, offset = _read_u64(raw_data, offset, "minimumLiquidity")
    initial_liquidity, offset = _read_u64(raw_data, offset, "initialLiquidity")
    lp_token_amount_out, offset = _read_u64(raw_data, offset, "lpTokenAmountOut")
    pool_bump, offset = _read_u8(raw_data, offset, "poolBump")
    pool, offset = _read_pubkey(raw_data, offset, "pool")
    lp_mint, offset = _read_pubkey(raw_data, offset, "lpMint")
    user_base_token_account, offset = _read_pubkey(
        raw_data,
        offset,
        "userBaseTokenAccount",
    )
    user_quote_token_account, offset = _read_pubkey(
        raw_data,
        offset,
        "userQuoteTokenAccount",
    )

    return {
        "migration_timestamp": migration_timestamp,
        "migration_index": migration_index,
        "creator": creator,
        "mint": mint,
        "quote_mint": quote_mint,
        "base_mint_decimals": base_mint_decimals,
        "quote_mint_decimals": quote_mint_decimals,
        "base_amount_in": base_amount_in,
        "quote_amount_in": quote_amount_in,
        "pool_base_amount": pool_base_amount,
        "pool_quote_amount": pool_quote_amount,
        "minimum_liquidity": minimum_liquidity,
        "initial_liquidity": initial_liquidity,
        "lp_token_amount_out": lp_token_amount_out,
        "pool_bump": pool_bump,
        "pool": pool,
        "lp_mint": lp_mint,
        "user_base_token_account": user_base_token_account,
        "user_quote_token_account": user_quote_token_account,
    }


def _read_pubkey(data: bytes, offset: int, field_name: str) -> tuple[str, int]:
    end_offset = offset + 32
    if end_offset > len(data):
        raise ValueError(f"{field_name} public key is truncated")

    return base58.b58encode(data[offset:end_offset]).decode("ascii"), end_offset


def _read_u64(data: bytes, offset: int, field_name: str) -> tuple[int, int]:
    end_offset = offset + 8
    if end_offset > len(data):
        raise ValueError(f"{field_name} is truncated")

    return struct.unpack("<Q", data[offset:end_offset])[0], end_offset


def _read_i64(data: bytes, offset: int, field_name: str) -> tuple[int, int]:
    end_offset = offset + 8
    if end_offset > len(data):
        raise ValueError(f"{field_name} is truncated")

    return struct.unpack("<q", data[offset:end_offset])[0], end_offset


def _read_u16(data: bytes, offset: int, field_name: str) -> tuple[int, int]:
    end_offset = offset + 2
    if end_offset > len(data):
        raise ValueError(f"{field_name} is truncated")

    return struct.unpack("<H", data[offset:end_offset])[0], end_offset


def _read_u8(data: bytes, offset: int, field_name: str) -> tuple[int, int]:
    if offset >= len(data):
        raise ValueError(f"{field_name} is truncated")

    return data[offset], offset + 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
