# Deterministic Mock Provider Specification

## BookingProvider port

Required operations for IR-006:

```python
availability(service_id, date_or_window) -> normalized slots
create_booking(request) -> BookingProviderOutcome
cancel_booking(external_ref) -> BookingProviderOutcome
get_booking(external_ref) -> BookingProviderOutcome
```

Outcome contains only normalized non-secret facts:

```text
provider_key
status
external_ref
amount_minor
currency
cancellation_policy
provider_code/message
```

## PaymentProvider port

Required operations for IR-007:

```python
authorize(request) -> PaymentProviderOutcome
capture(request) -> PaymentProviderOutcome
refund(request) -> PaymentProviderOutcome
void(request) -> PaymentProviderOutcome
get_status(external_ref) -> PaymentProviderOutcome
```

No full card number, CVV, access token or provider secret exists in request/response fixtures.

## Deterministic behavior

The existing fixture declares:

```json
{
  "mock-booking": {
    "default": "CONFIRMED",
    "failure_token": "FORCE_BOOKING_FAIL"
  },
  "mock-payment": {
    "default_authorize": "AUTHORIZED",
    "default_capture": "SUCCEEDED",
    "failure_token": "FORCE_PAYMENT_FAIL"
  }
}
```

Use a constructor/test dependency or demo fixture mode to select forced failure. Do not use randomness.

Production-like API clients should not be able to forge `status=CONFIRMED/SUCCEEDED` in JSON. Provider outcome is adapter-owned.

## Provider call evidence

Every mock commerce call records one `provider_calls` row:

- provider_key
- operation
- request_json (redacted/minimal)
- response_json (normalised)
- SUCCESS/FAILURE
- deterministic latency may be null/0

A replayed idempotent payment must not create a second provider call.
