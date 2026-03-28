from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PUMP_FUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
DEFAULT_OUTPUT_PATH = Path("data/events.jsonl")
DEFAULT_COMMITMENT = "processed"
DEFAULT_SOURCE = "pumpfun.logs"
RECONNECT_BACKOFF_SECONDS = 5


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    solana_node_wss_endpoint: str
    output_path: Path
    pump_program_id: str = PUMP_FUN_PROGRAM_ID
    commitment: str = DEFAULT_COMMITMENT
    source: str = DEFAULT_SOURCE
    reconnect_backoff_seconds: int = RECONNECT_BACKOFF_SECONDS


def load_config() -> CollectorConfig:
    load_dotenv()

    solana_node_wss_endpoint = os.getenv("SOLANA_NODE_WSS_ENDPOINT", "").strip()
    if not solana_node_wss_endpoint:
        raise RuntimeError(
            "Missing required environment variable: SOLANA_NODE_WSS_ENDPOINT"
        )

    output_path_value = os.getenv(
        "COLLECTOR_OUTPUT_PATH",
        str(DEFAULT_OUTPUT_PATH),
    ).strip()
    if not output_path_value:
        raise RuntimeError("COLLECTOR_OUTPUT_PATH cannot be empty")

    return CollectorConfig(
        solana_node_wss_endpoint=solana_node_wss_endpoint,
        output_path=Path(output_path_value),
    )
