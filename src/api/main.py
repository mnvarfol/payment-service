import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from src.broker.rabbit import broker
from src.publisher.worker import outbox_publisher_loop

from src.api.v1.payments import router as payments_router
from src.exceptions import PaymentCreationError
from src.api.handlers import payment_creation_error_handler
from src.broker.topology import (
    payments_exchange,
    payments_queue,
    payments_retry_queue_1,
    payments_retry_queue_2,
    payments_retry_queue_3,
    payments_dlq,
)
from src.api.dependencies import verify_api_key


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    await broker.start()

    logger.info("RabbitMQ broker started")

    exchange = await broker.declare_exchange(
        payments_exchange
    )

    payments = await broker.declare_queue(
        payments_queue
    )

    retry1 = await broker.declare_queue(
        payments_retry_queue_1
    )

    retry2 = await broker.declare_queue(
        payments_retry_queue_2
    )

    retry3 = await broker.declare_queue(
        payments_retry_queue_3
    )

    dlq = await broker.declare_queue(
        payments_dlq
    )

    await payments.bind(
        exchange,
        routing_key="payment.created",
    )

    await retry1.bind(
        exchange,
        routing_key="payment.retry.1",
    )

    await retry2.bind(
        exchange,
        routing_key="payment.retry.2",
    )

    await retry3.bind(
        exchange,
        routing_key="payment.retry.3",
    )

    await dlq.bind(
        exchange,
        routing_key="payment.dlq",
    )

    publisher_task = asyncio.create_task(
        outbox_publisher_loop()
    )

    logger.info("Outbox publisher started")

    yield

    publisher_task.cancel()

    try:
        await publisher_task
    except asyncio.CancelledError:
        pass

    await broker.stop()

    logger.info("Application stopped")


app = FastAPI(
    title="Payment Service",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[
        Depends(verify_api_key),
    ],
)

app.add_exception_handler(
    PaymentCreationError,
    payment_creation_error_handler,
)

app.include_router(
    payments_router,
    prefix="/api/v1",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }