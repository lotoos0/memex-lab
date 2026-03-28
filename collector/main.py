from __future__ import annotations

import asyncio
import logging

from collector.config import load_config
from collector.listeners.pumpfun_logs import PumpFunLogsListener
from collector.storage.jsonl_writer import JsonlWriter


async def run() -> None:
    config = load_config()
    writer = JsonlWriter(config.output_path)
    listener = PumpFunLogsListener(config=config, writer=writer)
    await listener.listen_forever()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Collector stopped by user")


if __name__ == "__main__":
    main()
