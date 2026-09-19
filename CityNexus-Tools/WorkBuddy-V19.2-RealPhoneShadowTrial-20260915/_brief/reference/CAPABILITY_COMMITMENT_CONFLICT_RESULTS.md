# CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md

**Scope:** capability ↔ C4 (locked commitment) conflict — the brief's "capability ↔ C4
conflict" focus item, plus the F7 family carried over from the previous round.
**Evidence:** `evidence/commitment_conflict_{a,b}.json`, `evidence/c4_gate_{a,b}.json`,
`evidence/c4_start_{a,b}.json`
**Probes:** `tools/v191_probe_commitment_conflict.py`, `tools/v191_probe_c4_gate.py`,
`tools/v191_probe_c4_start.py`

---

## 1. The conflict is real and reproducible

A `C4_Anchored`/`ACTIVE` commitment is created through the production path:

```
POST /api/v1/journeys/{id}/inbox/import   (STRUCTURED_JSON)  -> 201 (draft)
POST /api/v1/journeys/{id}/inbox/{draft_id}/confirm          -> 200
     -> TransportReservation + Commitment(level="C4_Anchored", status="ACTIVE")
```

(`app/operations/v9.py:693 confirm_reservation_draft()` hardcodes `level="C4_Anchored"`.)

Then, with a HARD capability that conflicts with that commitment:

| Step | Result |
|---|---|
| `POST /journeys/{id}/plans/generate` | **201 / 3 plans** |
| `validate_plan_feasibility()` on all 3 plans | `feasible: false`, `["LOCKED_COMMITMENT_LOST:ea06631e-f5b4-598a-8a96-2483c271a825"]` |
| `POST /journeys/{id}/plans/{plan}/select` | **200** |
| `POST /journeys/{id}/bookings` on that plan | **422** `"selected plan is no longer feasible: LOCKED_COMMITMENT_LOST:…"` |

`generator_produced_plans_the_validator_rejects: true`,
`generation_includes_locked_commitment: false`.

**The product lets the traveller generate and select a plan it will not let them book.**

---

## 2. Root cause: three code paths, two definitions of feasibility

| Path | Constraint assembly | C4 included? |
|---|---|---|
| `generate_plans()` (`services.py:847`) | `_journey_constraints_with_capabilities()` | **no** |
| `select_plan()` (`main.py:3693`) | `_journey_constraints_with_capabilities(..., active_only=True)` | **no** |
| `_assert_selected_plan_feasible()` (`main.py:4458`) → `validate_selected_plan_feasibility()` → `validate_plan_feasibility(..., include_active_c4=True)` | includes C4 | **yes** |
| `POST /bookings` | same as above | **yes** |

`validate_plan_feasibility()` itself defaults to `include_active_c4=True`
(`services.py:706`), so the **default is correct** and the two planning entry points
explicitly bypass it by not loading commitments at all.

**C4 does not influence generation.** `c4_influence.plans_differ: false` — plan signatures
(`(place_id, start_at)` per activity) are identical with and without the commitment, measured
after correcting the seed timestamps to fall inside the demo journey window
(`2026-10-10T09:00–19:00`; an earlier run seeded `2026-09-20` and the C4 was filtered out
before reaching the gate, which looked like "C4 has no influence" but was really "C4 was
excluded").

---

## 3. NEW P0: `start` crashes for an ARRIVAL-anchored C4

`POST /journeys/{id}/start` → **500**, journey left in `PLANNED`:

```
main.py:4891 start_journey
  -> main.py:4766 _twin_snapshot
     -> runtime.py:54 capture_runtime_mobility_snapshot
        -> snapshot_capture.py:121
MobilitySnapshotCaptureError: mobility fact unavailable for place-old-town|ea06631e-…
KeyError: 'no routable coordinates for ea06631e-f5b4-598a-8a96-2483c271a825'
```

Anchor-role matrix (`evidence/c4_start_{a,b}.json`):

| Anchor role | `start` | Journey state |
|---|---|---|
| `ARRIVAL` @ 12:30 | **500** | **stuck `PLANNED`** |
| `DEPARTURE` | 200 | `ACTIVE` |
| `MID_TRIP` (`place-old-town`) | 200 | `ACTIVE` |
| `MID_TRIP` (`place-riverside-museum`) | 200 | `ACTIVE` |
| `ARRIVAL` @ 07:00 (before the first activity → filtered out) | 200 | `ACTIVE` |
| control (no reservation) | 200 | `ACTIVE` |

An `ARRIVAL`-anchored commitment stores a random UUID as its mobility `semantic_key`
(`_uuid("place:…")`), and `_twin_snapshot` line 4766 tries to route to it. `GET /twin` on the
same journey returns **200**, so only the `start` path is affected.

---

## 4. F7 family — carried over from the previous round

| Finding | Status | Evidence |
|---|---|---|
| **F7a** paid C4 survives the conflict | **holds** | `commitment_survived: true`, `status: ACTIVE`; 4 further cases at Snapshot A |
| **F7b** the conflict is never surfaced | **STILL_REPRODUCIBLE** | `/twin` mentions `commitment` but not `step_free` / `accessib` / `conflict`; the blocking message is the single generic string |
| **F7c** a SOFT preference silently keeps an obstructed activity | **STILL_REPRODUCIBLE** | SOFT + known-stairs cruise → **201 / 3 plans, all 3 containing the obstructed cruise**, `any_warning_in_body: false` |
| **F7d** a `robust` flag reports the conflict | **restated, not reproduced** | `robust_flag` came back `null` because `_envelope_payload` is never reached; the `/twin` payload has no `feasibility_envelope` at all (keys: `active_plan_version_id`, `context`, `current_activity_id`, `journey_id`, `latest_event_id`, `projection_status`, `snapshot_at`, `upcoming_commitments`). F7d as originally written cannot be reproduced in this form. |

HARD + paid cruise → **422 generic**, the cruise present in all 3 **stale** plans, commitment
survives `ACTIVE`. So the HARD case is refused but the stale plans are not cleaned up and the
reason is not explained.

---

## 5. Duplicate C4s are not guarded

Two `inbox/import` + `confirm` cycles with the **same `confirmation_ref`** each create a
separate `C4_Anchored` commitment. There is no duplicate-reference check on the
`inbox/import` path, so the same external booking can be anchored twice.

---

## 6. Verdict table

| # | Finding | Result | Tag |
|---|---|---|---|
| 1 | A selected plan is always bookable | **VIOLATED** — `select` 200 then `bookings` 422 | `FINAL_V19` |
| 2 | Generation respects active C4 commitments | **VIOLATED** — `plans_differ: false`, `generation_includes_locked_commitment: false` | `FINAL_V19` |
| 3 | All planning paths share one feasibility definition | **VIOLATED** — 3 paths, 2 definitions | `FINAL_V19` |
| 4 | `start` works for every anchor role | **VIOLATED** — ARRIVAL → 500, journey stuck `PLANNED` | `NEW` |
| 5 | A paid commitment survives a capability conflict | holds | — |
| 6 | The conflict is surfaced to the traveller | **VIOLATED** — never mentioned on any surface | `FINAL_V19` |
| 7 | A SOFT preference does not silently retain an obstructed activity | **VIOLATED** — 3/3 plans keep it, no warning | `FINAL_V19` |
| 8 | Stale plans are cleaned up when feasibility fails | **VIOLATED** — 3 stale `CANDIDATE` plans remain | `FINAL_V19` |
| 9 | Duplicate `confirmation_ref` is rejected | **VIOLATED** — two separate C4s created | `NEW` |
| 10 | `robust` flag reports the conflict (F7d) | **INCONCLUSIVE** — the payload has no `feasibility_envelope`; restate the finding | `INCONCLUSIVE` |

## 7. Recommendation (not applied)

1. Load active C4 commitments in `generate_plans()` and `select_plan()` — or, better, have all
   four paths call one constraint-assembly function.
2. Make `POST /plans/{id}/select` run `_assert_selected_plan_feasible()` so `select` and
   `bookings` cannot disagree.
3. Give `ARRIVAL`-anchored commitments a routable `semantic_key` (use the arrival place's
   coordinates, not a fresh UUID), or make `_twin_snapshot` tolerate an unroutable key.
4. Mark stale `CANDIDATE` plans `SUPERSEDED` when regeneration fails feasibility.
5. Add a duplicate-`confirmation_ref` guard on `inbox/import`.
6. Restate F7d against a surface that actually exists, or drop it.
