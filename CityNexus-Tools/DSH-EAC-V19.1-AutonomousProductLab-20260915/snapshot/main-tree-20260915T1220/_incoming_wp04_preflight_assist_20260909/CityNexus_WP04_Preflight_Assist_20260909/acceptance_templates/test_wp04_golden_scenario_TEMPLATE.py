"""Template acceptance test to activate only after WP03 repair + WP04 endpoints exist.

Codex: copy/adapt into backend/tests. Keep it endpoint-level and deterministic.
Do not weaken assertions to make it pass.
"""
from __future__ import annotations


def _find_river_cruise(plans: list[dict]) -> tuple[dict, dict]:
    for plan in plans:
        for activity in plan.get('activities', []):
            if activity.get('place_id') == 'place-river-cruise':
                return plan, activity
    raise AssertionError('canonical River Cruise activity was not generated')


def test_wp04_golden_booking_payment_and_replay(client, source_strength_codes):
    reset = client.post('/api/v1/demo/reset')
    assert reset.status_code == 200
    journey_id = reset.json()['journey_id']

    generated = client.post(f'/api/v1/journeys/{journey_id}/plans/generate', json={'candidate_count': 3})
    assert generated.status_code == 201
    plan, cruise = _find_river_cruise(generated.json())

    selected = client.post(f"/api/v1/journeys/{journey_id}/plans/{plan['id']}/select")
    assert selected.status_code == 200
    assert selected.json()['status'] == 'PLANNED'

    # The selected plan must expose the same Activity ID; re-read it to avoid stale assumptions.
    plan_read = client.get(f"/api/v1/plans/{plan['id']}")
    assert plan_read.status_code == 200
    _, cruise = _find_river_cruise([plan_read.json()])
    assert cruise['start_at'] == '2026-10-10T15:30:00+08:00'

    booking = client.post(
        f'/api/v1/journeys/{journey_id}/bookings',
        json={'activity_id': cruise['id'], 'provider_key': 'mock-booking'},
    )
    assert booking.status_code == 201
    booking_body = booking.json()
    assert booking_body['status'] == 'CONFIRMED'
    assert booking_body['commitment_id']
    assert booking_body['external_ref']

    key = 'wp04-golden-payment-0001'
    transaction_payload = {
        'booking_id': booking_body['id'],
        'order_id': None,
        'transaction_type': 'CAPTURE',
        'amount': booking_body['amount'],
        'provider_key': 'mock-payment',
    }
    paid = client.post(
        f'/api/v1/journeys/{journey_id}/transactions',
        json=transaction_payload,
        headers={'Idempotency-Key': key},
    )
    assert paid.status_code == 201
    tx = paid.json()
    assert tx['status'] == 'SUCCEEDED'
    assert tx['external_ref']

    # Replay must return the same logical transaction, never a second charge.
    replay = client.post(
        f'/api/v1/journeys/{journey_id}/transactions',
        json=transaction_payload,
        headers={'Idempotency-Key': key},
    )
    assert replay.status_code in {200, 201}
    assert replay.json()['id'] == tx['id']

    commitment = client.get(f"/api/v1/commitments/{booking_body['commitment_id']}")
    assert commitment.status_code == 200
    c = commitment.json()
    assert c['status'] == 'ACTIVE'
    assert c['level'] == source_strength_codes[4]
    assert c['policy']['semantic_key'] == 'place-river-cruise'
    assert c['policy']['scheduled_start_at'] == '2026-10-10T15:30:00+08:00'
    assert c['policy']['strength_rank'] == 4


def test_payment_failure_never_strengthens_commitment(client, canonical_confirmed_booking):
    # Implement fixture/provider injection so this uses FORCE_PAYMENT_FAIL without a real network.
    booking = canonical_confirmed_booking
    before = client.get(f"/api/v1/commitments/{booking['commitment_id']}").json()
    payload = {
        'booking_id': booking['id'],
        'transaction_type': 'CAPTURE',
        'amount': booking['amount'],
        'provider_key': 'mock-payment',
    }
    # Project test fixture selects the failure-configured mock provider here.
    response = client.post(
        f"/api/v1/journeys/{booking['journey_id']}/transactions",
        json=payload,
        headers={'Idempotency-Key': 'wp04-failure-payment-0001'},
    )
    assert response.status_code == 201
    assert response.json()['status'] == 'FAILED'
    after = client.get(f"/api/v1/commitments/{booking['commitment_id']}").json()
    assert after['level'] == before['level']
    assert after['policy']['strength_rank'] == before['policy']['strength_rank']
