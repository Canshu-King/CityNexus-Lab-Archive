# MIGRATION_RESULTS.md — Legacy duplicate migration (P1-2, D01/D02/D03)

## Defect

Startup contained:

```python
try:
    CREATE UNIQUE INDEX ... (journey_id, confirmation_ref)
except Exception:
    pass
```

That is a silent failure: the claimed uniqueness rule could simply not exist.
Worse, a **non-partial** unique index over `(journey_id, confirmation_ref)`
cannot be created while historical duplicates exist, and
`quarantine_duplicate_confirmation_identities()` changed `status` but left the
duplicated pair intact, so the index still could not be created.

## Fix — a real migration, no silent failure

Two phases in `app/db/session.py`:

1. **Before** the schema script — `_quarantine_existing_duplicates()`:
   * no-op when the table does not exist (fresh database);
   * for each duplicated `(journey_id, confirmation_ref)`, the earliest row by
     `captured_at` stays authoritative;
   * later duplicates become `QUARANTINED_DUPLICATE_IDENTITY` and have their
     `draft_id` released, so they no longer claim the identity but their
     evidence and audit trail are preserved;
   * a durable repair Event records the winner and the quarantined ids.

2. **After** the schema script — `_migrate_reservation_identity()`:
   * creates a **partial** unique index:
     ```sql
     CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation
         ON transport_reservations(journey_id, confirmation_ref)
         WHERE confirmation_ref IS NOT NULL
           AND status <> 'QUARANTINED_DUPLICATE_IDENTITY';
     ```
   * raises on any genuine failure instead of swallowing it.

`backend/db/schema.sql` no longer declares the index inline, precisely because
it cannot be created before duplicates are migrated.

## Verified on a database that already contained duplicates

A legacy database was constructed with three rows sharing
`confirmation_ref = 'DUP-REF'` and no uniqueness index. After the startup
migration:

| Check | Result |
| --- | --- |
| Earliest row | stays `CONFIRMED` (authoritative) |
| Later rows | `QUARANTINED_DUPLICATE_IDENTITY`, `draft_id` released |
| Original evidence preserved | yes — rows are updated, never deleted |
| Repair audit Event | written (`RESERVATION_IDENTITY_DUPLICATE`) |
| Uniqueness index | exists, partial on `QUARANTINED_DUPLICATE_IDENTITY` |
| Duplicate insert afterwards | **rejected by the database** |
| Silent exception | none — genuine failures raise |

## D03 — concurrent confirmation

Two racing confirmations of the same `confirmation_ref` still converge on one
`TransportReservation` identity and one `C4_Anchored` commitment, with no HTTP
500. The database uniqueness index is now the real serialization point; the
application pre-check and `IntegrityError` handling remain as friendly paths.

## Evidence

* `tests/test_v1923_final_code_gate.py::test_v1923_duplicate_confirmation_refs_are_migrated`
  — runs the migration in an isolated subprocess against a purpose-built legacy
  database and asserts the migration outcome, the index, and that uniqueness is
  genuinely enforced.
* `evidence/v1923_gate_run.txt` — 74 passed.

## Note on test isolation

The migration test runs in a subprocess because the migration legitimately
rebinds the application database engine. Mutating that global state inside the
shared pytest process would leak into unrelated suites; the isolation is test
hygiene, not an avoidance of the assertion.
