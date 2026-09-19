from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Callable, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.commerce.commitment_policy import CommitmentFacts, derive_strength_rank, source_strength_code
from app.commerce.idempotency import IdempotencyConflict, canonical_request_signature
from app.commerce.order_pricing import OrderLineRequest, price_order
from app.commerce.validators import (
    BookingTargetContext,
    CommerceValidationError,
    PaymentTargetContext,
    stable_semantic_key,
    validate_booking_target,
    validate_idempotency_key,
    validate_payment_target,
    validate_transaction_target_ids,
)
from app.core.audit import record_audit
from app.db.models import Activity, Journey, PlanVersion
from app.db.models import Booking, Commitment, IdempotencyKey, Order, PaymentTransaction, ProviderCall
from app.integrations.commerce_ports import BookingProvider, PaymentProvider


class CommerceConflict(ValueError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _provider_call(session: Session, *, provider_key: str, operation: str, request: dict, response: dict, ok: bool) -> None:
    session.add(
        ProviderCall(
            id=str(uuid4()),
            provider_key=provider_key,
            operation=operation,
            request_json=dump(request),
            response_json=dump(response),
            status='SUCCESS' if ok else 'FAILURE',
            latency_ms=0,
            created_at=now_iso(),
        )
    )


def selected_activity(session: Session, journey_id: str, activity_id: str) -> tuple[Journey, PlanVersion, Activity, BookingTargetContext]:
    journey = session.get(Journey, journey_id)
    if journey is None:
        raise CommerceValidationError('Journey not found')
    if not journey.active_plan_version_id:
        raise CommerceValidationError('Journey has no selected plan')
    plan = session.get(PlanVersion, journey.active_plan_version_id)
    if plan is None or plan.journey_id != journey.id:
        raise CommerceValidationError('selected PlanVersion is missing/inconsistent')
    activity = session.get(Activity, activity_id)
    if activity is None:
        raise CommerceValidationError('Activity not found')
    context = BookingTargetContext(
        journey_id=journey.id,
        journey_status=journey.status,
        selected_plan_id=journey.active_plan_version_id,
        selected_plan_status=plan.status,
        activity_id=activity.id,
        activity_plan_id=activity.plan_version_id,
        activity_status=activity.status,
        activity_place_id=activity.place_id,
        activity_service_id=activity.city_service_id,
    )
    validate_booking_target(context)
    return journey, plan, activity, context


def create_booking(
    session: Session,
    *,
    journey_id: str,
    activity_id: str,
    provider: BookingProvider,
    source_strength_codes: Sequence[str],
    booking_source_type_code: str,
    assert_selected_plan_feasible: Callable[[Session, Journey, PlanVersion], None] | None = None,
    force_failure: bool = False,
) -> Booking:
    journey, plan, activity, context = selected_activity(session, journey_id, activity_id)
    if assert_selected_plan_feasible:
        assert_selected_plan_feasible(session, journey, plan)

    booking_id = str(uuid4())
    request = {
        'merchant_reference': booking_id,
        'activity_id': activity.id,
        'amount_minor': activity.estimated_cost_minor,
        'currency': activity.currency,
    }
    outcome = provider.create_booking(**request, force_failure=force_failure)
    response = {
        'status': outcome.status,
        'external_ref': outcome.external_ref,
        'amount_minor': outcome.amount_minor,
        'currency': outcome.currency,
        'cancellation_policy': outcome.cancellation_policy,
        'provider_code': outcome.provider_code,
    }
    _provider_call(
        session,
        provider_key=outcome.provider_key,
        operation='booking.create',
        request=request,
        response=response,
        ok=outcome.status == 'CONFIRMED',
    )

    now = now_iso()
    commitment_id: str | None = None
    if outcome.status == 'CONFIRMED':
        semantic = stable_semantic_key(context)
        decision = derive_strength_rank(
            CommitmentFacts(
                provider_confirmed=True,
                payment_succeeded=False,
                fixed_schedule=bool(activity.locked),
                user_locked=bool(activity.locked),
                cancellation_loss_minor=int(outcome.cancellation_policy.get('loss_minor', 0)),
                easily_replaceable=not bool(activity.locked),
            )
        )
        commitment_id = str(uuid4())
        policy = {
            'semantic_key': semantic,
            'scheduled_start_at': activity.start_at,
            'scheduled_end_at': activity.end_at,
            'fixed_schedule': bool(activity.locked),
            'user_locked': bool(activity.locked),
            'easily_replaceable': not bool(activity.locked),
            'strength_rank': decision.rank,
            'strength_reasons': list(decision.reasons),
            'source_type': booking_source_type_code,
            'source_refs': {'booking_external_ref': outcome.external_ref},
        }
        session.add(
            Commitment(
                id=commitment_id,
                journey_id=journey.id,
                activity_id=activity.id,
                kind='BOOKING',
                level=source_strength_code(decision.rank, source_strength_codes),
                status='ACTIVE',
                monetary_value_minor=activity.estimated_cost_minor,
                currency=activity.currency,
                external_ref=outcome.external_ref,
                policy_json=dump(policy),
                created_at=now,
                updated_at=now,
            )
        )
        # No ORM relationship is required for the MVP models, so flush the FK target
        # before inserting Booking(commitment_id=...).
        session.flush()

    booking = Booking(
        id=booking_id,
        journey_id=journey.id,
        activity_id=activity.id,
        commitment_id=commitment_id,
        provider_key=outcome.provider_key,
        external_ref=outcome.external_ref,
        status=outcome.status,
        amount_minor=outcome.amount_minor,
        currency=outcome.currency,
        cancellation_policy_json=dump(outcome.cancellation_policy),
        created_at=now,
        updated_at=now,
    )
    session.add(booking)
    record_audit(
        session,
        action='booking.created',
        entity_type='Booking',
        entity_id=booking.id,
        journey_id=journey.id,
        after={'status': booking.status, 'external_ref': booking.external_ref},
    )
    session.flush()
    return booking


def create_order(
    session: Session,
    *,
    journey_id: str,
    activity_id: str,
    service_id: str,
    items: list[OrderLineRequest],
    catalog: dict,
    source_strength_codes: Sequence[str],
    order_source_type_code: str,
) -> Order:
    journey, _plan, activity, context = selected_activity(session, journey_id, activity_id)
    semantic = stable_semantic_key(context)
    priced = price_order(service_id=service_id, requests=items, catalog=catalog)
    now = now_iso()
    order_id = str(uuid4())
    commitment_id = str(uuid4())
    decision = derive_strength_rank(CommitmentFacts(provider_confirmed=True, easily_replaceable=True))
    policy = {
        'semantic_key': semantic,
        'scheduled_start_at': activity.start_at,
        'scheduled_end_at': activity.end_at,
        'fixed_schedule': bool(activity.locked),
        'strength_rank': decision.rank,
        'strength_reasons': list(decision.reasons),
        'source_type': order_source_type_code,
        'source_refs': {'order_id': order_id},
    }
    session.add(
        Commitment(
            id=commitment_id,
            journey_id=journey.id,
            activity_id=activity.id,
            kind='ORDER',
            level=source_strength_code(decision.rank, source_strength_codes),
            status='ACTIVE',
            monetary_value_minor=priced.total_minor,
            currency=priced.currency,
            external_ref=f'mock-order:{order_id}',
            policy_json=dump(policy),
            created_at=now,
            updated_at=now,
        )
    )
    session.flush()
    order = Order(
        id=order_id,
        journey_id=journey.id,
        activity_id=activity.id,
        commitment_id=commitment_id,
        provider_key='mock-order',
        external_ref=f'mock-order:{order_id}:confirmed',
        status='CONFIRMED',
        amount_minor=priced.total_minor,
        currency=priced.currency,
        items_json=dump([line.__dict__ for line in priced.lines]),
        created_at=now,
        updated_at=now,
    )
    session.add(order)
    record_audit(
        session,
        action='order.created',
        entity_type='Order',
        entity_id=order.id,
        journey_id=journey.id,
        after={'status': order.status, 'amount_minor': order.amount_minor, 'currency': order.currency},
    )
    session.flush()
    return order


def create_capture_transaction(
    session: Session,
    *,
    journey_id: str,
    booking_id: str | None,
    order_id: str | None,
    requested_amount_minor: int,
    requested_currency: str,
    provider: PaymentProvider,
    idempotency_key: str,
    source_strength_codes: Sequence[str],
    force_failure: bool = False,
) -> PaymentTransaction:
    validate_transaction_target_ids(booking_id=booking_id, order_id=order_id)
    header_key = validate_idempotency_key(idempotency_key)
    scoped_key = f'transaction.create:{provider.provider_key}:{header_key}'

    booking = session.get(Booking, booking_id) if booking_id else None
    order = session.get(Order, order_id) if order_id else None
    target = booking or order
    if target is None:
        raise CommerceValidationError('payment target not found')
    validate_payment_target(
        PaymentTargetContext(
            journey_id=journey_id,
            target_journey_id=target.journey_id,
            authoritative_amount_minor=target.amount_minor,
            authoritative_currency=target.currency,
            target_status=target.status,
        ),
        requested_amount_minor=requested_amount_minor,
        requested_currency=requested_currency,
    )

    semantic_payload = {
        'journey_id': journey_id,
        'provider_key': provider.provider_key,
        'booking_id': booking_id,
        'order_id': order_id,
        'transaction_type': 'CAPTURE',
        'amount_minor': requested_amount_minor,
        'currency': requested_currency.upper(),
    }
    signature = canonical_request_signature(semantic_payload)
    existing = session.get(IdempotencyKey, scoped_key)
    if existing:
        if existing.request_hash != signature:
            raise IdempotencyConflict('same idempotency key used for a different request')
        stored = json.loads(existing.response_json or '{}')
        transaction_id = stored.get('transaction_id')
        transaction = session.get(PaymentTransaction, transaction_id) if transaction_id else None
        if transaction is None:
            raise CommerceConflict('idempotency record points to a missing transaction')
        return transaction

    transaction_id = str(uuid4())
    request = {
        'merchant_reference': transaction_id,
        'amount_minor': requested_amount_minor,
        'currency': requested_currency.upper(),
    }
    outcome = provider.capture(**request, force_failure=force_failure)
    response = {
        'status': outcome.status,
        'external_ref': outcome.external_ref,
        'provider_code': outcome.provider_code,
    }
    _provider_call(
        session,
        provider_key=provider.provider_key,
        operation='payment.capture',
        request=request,
        response=response,
        ok=outcome.status == 'SUCCEEDED',
    )
    now = now_iso()
    tx = PaymentTransaction(
        id=transaction_id,
        journey_id=journey_id,
        booking_id=booking_id,
        order_id=order_id,
        provider_key=provider.provider_key,
        idempotency_key=header_key,
        transaction_type='CAPTURE',
        status=outcome.status,
        amount_minor=requested_amount_minor,
        currency=requested_currency.upper(),
        external_ref=outcome.external_ref,
        provider_payload_json=dump({'provider_code': outcome.provider_code}),
        created_at=now,
        updated_at=now,
    )
    session.add(tx)

    commitment_id = target.commitment_id
    if outcome.status == 'SUCCEEDED' and commitment_id:
        commitment = session.get(Commitment, commitment_id)
        if commitment is None:
            raise CommerceConflict('target commitment is missing')
        policy = json.loads(commitment.policy_json or '{}')
        facts = CommitmentFacts(
            provider_confirmed=True,
            payment_succeeded=True,
            fixed_schedule=bool(policy.get('fixed_schedule')),
            user_locked=bool(policy.get('user_locked')),
            cancellation_loss_minor=max(int(commitment.monetary_value_minor), 0),
            easily_replaceable=bool(policy.get('easily_replaceable', True)),
        )
        decision = derive_strength_rank(facts)
        old_rank = int(policy.get('strength_rank', 0))
        new_rank = max(old_rank, decision.rank)
        source_refs = dict(policy.get('source_refs') or {})
        source_refs.update(
            {
                'payment_transaction_id': tx.id,
                'payment_external_ref': outcome.external_ref,
            }
        )
        policy.update(
            {
                'strength_rank': new_rank,
                'strength_reasons': list(decision.reasons),
                'source_refs': source_refs,
            }
        )
        commitment.level = source_strength_code(new_rank, source_strength_codes)
        commitment.external_ref = outcome.external_ref or commitment.external_ref
        commitment.policy_json = dump(policy)
        commitment.updated_at = now

    session.add(
        IdempotencyKey(
            key=scoped_key,
            operation='transaction.create',
            request_hash=signature,  # legacy column name; stores canonical request signature
            response_status=201,
            response_json=dump({'transaction_id': tx.id, 'status': tx.status}),
            created_at=now,
            expires_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        )
    )
    record_audit(
        session,
        action='payment.capture.succeeded' if tx.status == 'SUCCEEDED' else 'payment.capture.failed',
        entity_type='PaymentTransaction',
        entity_id=tx.id,
        journey_id=journey_id,
        after={'status': tx.status, 'external_ref': tx.external_ref},
    )
    session.flush()
    return tx
