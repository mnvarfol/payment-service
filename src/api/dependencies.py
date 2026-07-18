from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.services.payment import PaymentService


def get_payment_service(
    session: AsyncSession = Depends(get_session),
) -> PaymentService:
    return PaymentService(session)