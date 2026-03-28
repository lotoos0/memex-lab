from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import websockets

from collector.config import CollectorConfig
from collector.parsers.create_event import CREATE_INSTRUCTION_NAMES, parse_create_event
from collector.storage.jsonl_writer import JsonlWriter

logger = logging.getLogger(__name__)

INSTRUCTION_LOG_PREFIX = "Program log: Instruction: "
PROGRAM_DATA_LOG_PREFIX = "Program data: "


class PumpFunLogsListener:
    def __init__(self, config: CollectorConfig, writer: JsonlWriter):
        self._config = config
        self._writer = writer

    async def listen_forever(self) -> None:
        while True:
            try:
                await self._listen_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Pump.fun log listener disconnected")

            logger.info(
                "Reconnecting websocket in %s seconds",
                self._config.reconnect_backoff_seconds,
            )
            await asyncio.sleep(self._config.reconnect_backoff_seconds)

    async def _listen_once(self) -> None:
        logger.info(
            "Connecting to %s for pump.fun program %s",
            self._config.solana_node_wss_endpoint,
            self._config.pump_program_id,
        )

        async with websockets.connect(
            self._config.solana_node_wss_endpoint
        ) as websocket:
            await websocket.send(json.dumps(self._build_subscription_request()))
            subscription_response = json.loads(await websocket.recv())

            if "error" in subscription_response:
                raise RuntimeError(
                    f"Subscription failed: {subscription_response['error']}"
                )

            logger.info(
                "Subscribed to pump.fun logs with subscription id %s",
                subscription_response.get("result"),
            )

            async for message in websocket:
                self._handle_message(message)

    def _build_subscription_request(self) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {"mentions": [self._config.pump_program_id]},
                {"commitment": self._config.commitment},
            ],
        }

    def _handle_message(self, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError as error:
            logger.warning("Skipping non-JSON websocket message: %s", error)
            return

        if payload.get("method") != "logsNotification":
            return

        result = payload.get("params", {}).get("result", {})
        value = result.get("value", {})
        logs = value.get("logs", [])
        if not isinstance(logs, list):
            logger.warning("Skipping notification with invalid logs payload")
            return

        instruction_name = _extract_create_instruction_name(logs)
        if instruction_name is None:
            return

        signature = value.get("signature")
        slot = _read_slot(result.get("context", {}))

        found_event = False
        for log_line in logs:
            if not isinstance(log_line, str) or not log_line.startswith(
                PROGRAM_DATA_LOG_PREFIX
            ):
                continue

            encoded_data = log_line.split(PROGRAM_DATA_LOG_PREFIX, 1)[1].strip()
            event = parse_create_event(
                encoded_data=encoded_data,
                source=self._config.source,
                signature=signature if isinstance(signature, str) else None,
                slot=slot,
                instruction_name=instruction_name,
                logs=logs,
            )

            if event is None:
                continue

            self._writer.write_event(event)
            logger.info("Stored token creation event for mint %s", event.mint)
            found_event = True
            break

        if not found_event:
            logger.warning(
                "Create instruction detected but no CreateEvent was parsed for signature %s",
                signature,
            )


def _extract_create_instruction_name(logs: list[str]) -> str | None:
    for log_line in logs:
        if not isinstance(log_line, str) or not log_line.startswith(
            INSTRUCTION_LOG_PREFIX
        ):
            continue

        instruction_name = log_line.split(INSTRUCTION_LOG_PREFIX, 1)[1].strip()
        if instruction_name in CREATE_INSTRUCTION_NAMES:
            return instruction_name

    return None


def _read_slot(context: Any) -> int | None:
    if not isinstance(context, dict):
        return None

    slot = context.get("slot")
    return slot if isinstance(slot, int) else None
