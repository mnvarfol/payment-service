from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def get_unpublished_events(
        self,
        limit: int = 100,
    ) -> list[Outbox]:
        """
        Получает события, которые еще не были опубликованы в брокер.

        Используется outbox publisher'ом для выборки пачки событий,
        ожидающих доставки.
        """
        stmt = (
            select(Outbox)
            .where(
                Outbox.published_at.is_(None),
            )
            .order_by(
                Outbox.created_at,
            )
            .limit(limit)
        )

        result = await self._session.execute(stmt)

        return list(result.scalars().all())