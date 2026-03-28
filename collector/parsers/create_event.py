from __future__ import annotations

import base64
import binascii
import logging
import struct
from datetime import datetime, timezone

import base58

from collector.models.token_event import TokenCreatedEvent

logger = logging.getLogger(__name__)

CREATE_EVENT_DISCRIMINATOR = bytes([27, 114, 169, 77, 222, 235, 99, 118])
CREATE_INSTRUCTION_NAMES = frozenset({"Create", "CreateV2"})
TOKEN_STANDARD_BY_INSTRUCTION = {
    "Create": "legacy",
    "CreateV2": "token2022",
}
EVENT_TYPE = "token_created"


def parse_create_event(
    *,
    encoded_data: str,
    source: str,
    signature: str | None,
    slot: int | None,
    instruction_name: str,
    logs: list[str],
) -> TokenCreatedEvent | None:
    if instruction_name not in TOKEN_STANDARD_BY_INSTRUCTION:
        logger.warning("Skipping unsupported instruction name: %s", instruction_name)
        return None

    try:
        raw_data = base64.b64decode(encoded_data, validate=True)
    except (ValueError, binascii.Error) as error:
        logger.warning(
            "Skipping malformed create event for signature %s: invalid base64 (%s)",
            signature,
            error,
        )
        return None

    if len(raw_data) < 8 or raw_data[:8] != CREATE_EVENT_DISCRIMINATOR:
        return None

    try:
        fields = _parse_event_fields(raw_data, instruction_name)
    except ValueError as error:
        logger.warning(
            "Skipping malformed create event for signature %s: %s",
            signature,
            error,
        )
        return None

    return TokenCreatedEvent(
        observed_at=_utc_now(),
        source=source,
        event_type=EVENT_TYPE,
        signature=signature,
        slot=slot,
        instruction_name=instruction_name,
        name=fields["name"],
        symbol=fields["symbol"],
        uri=fields["uri"],
        mint=fields["mint"],
        bonding_curve=fields["bonding_curve"],
        user=fields["user"],
        creator=fields["creator"],
        token_standard=fields["token_standard"],
        is_mayhem_mode=fields["is_mayhem_mode"],
        raw_data_base64=encoded_data,
        raw_logs=list(logs),
    )


def _parse_event_fields(
    raw_data: bytes,
    instruction_name: str,
) -> dict[str, str | bool]:
    offset = 8

    name, offset = _read_string(raw_data, offset, "name")
    symbol, offset = _read_string(raw_data, offset, "symbol")
    uri, offset = _read_string(raw_data, offset, "uri")
    mint, offset = _read_pubkey(raw_data, offset, "mint")
    bonding_curve, offset = _read_pubkey(raw_data, offset, "bonding_curve")
    user, offset = _read_pubkey(raw_data, offset, "user")
    creator, offset = _read_pubkey(raw_data, offset, "creator")

    is_mayhem_mode = False
    if TOKEN_STANDARD_BY_INSTRUCTION[instruction_name] == "token2022":
        is_mayhem_mode = _read_optional_bool(raw_data, offset)

    return {
        "name": name,
        "symbol": symbol,
        "uri": uri,
        "mint": mint,
        "bonding_curve": bonding_curve,
        "user": user,
        "creator": creator,
        "token_standard": TOKEN_STANDARD_BY_INSTRUCTION[instruction_name],
        "is_mayhem_mode": is_mayhem_mode,
    }


def _read_string(data: bytes, offset: int, field_name: str) -> tuple[str, int]:
    if offset + 4 > len(data):
        raise ValueError(f"{field_name} length prefix is missing")

    length = struct.unpack("<I", data[offset : offset + 4])[0]
    offset += 4

    if offset + length > len(data):
        raise ValueError(f"{field_name} value is truncated")

    try:
        value = data[offset : offset + length].decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{field_name} is not valid UTF-8") from error

    return value, offset + length


def _read_pubkey(data: bytes, offset: int, field_name: str) -> tuple[str, int]:
    end_offset = offset + 32
    if end_offset > len(data):
        raise ValueError(f"{field_name} public key is truncated")

    value = base58.b58encode(data[offset:end_offset]).decode("ascii")
    return value, end_offset


def _read_optional_bool(data: bytes, offset: int) -> bool:
    if offset >= len(data):
        return False

    return data[offset] != 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
