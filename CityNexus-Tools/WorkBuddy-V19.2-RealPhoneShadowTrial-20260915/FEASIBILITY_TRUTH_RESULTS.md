# Single Feasibility Truth across the planning paths

Evidence: `evidence/feasibility_truth_a.json`, `evidence/feasibility_truth_b.json`.

Question: do `generate_plans()`, generic compose, `select`, and the booking-path validator agree
about the same journey?

---

## 1. The V19.1 split-brain is closed at the constraint level

In V19.1 the four paths built **different** constraint sets:

| Path | V19.1 (C) |
|---|---|
| `generate_plans()` (`services.py:847`) | `_journey_constraints_with_capabilities(...)` — no C4 |
| `select_plan()` (`main.py:3693`) | same — no C4 |
| `_assert_selected_plan_feasible()` (`main.py:4458`) | `validate_plan_feasibility(..., include_active_c4=True)` — **with C4** |

That is what produced the V19.1 sequence: generate 201 / validator `LOCKED_COMMITMENT_LOST` /
select 200 / booking 422.

In V19.2 every call site now resolves `include_c4` to `True`, because
`_journey_constraints_with_capabilities(session, journey, *, active_only=False, include_c4=True)`
defaults it to `True` and no caller overrides it:

| Call site | Argument | Effective `include_c4` |
|---|---|---|
| `main.py:3727` (select) | `active_only=True` | **True** |
| `main.py:4054` | defaults | **True** |
| `services.py:518` | `active_only=True` | **True** |
| `services.py:739` (validator) | `include_c4=include_active_c4` | True |
| `services.py:844` (generate) | defaults | **True** |

Measured result: **`generator_produced_plans_the_validator_rejects: []`** on both A and B. No
path produces plans another path rejects.

## 2. What that means in practice

The agreement was achieved by making `generate` **stricter**, not by making the validator
permissive. Measured matrix (`evidence/feasibility_truth_a.json`):

| Scenario | generate | plans | validator | select | booking |
|---|---|---|---|---|---|
| control: no reservation | 201 | 3 | `passed: true ×3` | 200 | 422 (commerce, see below) |
| control: generic compose | 201 | 1 | `passed: true` | 200 | 422 (commerce) |
| ARRIVAL C4 | **422** | 0 | no plans to validate | skipped | skipped |
| DEPARTURE C4 | **422** | 0 | no plans to validate | skipped | skipped |

So there is now **one truth** — but it is the truth that *nothing can be planned* whenever a
confirmed reservation exists. See `C4_ANCHOR_AND_IDEMPOTENCY_RESULTS.md`.

## 3. The booking-path 422 is a commerce rejection, not a feasibility rejection

```
POST /api/v1/journeys/{id}/bookings  {"activity_id": "...", "provider_key": "mock-booking"}
→ 422  {"error": {"code": "VALIDATION_ERROR",
                  "message": "activity has no supported tradable commerce service"}}
```

`BookingCreate` requires `activity_id: UUID` (`app/schemas.py:527`), and the demo activities carry
no tradable commerce service. So booking cannot be used as a feasibility oracle with the demo
data. The feasibility half of the booking path was measured directly instead, via
`validate_selected_plan_feasibility` (which is what `_assert_selected_plan_feasible` calls), and it
agrees with `select`.

**Note for the gate:** the road-prep's P0-1 description ("generate → 201 / validator →
LOCKED_COMMITMENT_LOST / select → 200 / booking → 422") **no longer reproduces**. The 422 seen at
booking today has a different cause and the `select`-accepted-then-`booking`-rejected sequence does
not occur. Label: **FIXED_IN_CURRENT**.

## 4. Exact reproduction

```
cd D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915
python tools/sync_tests.py A
python tools/v192_probe_feasibility_truth.py A
```

## 5. Residual issue

`generate` still reports a **collapsed** reason. When C4 blocks planning the client sees:

```json
{"error": {"code": "VALIDATION_ERROR",
           "message": "No feasible plan candidates satisfy the journey constraints",
           "details": null}}
```

while the validator knows the exact cause (`LOCKED_COMMITMENT_LOST:<semantic_key>`). Propagate
the concrete failure codes into the `generate` body — the V19.1 round flagged this as P1-2 and it
is still open.
