# RESERVATION_HELPER_RESULTS.md — ORM quarantine helper aligned with schema (D01–D03)

## D01 — startup migration stays green

The startup migration introduced in V19.2.3 was **not** touched by this round
and remains green:

* legacy duplicates are quarantined before the schema script runs;
* the partial unique index
  (`WHERE confirmation_ref IS NOT NULL AND status <> 'QUARANTINED_DUPLICATE_IDENTITY'`)
  is genuinely created;
* a repair Event is written;
* a new duplicate is rejected by SQLite;
* no silent exception swallowing.

Evidence: `tests/test_v1923_final_code_gate.py::test_v1923_duplicate_confirmation_refs_are_migrated`
(passes in the 86-test gate run), `evidence/gate_suites_run.txt`.

## D02 — the ORM helper agrees with the schema

**Defect in Snapshot F.** `app/operations/reservation_identity.py` wrote:

```python
event_type = RESERVATION_IDENTITY_DUPLICATE
```

`events.event_type` is a **closed vocabulary** in `backend/db/schema.sql`
(`USER_CHANGE` is the sanctioned value for a user-initiated change). A direct
run against a duplicate database raised:

```
sqlite3.IntegrityError: CHECK constraint failed: event_type IN (...)
```

The helper is invoked from the reservation-confirm flow, so this was a real
crash path even though the startup migration normally removes duplicates first.

**Fix.**

* `event_type = "USER_CHANGE"` (sanctioned);
* `provider_key = "citynexus-reservation"` retained as the discriminator;
* `payload.kind = "RESERVATION_IDENTITY_DUPLICATE"` carries the specific reason;
* the partial unique index was **not** weakened.

Verified (`test_v1924_orm_quarantine_helper_matches_schema_and_is_idempotent`):

```
Event.event_type = USER_CHANGE
payload.kind     = RESERVATION_IDENTITY_DUPLICATE
no IntegrityError
```

## D03 — duplicate detection excludes quarantined rows (idempotent)

**Defect in Snapshot F.** Detection counted every row with a matching
`confirmation_ref`, including rows already quarantined on a previous run, so the
repair was not idempotent.

**Fix.** Both the grouping query and the per-reference row query now exclude
`status = QUARANTINED_DUPLICATE_IDENTITY`.

Verified on 3 seeded duplicates:

| Step | Result |
| --- | --- |
| first `detect()` | reports `ORM-DUP` with 3 reservation ids |
| first `quarantine()` | winner kept `CONFIRMED`; losers `QUARANTINED_DUPLICATE_IDENTITY`; 1 audit Event |
| second `detect()` | **`[]`** |
| second `quarantine()` | **`[]`** |
| audit Event count after second run | **unchanged (1)** — no repeated repair |

`test_v1924_reservation_confirm_flow_survives_legacy_duplicates` additionally
confirms the helper can run inside the confirmation flow without raising.

## Evidence

* `evidence/gate_suites_run.txt` — 86 passed, including the V19.2.3 migration
  test and the three V19.2.4 helper tests.
* `tests/test_v1924_final_truth_gate.py` — D02/D03 regression tests.
