from fastapi import FastAPI

from src.api.v1.payments import router as payments_router
from src.exceptions import PaymentCreationError
from src.api.handlers import payment_creation_error_handler


app = FastAPI(
    title="Payment Service",
    version="1.0.0",
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