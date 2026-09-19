# MOBILITY_IDENTITY_RESULTS.md — One canonical mobility identity

## The invariant

```
Activity.metadata.semantic_key  ->  stable routing / feasibility identity
Activity.place_id               ->  database Place identity
```

Both are needed and they are **not** the same thing. Frozen provider mobility
evidence is captured against semantic node keys, so the deterministic gate must
key on `semantic_key` at every stage, or the same plan appears to have different
mobility facts depending on who is asking.

## The defect

V19.2.1 had two identity spaces:

* the V9 stay materializer stored `metadata.semantic_key = node.key`
  (`arrival-anchor`, `stay:...:luggage-drop`) while `Activity.place_id` was a
  derived Place id;
* the shared gate keyed on `place_id`.

To paper over the gap, `app/operations/v9.py` contained a **temporary rebind**
that copied frozen fact values onto concrete Place ids before validation. That
translation layer is exactly the kind of hack that produces
`MOBILITY_DATA_UNAVAILABLE` drift whenever one side changes.

## The fix

1. `activity_from_record()` now reads the routing identity as
   `metadata.semantic_key` first, falling back to `place_id` /
   `city_service_id` / `activity_key`.
2. `_location_key()` prefers the frozen-evidence semantic key, falling back to
   the concrete Place identity for callers that never carried one.
3. The V19.2.1 rebind in `app/operations/v9.py` was **deleted** and replaced by
   `MobilitySnapshot.from_evidence(mobility_evidence)` — the stored bundle is
   already keyed by the canonical identity, so it is consumed directly. No new
   translation layer was introduced.
4. The V9 materializer now writes canonical structural identities
   (`v12:{journey_id}:{arrival|departure}-anchor`) into both the activity
   metadata and the frozen evidence, so persistence, reload, selection and
   booking all reload one consistent graph.
5. `protected_commitments` binds reservation anchors to that same canonical
   identity, and `operations/v9.py` binds the commitment to the activity by
   canonical key.

## Result

* The V9 flagship end-to-end (`tests/test_v9_real_trip_operations.py`, 4 tests)
  passes: materialize -> gate -> select -> start -> protected activity visible.
* No `MOBILITY_DATA_UNAVAILABLE` drift remains on the reload path.
* The gate reads the **same frozen snapshot** at generation, select, booking and
  start; there is no second capture and no identity translation.

## Evidence

* `evidence/broad_regression_head.txt` — `test_v9_real_trip_operations.py` and
  the C4/replan integration suites pass.
* `evidence/v192_contract_run.txt` — 61/61, including the frozen-evidence
  reload guard.
* `evidence/acceptance_matrix_d.json` — generate -> persist -> reload -> select
  -> start all agree for ARRIVAL, DEPARTURE and MID_TRIP.

## Note on scope

`Activity.metadata.semantic_key` is authoritative for routing; `place_id`
remains authoritative for the database Place row. The two are allowed to
differ, and now do so in a controlled, single-source way instead of being
silently translated at the gate.
