from fastapi import Request
from fastapi.responses import JSONResponse


async def payment_creation_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
        },
    )