from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.outbox import Outbox


class OutboxRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session

    async def create(
        self,
        event: Outbox,
    ) -> Outbox:
        """
        Создает событие в outbox.
        Используется внутри общей транзакции с платежом.
        """
        self._session.add(event)

        await self._session.flush()

        return event

    async def get_pending_events(
        self,
        limit: int = 100,
    ) -> list[Outbox]:
        """
        Получает необработанные события.
        Используется publisher'ом.

        skip_locked позволяет нескольким publisher'ам
        забирать разные события параллельно.
        """
        stmt = (
            select(Outbox)
            .where(
                Outbox.published_at.is_(None),
                Outbox.attempts < settings.outbox_max_attempts,
            )
            .order_by(
                Outbox.created_at,
            )
            .limit(limit)
            .with_for_update(
                skip_locked=True,
            )
        )

        result = await self._session.execute(stmt)

        return list(result.scalars().all())

    async def mark_published(
        self,
        event_id: UUID,
    ) -> None:
        """
        Помечает событие как опубликованное.
        """
        stmt = (
            update(Outbox)
            .where(
                Outbox.id == event_id,
            )
            .values(
                published_at=func.now(),
            )
        )

        await self._session.execute(stmt)

    async def increment_attempts(
        self,
        event_id: UUID,
    ) -> None:
        """
        Увеличивает количество попыток публикации.
        """
        stmt = (
            update(Outbox)
            .where(
                Outbox.id == event_id,
            )
            .values(
                attempts=Outbox.attempts + 1,
            )
        )

        await self._session.execute(stmt)

    async def get_by_id(
        self,
        event_id: UUID,
    ) -> Outbox | None:
        """
        Получает событие по ID.
        """
        stmt = select(Outbox).where(
            Outbox.id == event_id,
        )

        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()