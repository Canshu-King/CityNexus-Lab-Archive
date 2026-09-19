from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Money(BaseModel):
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


class BookingSlot(BaseModel):
    start_at: datetime
    end_at: datetime
    provider_key: str
    provider_slot_ref: str


class BookingCreate(BaseModel):
    activity_id: UUID
    provider_key: str = 'mock-booking'


class Booking(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    journey_id: UUID
    activity_id: UUID | None
    commitment_id: UUID | None
    provider_key: str
    external_ref: str | None
    status: Literal['DRAFT', 'PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'FAILED']
    amount: Money
    cancellation_policy: dict


class OrderItemInput(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=1, le=99)


class OrderCreate(BaseModel):
    activity_id: UUID
    items: list[OrderItemInput] = Field(min_length=1, max_length=50)
    provider_key: str = 'mock-booking'


class Order(BaseModel):
    id: UUID
    journey_id: UUID
    activity_id: UUID | None
    commitment_id: UUID | None
    provider_key: str
    external_ref: str | None
    status: Literal['DRAFT', 'PENDING', 'CONFIRMED', 'FULFILLED', 'CANCELLED', 'FAILED']
    amount: Money
    items: list[OrderItemInput]


class TransactionCreate(BaseModel):
    booking_id: UUID | None = None
    order_id: UUID | None = None
    transaction_type: Literal['AUTHORIZE', 'CAPTURE', 'REFUND', 'VOID']
    amount: Money
    provider_key: str = 'mock-payment'

    @model_validator(mode='after')
    def exactly_one_target(self) -> 'TransactionCreate':
        if (self.booking_id is None) == (self.order_id is None):
            raise ValueError('exactly one of booking_id or order_id is required')
        return self


class Transaction(BaseModel):
    id: UUID
    journey_id: UUID
    booking_id: UUID | None
    order_id: UUID | None
    provider_key: str
    transaction_type: Literal['AUTHORIZE', 'CAPTURE', 'REFUND', 'VOID']
    status: Literal['INITIATED', 'AUTHORIZED', 'SUCCEEDED', 'FAILED', 'REFUNDED', 'VOIDED']
    amount: Money
    external_ref: str | None


class Commitment(BaseModel):
    id: UUID
    journey_id: UUID
    activity_id: UUID | None
    kind: Literal['BOOKING', 'ORDER', 'PAYMENT', 'APPOINTMENT', 'OTHER']
    # The exact five allowed source-domain codes MUST be injected from the frozen YAML.
    level: str
    status: Literal['PROPOSED', 'ACTIVE', 'FULFILLED', 'CANCELLED', 'BREACHED']
    monetary_value: Money
    external_ref: str | None
    policy: dict
