# WP04 Schema / ORM Delta

## Current SQL tables already available

- commitments
- bookings
- orders
- transactions
- provider_calls
- idempotency_keys

This is useful: WP04 should not invent duplicate commerce tables.

## ORM work required

The current WP03 ORM file does not define these six tables. Add SQLAlchemy models aligned with the existing SQL contract:

- `Commitment`
- `Booking`
- `Order`
- `PaymentTransaction` mapped to table `transactions`
- `ProviderCall`
- `IdempotencyKey`

Keep domain naming explicit: source entity is `PaymentTransaction`; `transactions` is only the persistence table name.

## Critical schema reconciliation before writing commitments

Current SQL check:

```text
level IN ('FLEXIBLE','RESERVED','PAID','LOCKED')
```

is incompatible with source evidence that commitment strength has five defined levels C0..C4 and FR-030 requires exactly five.

Codex must read the exact `commitment_strength` values from the local frozen v0.4.2 YAML and choose a lossless persistence/API representation. In the same read, also record the exact `commitment_source_type` enum used by FR-029; do not guess it.

Preferred minimal change:

- preserve column name `level` if desired;
- change the SQL check/Pydantic enum to the exact five source codes (or exact reversible names);
- keep payment status solely in `PaymentTransaction.status`;
- derive an internal rank 0..4 by mapping, not by string comparison.

Do not guess C1-C3 names from this assist package.

## `policy_json` required fields for WP04 commitment

For canonical/anchored commitments, persist at least:

```text
semantic_key
scheduled_start_at
scheduled_end_at
fixed_schedule
strength_rank
booking_external_ref
payment_external_ref (after capture)
```

This lets WP06 preserve the commitment across PlanVersion/Activity UUID changes.

## Indexes recommended

Existing `idx_commitments_journey` is good.
Add only if tests/profile need them; do not indulge in index cosplay.

Useful low-risk indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_bookings_journey ON bookings(journey_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_journey ON orders(journey_id, status);
CREATE INDEX IF NOT EXISTS idx_transactions_journey ON transactions(journey_id, created_at);
```

## Existing idempotency table

The column `request_hash` can store a canonical application request fingerprint. User instruction against hash work applies to file/package integrity checks; no package hashes are needed. The reference implementation uses canonical JSON directly, so no cryptographic function is required.

Recommended storage key scope:

```text
transaction.create:{provider_key}:{Idempotency-Key}
```

because `idempotency_keys.key` is globally primary-keyed while transactions are provider-key scoped.
