import asyncio
import logging
import random
import json

from typing import Any

from faststream.rabbit import RabbitMessage

from src.broker.rabbit import broker
from src.broker.topology import (
    payments_exchange,
    payments_queue,
)
from src.db.session import AsyncSessionLocal
from src.models.payment import PaymentStatus
from src.repositories.payment import PaymentRepository
from src.services.webhook import WebhookService


logger = logging.getLogger(__name__)


def get_retry_attempt(
    message: RabbitMessage,
) -> int:
    headers = message.headers or {}

    deaths = headers.get(
        "x-death",
        [],
    )

    if not deaths:
        return 0

    queue = deaths[0].get("queue")

    mapping = {
        "payments.retry.1": 1,
        "payments.retry.2": 2,
        "payments.retry.3": 3,
    }

    return mapping.get(
        queue,
        0,
    )


def get_failure_route(
    attempt: int,
) -> str:

    if attempt == 0:
        return "payment.retry.1"

    if attempt == 1:
        return "payment.retry.2"

    if attempt == 2:
        return "payment.retry.3"

    return "payment.dlq"


async def publish_failure(
    body: dict,
    routing_key: str,
) -> None:

    logger.warning(
        "Publishing retry message routing_key=%s body=%s",
        routing_key,
        body,
    )

    await broker.publish(
        message=body,
        exchange=payments_exchange,
        routing_key=routing_key,
    )

    logger.warning(
        "Retry message published routing_key=%s",
        routing_key,
    )


@broker.subscriber(
    payments_queue,
    exchange=payments_exchange,
)
async def process_payment(
    message: RabbitMessage,
):

    body: dict[str, Any] = json.loads(
        message.body.decode()
    )

    payment_id = body["payment_id"]

    logger.info(
        "Processing payment %s",
        payment_id,
    )

    async with AsyncSessionLocal() as session:

        repository = PaymentRepository(
            session
        )

        payment = await repository.get_by_id(
            payment_id,
        )

        if payment is None:

            logger.warning(
                "Payment %s not found",
                payment_id,
            )

            return


        if payment.status == PaymentStatus.SUCCEEDED:

            logger.info(
                "Payment %s already processed",
                payment_id,
            )

            return

        await asyncio.sleep(
            random.randint(2, 5)
        )

        if random.random() < 0.1:

            attempt = get_retry_attempt(
                message,
            )

            logger.warning(
                "Payment %s failed. Attempt %s",
                payment_id,
                attempt + 1,
            )


            routing_key = get_failure_route(
                attempt,
            )

            if routing_key == "payment.dlq":

                await repository.update_status(
                    payment,
                    PaymentStatus.FAILED,
                )

                await session.commit()


                await publish_failure(
                    body,
                    routing_key,
                )


                logger.error(
                    "Payment %s moved to DLQ",
                    payment_id,
                )

                return

            await publish_failure(
                body,
                routing_key,
            )


            logger.info(
                "Payment %s sent to retry queue %s",
                payment_id,
                routing_key,
            )


            return

        await repository.update_status(
            payment,
            PaymentStatus.SUCCEEDED,
        )

        await session.commit()


        logger.info(
            "Payment %s processed successfully",
            payment_id,
        )


        webhook_service = WebhookService()


        try:

            await webhook_service.send(
                url=str(payment.webhook_url),
                payload={
                    "payment_id": str(payment.id),
                    "status": payment.status.value,
                },
            )


            logger.info(
                "Webhook sent successfully for payment %s",
                payment_id,
            )


        except Exception:

            logger.exception(
                "Webhook failed for payment %s",
                payment_id,
            )