import asyncio
import logging

from src.publisher.publisher import publish_outbox_events


logger = logging.getLogger(__name__)


async def outbox_publisher_loop() -> None:
    while True:
        try:
            await publish_outbox_events()

        except Exception:
            logger.exception(
                "Outbox publishing failed",
            )

        await asyncio.sleep(5)