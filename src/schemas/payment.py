from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field
from annotated_types import Len, Gt

from src.models.payment import Currency, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Annotated[
        Decimal,
        Gt(Decimal("0")),
    ]

    currency: Currency

    description: Annotated[
        str | None,
        Len(max_length=500),
    ] = None

    payment_metadata: dict = Field(
        default_factory=dict,
    )

    webhook_url: AnyHttpUrl


class PaymentCreateResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentDetailResponse(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str | None
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    payment_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)