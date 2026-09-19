# C4_INTERIOR_TRUTH_RESULTS.md — Interior C4 boundary enforcement

## Required invariant

* `ARRIVAL` and `DEPARTURE` are **structural edge anchors** and do not reject
  themselves.
* Every **other** `LOCKED_COMMITMENT` activity — `MID_TRIP` and role-less
  booking/order anchors — must lie within
  `[ARRIVAL completion, DEPARTURE start]`.

## Why the shared gate matters here

The generator already refuses to *build* these layouts. But the shared
deterministic feasibility gate is what protects against plans the generator
never produced:

* plans persisted before a scheduler fix,
* imported plans,
* planner-edited plans,
* stale plans,
* and any future generator bug.

`select`, `start` and every revalidation path call that gate. If it accepts an
impossible layout, the layout becomes usable.

## Defect (reproduced on exact Snapshot G)

```
mid_before_arrival        passed=true   expected=false   FAIL
mid_after_departure       passed=true   expected=false   FAIL
roleless_before_arrival   passed=true   expected=false   FAIL
mid_inside                passed=true   expected=true    PASS
roleless_inside           passed=true   expected=true    PASS
```

### Root cause

The boundary loop skipped **every** anchor activity:

```python
anchor_keys = {commitment.activity_key for commitment, _role in locked_specs}
...
if item_key in anchor_keys:
    continue
```

Only structural edges should be skipped. `MID_TRIP` and role-less anchors were
skipped as well, so their position was never checked against
`arrival_end_min` / `departure_start_min`.

## Fix (one file)

`backend/app/replanning/feasibility.py` — the skip rule became role-aware:

```python
anchor_roles = {
    commitment.activity_key: role for commitment, role in locked_specs
}
...
item_anchor_role = anchor_roles.get(item_key, "")
if item_anchor_role in {"ARRIVAL", "DEPARTURE"}:
    continue
```

A role-less anchor resolves to `""`, which is **not** in the edge set, so it is
now boundary-checked exactly like a `MID_TRIP` anchor. Structural edges keep
their self-exemption.

## Post-fix probe

`evidence/v1925_c4_interior_probe.json` — 5/5 PASS, exit code 0:

| Case | passed | failures |
| --- | --- | --- |
| mid_before_arrival | false | `C4_ACTIVITY_BEFORE_ARRIVAL:mid` |
| mid_after_departure | false | `C4_ACTIVITY_AFTER_DEPARTURE:mid` |
| roleless_before_arrival | false | `C4_ACTIVITY_BEFORE_ARRIVAL:booking` |
| mid_inside | true | `[]` |
| roleless_inside | true | `[]` |

## Regression tests

`backend/tests/test_v1925_c4_interior_truth.py` — 7 passed:

1. `test_v1925_mid_trip_before_arrival_is_rejected`
2. `test_v1925_mid_trip_after_departure_is_rejected`
3. `test_v1925_roleless_lock_before_arrival_is_rejected`
4. `test_v1925_mid_trip_inside_boundaries_is_accepted`
5. `test_v1925_roleless_lock_inside_boundaries_is_accepted`
6. `test_v1925_structural_edges_do_not_reject_themselves` (guards the V19.2.4
   F05 semantic: a booked 08:00 departure on a 09:00 draft Journey stays valid)
7. `test_v1925_interior_lock_on_the_boundary_is_inside` (boundary semantics are
   inclusive)

## No regression in the prior gate truth

The V19.2.4 probe still passes **4/4**
(`evidence/v1924_truth_probe_regression.json`), and the full gate suite is
**93/93**. In particular the V19.2.4 F05 case — an edge-defining departure
outside the draft window — is still accepted, so the interior-lock tightening
did not accidentally start rejecting structural edges.
