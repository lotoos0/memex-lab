from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PUMP_FUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_FUN_MIGRATION_PROGRAM_ID = "39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg"
DEFAULT_OUTPUT_PATH = Path("data/events.jsonl")
DEFAULT_MIGRATION_OUTPUT_PATH = Path("data/migration_events.jsonl")
DEFAULT_SNAPSHOT_OUTPUT_PATH = Path("data/snapshots.jsonl")
DEFAULT_COMMITMENT = "processed"
DEFAULT_SOURCE = "pumpfun.logs"
DEFAULT_MIGRATION_SOURCE = "pumpfun.migration_logs"
RECONNECT_BACKOFF_SECONDS = 5


@dataclass(frozen=True, slots=True)
class StorageConfig:
    output_path: Path
    migration_output_path: Path
    snapshot_output_path: Path = DEFAULT_SNAPSHOT_OUTPUT_PATH


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    solana_node_wss_endpoint: str
    output_path: Path
    migration_output_path: Path
    pump_program_id: str = PUMP_FUN_PROGRAM_ID
    migration_program_id: str = PUMP_FUN_MIGRATION_PROGRAM_ID
    commitment: str = DEFAULT_COMMITMENT
    source: str = DEFAULT_SOURCE
    migration_source: str = DEFAULT_MIGRATION_SOURCE
    reconnect_backoff_seconds: int = RECONNECT_BACKOFF_SECONDS


def load_storage_config() -> StorageConfig:
    load_dotenv()

    output_path_value = os.getenv(
        "COLLECTOR_OUTPUT_PATH",
        str(DEFAULT_OUTPUT_PATH),
    ).strip()
    if not output_path_value:
        raise RuntimeError("COLLECTOR_OUTPUT_PATH cannot be empty")

    migration_output_path_value = os.getenv(
        "COLLECTOR_MIGRATION_OUTPUT_PATH",
        str(DEFAULT_MIGRATION_OUTPUT_PATH),
    ).strip()
    if not migration_output_path_value:
        raise RuntimeError("COLLECTOR_MIGRATION_OUTPUT_PATH cannot be empty")

    return StorageConfig(
        output_path=Path(output_path_value),
        migration_output_path=Path(migration_output_path_value),
    )


def load_config() -> CollectorConfig:
    storage_config = load_storage_config()

    solana_node_wss_endpoint = os.getenv("SOLANA_NODE_WSS_ENDPOINT", "").strip()
    if not solana_node_wss_endpoint:
        raise RuntimeError(
            "Missing required environment variable: SOLANA_NODE_WSS_ENDPOINT"
        )

    return CollectorConfig(
        solana_node_wss_endpoint=solana_node_wss_endpoint,
        output_path=storage_config.output_path,
        migration_output_path=storage_config.migration_output_path,
    )
