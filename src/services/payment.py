from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import PaymentCreationError
from src.models.outbox import Outbox
from src.models.payment import Payment, PaymentStatus
from src.repositories.outbox import OutboxRepository
from src.repositories.payment import PaymentRepository
from src.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session
        self._payment_repository = PaymentRepository(session)
        self._outbox_repository = OutboxRepository(session)

    async def create(
        self,
        data: PaymentCreate,
        idempotency_key: str,
    ) -> Payment:
        """
        Создание платежа.

        Логика:
        1. Создаем платеж.
        2. Создаем событие payment.created в outbox.
        3. Фиксируем обе записи одной транзакцией.
        4. При конфликте idempotency_key возвращаем существующий платеж.
        """

        try:
            payment = Payment(
                amount=data.amount,
                currency=data.currency,
                description=data.description,
                payment_metadata=data.payment_metadata,
                status=PaymentStatus.PENDING,
                idempotency_key=idempotency_key,
                webhook_url=str(data.webhook_url),
            )

            payment = await self._payment_repository.create(payment)

            event = Outbox(
                event_type="payment.created",
                aggregate_id=payment.id,
                payload={
                    "payment_id": str(payment.id),
                    "amount": str(payment.amount),
                    "currency": payment.currency.value,
                    "webhook_url": payment.webhook_url,
                },
            )

            await self._outbox_repository.create(event)

            await self._session.commit()

            return payment

        except IntegrityError as exc:
            await self._session.rollback()

            existing_payment = (
                await self._payment_repository.get_by_idempotency_key(
                    idempotency_key,
                )
            )

            if existing_payment is not None:
                return existing_payment

            raise PaymentCreationError(
                "Failed to create payment",
            ) from exc

    async def get(
        self,
        payment_id: UUID,
    ) -> Payment | None:
        """
        Получение платежа по ID.
        """

        return await self._payment_repository.get_by_id(payment_id)