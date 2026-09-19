# WP04 Architecture — Booking, Order, Payment, Commitment

## Goal

Turn a selected feasible Journey plan into deterministic local commerce records without real payment risk or internet dependency.

Canonical chain:

```text
Journey PLANNED
  -> SELECTED PlanVersion
  -> selected Activity (River Cruise 15:30)
  -> MockBookingProvider.create
  -> provider-confirmed Booking
  -> ACTIVE Commitment created/strengthened
  -> MockPaymentProvider.capture
  -> SUCCEEDED PaymentTransaction
  -> same Commitment strengthened by deterministic policy
  -> canonical fixed paid cruise reaches source C4 Anchored / MVP LOCKED behavior
```

## Module boundaries

```text
API route
  -> application commerce service
      -> precondition/ownership validation
      -> provider port
      -> deterministic mock adapter
      -> provider-call record
      -> domain transition/policy
      -> persistence transaction
      -> audit event
```

Provider adapters do not write domain tables directly. API routes do not contain provider/domain transition logic.

## New application modules

Recommended:

```text
backend/app/commerce/
  service.py                # orchestration
  commitment_policy.py     # pure strength derivation
  idempotency.py            # replay/conflict semantics
  validators.py             # ownership/state/amount guards

backend/app/integrations/
  commerce_ports.py
  mock/commerce_providers.py
```

Existing `services.py` may keep schema conversion helpers, but avoid turning it into another thousand-line kitchen drawer.

## Transaction boundaries

### Booking create

1. Validate Journey is PLANNED with selected plan.
2. Validate Activity belongs to selected PlanVersion/Journey.
3. Call deterministic booking provider.
4. Record provider call outcome.
5. In one DB transaction persist Booking + Commitment effect + audit.

Provider rejection may still persist a `FAILED` Booking attempt, but it must not create an ACTIVE confirmed commitment.

### Payment create

1. Resolve idempotency key before provider call.
2. Validate exactly one target: booking XOR order.
3. Validate target belongs to Journey.
4. Validate amount/currency against target.
5. Call mock payment provider exactly once for a new idempotency request.
6. Persist PaymentTransaction and provider call.
7. If CAPTURE succeeds, strengthen associated Commitment in the **same DB transaction**.
8. Persist idempotency replay record and audit.

Same idempotency key + same semantic request must never call provider twice or create a duplicate charge/transaction.
Same key + different semantic request returns 409 before provider call.

## No-network rule

WP04 is fixture-backed. No Stripe/PayPal/real booking API, no secret, no card credential, no HTTP call. Provider interfaces must remain replaceable later.
