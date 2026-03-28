from __future__ import annotations

import asyncio
import logging

from collector.config import load_config
from collector.listeners.migration_logs import MigrationLogsListener
from collector.listeners.pumpfun_logs import PumpFunLogsListener
from collector.storage.jsonl_writer import JsonlWriter


async def run() -> None:
    config = load_config()
    create_writer = JsonlWriter(config.output_path)
    migration_writer = JsonlWriter(config.migration_output_path)
    create_listener = PumpFunLogsListener(config=config, writer=create_writer)
    migration_listener = MigrationLogsListener(
        config=config,
        writer=migration_writer,
    )
    await asyncio.gather(
        create_listener.listen_forever(),
        migration_listener.listen_forever(),
    )


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
