import logging
from datetime import datetime, timezone

from src.broker.rabbit import broker
from src.broker.topology import payments_exchange
from src.db.session import AsyncSessionLocal
from src.repositories.outbox import OutboxRepository


logger = logging.getLogger(__name__)


async def publish_outbox_events() -> None:
    async with AsyncSessionLocal() as session:
        repository = OutboxRepository(session)

        events = await repository.get_unpublished_events()

        for event in events:
            try:
                await broker.publish(
                    message=event.payload,
                    exchange=payments_exchange,
                    routing_key=event.event_type,
                )

                event.published_at = datetime.now(
                    timezone.utc,
                )

            except Exception:
                logger.exception(
                    "Failed to publish event %s",
                    event.id,
                )

        await session.commit()