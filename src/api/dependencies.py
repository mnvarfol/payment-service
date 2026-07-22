from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dependencies import get_session
from src.services.payment import PaymentService
from src.config import settings


def get_payment_service(
    session: AsyncSession = Depends(get_session),
) -> PaymentService:
    return PaymentService(session)


async def verify_api_key(
    x_api_key: str = Header(alias="X-API-Key"),
) -> None:

    if x_api_key != settings.api_key.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )