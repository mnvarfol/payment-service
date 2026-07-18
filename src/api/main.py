import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.broker.rabbit import broker
from src.publisher.worker import outbox_publisher_loop

from src.api.v1.payments import router as payments_router
from src.exceptions import PaymentCreationError
from src.api.handlers import payment_creation_error_handler
from src.broker.topology import payments_exchange


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    await broker.start()

    logger.info("RabbitMQ broker started")

    await broker.declare_exchange(
        payments_exchange
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