from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import Base


class Commitment(Base):
    __tablename__ = 'commitments'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey('journeys.id', ondelete='CASCADE'))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey('activities.id', ondelete='SET NULL'), nullable=True
    )
    kind: Mapped[str] = mapped_column(String)
    level: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    monetary_value_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    policy_json: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Booking(Base):
    __tablename__ = 'bookings'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey('journeys.id', ondelete='CASCADE'))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey('activities.id', ondelete='SET NULL'), nullable=True
    )
    commitment_id: Mapped[str | None] = mapped_column(
        ForeignKey('commitments.id', ondelete='SET NULL'), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    cancellation_policy_json: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey('journeys.id', ondelete='CASCADE'))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey('activities.id', ondelete='SET NULL'), nullable=True
    )
    commitment_id: Mapped[str | None] = mapped_column(
        ForeignKey('commitments.id', ondelete='SET NULL'), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    items_json: Mapped[str] = mapped_column(Text, default='[]')
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class PaymentTransaction(Base):
    __tablename__ = 'transactions'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey('journeys.id', ondelete='CASCADE'))
    booking_id: Mapped[str | None] = mapped_column(
        ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey('orders.id', ondelete='SET NULL'), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String)
    transaction_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_payload_json: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint('provider_key', 'idempotency_key'),)


class ProviderCall(Base):
    __tablename__ = 'provider_calls'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    operation: Mapped[str] = mapped_column(String)
    request_json: Mapped[str] = mapped_column(Text)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String)


class IdempotencyKey(Base):
    __tablename__ = 'idempotency_keys'
    key: Mapped[str] = mapped_column(String, primary_key=True)
    operation: Mapped[str] = mapped_column(String)
    request_hash: Mapped[str] = mapped_column(Text)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String)
