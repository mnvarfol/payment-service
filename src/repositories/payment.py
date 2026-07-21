from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session

    async def create(
        self,
        payment: Payment,
    ) -> Payment:
        """
        Добавляет платеж в текущую транзакцию.
        Commit выполняется на уровне сервиса.
        """
        self._session.add(payment)

        await self._session.flush()
        await self._session.refresh(payment)

        return payment

    async def get_by_id(
        self,
        payment_id: UUID,
    ) -> Payment | None:
        """
        Получение платежа по идентификатору.
        """
        stmt = select(Payment).where(
            Payment.id == payment_id,
        )

        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Payment | None:
        """
        Получение платежа по ключу идемпотентности.
        """
        stmt = select(Payment).where(
            Payment.idempotency_key == idempotency_key,
        )

        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()
    

    async def update_status(
        self,
        payment: Payment,
        status: PaymentStatus,
    ) -> Payment:

        payment.status = status

        await self._session.flush()

        return payment