# WP04 Preflight Findings from current repair checkpoint

This was prepared against `CityNexus-MVP-WP00-WP03-Repair-Checkpoint-Review-20260909.zip` while Codex is independently repairing the final pre-WP04 WP03 issues.

## Ready foundations

- SQL already contains Commitment, Booking, Order, Transaction, ProviderCall and IdempotencyKey tables.
- OpenAPI already contains create/cancel booking, create order and create transaction endpoints.
- deterministic provider behavior fixture already specifies mock booking/payment success/failure behavior.
- canonical demo fixture already identifies the 15:30 River Cruise locked commitment.
- requirement baseline contains WP04-relevant FR/BR/IR/NFR/SR acceptance criteria.

## Important gaps discovered now

### 1. Commitment strength representation is currently lossless only on paper, not in schema

Reconciliation says source domain has five strengths `C0_Flexible ... C4_Anchored`.
Current SQL/OpenAPI allow only four labels `FLEXIBLE/RESERVED/PAID/LOCKED`.
FR-030 explicitly requires exactly five source levels.
BR-011 explicitly prevents treating payment alone as the strength decision.

This must be reconciled before WP04 starts persisting commitments.

### 2. Commitment source-type mapping also needs one exact source read

FR-029 traces to `commitment_source_type`. The assist does not guess this enum either. Read it in the same tiny frozen-YAML inspection as `commitment_strength`, then record the reversible mapping used by the MVP.

### 3. Current ORM has no commerce/technical models

No ORM classes yet for Commitment, Booking, Order, PaymentTransaction, ProviderCall, IdempotencyKey.

### 4. Provider ports are incomplete

Current ports only cover CityDataProvider and MobilityProvider. IR-006/007 need BookingProvider and PaymentProvider.

### 5. OpenAPI cannot fully prove IR-006/IR-007 yet

Create/cancel/create-payment exist, but availability/status operations are missing. The assist proposes three small GET endpoints.

### 6. The stable lock identity must survive PlanVersion changes

WP04 must not create a lock that only points to one Activity UUID. `policy_json` should carry stable semantic key + committed schedule so WP06 can preserve the 15:30 River Cruise when creating a new PlanVersion.

## Scope discipline

Do not start implementing this package until the current WP03 repair gate passes. This package exists to prevent Codex from spending quota rediscovering WP04 architecture afterwards.

### 7. Existing OrderCreate lets the client submit unit prices

For WP04, server-side catalog data must be authoritative for SKU price/total. The assist supplies a tiny deterministic commerce catalog and an `order_pricing.py` reference. Prefer request items `{sku, quantity}`; do not trust a client-supplied unit price.
