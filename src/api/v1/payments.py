from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.dependencies import get_payment_service
from src.schemas.payment import (
    PaymentCreate,
    PaymentCreateResponse,
    PaymentDetailResponse,
)
from src.services.payment import PaymentService


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_payment(
    data: PaymentCreate,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
    ),
    service: PaymentService = Depends(get_payment_service),
):
    payment = await service.create(
        data=data,
        idempotency_key=idempotency_key,
    )

    return PaymentCreateResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailResponse,
)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
):
    payment = await service.get(payment_id)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return PaymentDetailResponse(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        payment_metadata=payment.payment_metadata,
        created_at=payment.created_at,
    )