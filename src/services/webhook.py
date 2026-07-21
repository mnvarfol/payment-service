import logging

import httpx


logger = logging.getLogger(__name__)


class WebhookService:

    async def send(
        self,
        url: str,
        payload: dict,
    ) -> None:

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=5,
            )

            response.raise_for_status()

            logger.info(
                "Webhook sent successfully: %s",
                url,
            )