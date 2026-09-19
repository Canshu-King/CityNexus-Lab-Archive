# Addendum — mid-audit baseline drift and V19.2.3 in-flight delta

**Written:** 2026-09-15 22:45 local
**Status:** observational only. **This addendum does not change the Snapshot E verdict.**

---

## 1. Baseline drift detected

The authoritative main tree `D:\moodle\CityNexus` was **modified by another agent
while this audit was running**. The Snapshot-E delta gate had already been
completed against a private frozen copy, so the verdict in
`SNAPSHOT_E_DELTA_GATE_VERDICT.md` is unaffected — but the live tree is no longer
Snapshot E.

Files changed after the audit baseline was frozen (21:47):

| Time | File | vs Snapshot E |
|---|---|---|
| 22:07 | `backend/app/planning/anchor_schedule.py` | +201 / −98 lines |
| 22:09 | `backend/app/planning/hard_recovery.py` | +131 / −47 lines |
| 22:12 | `backend/app/main.py` | +88 / −6 lines |
| 22:15 | `backend/app/schemas.py` | new |
| 22:15 | `backend/app/services.py` | +46 / −4 lines |
| 22:18 | `backend/app/db/session.py` | new |
| 22:20 | `contracts/openapi.yaml` | +26 / −0 lines |

`app/replanning/feasibility.py` and
`frontend/src/features/recovery/RecoveryRequiredPanel.tsx` are **unchanged**.

A read-only in-flight snapshot was taken at ~22:2x into `_tree_inflight/` and the
same probes were re-run against it. **This is not a verdict on V19.2.3** — the
build is still in progress and no V19.2.3 package has been submitted.

## 2. What the in-flight tree already fixes

| Item | Snapshot E | In-flight (22:2x) |
|---|---|---|
| T01 ARRIVAL 12:30 lower bound | FAIL | **PASS** |
| T02 DEPARTURE 15:30 upper bound | FAIL | **PASS** |
| T03 MID_TRIP pin | PASS | PASS |
| T04 ARRIVAL+MID_TRIP+DEPARTURE | FAIL | **PASS** |
| T05 impossible anchor set | FAIL (fabricated plan) | **PASS** (`schedule = None`) |
| R03 NO_ALTERNATIVE from `is_feasible is None` | FAIL | **fixed** — `is_feasible=None` now yields `RECOVERY_REQUIRED` |
| D01/D02 schema unique index | FAIL (crash + no index) | `schema.sql` index removed; `db/session.py` now quarantines then creates a **partial** unique index and raises instead of swallowing |
| R02 resolve on selection | FAIL (never called) | `main.py:4068` now calls `resolve_recovery_events` inside the plan-select transaction; also at 2011 and 2320 |
| R01 acknowledge surface | absent | `POST /api/v1/journeys/{journey_id}/recovery/acknowledge` added (main.py:2024) + OpenAPI path + `acknowledged` / `acknowledged_at` fields |

In-flight T01/T02/T05 schedules (verbatim):

```
T01  Arrival (ARRIVAL)   12:30–12:50     <- arrival is now a hard lower bound
     Old Town Gate       13:10–14:25
     Riverside Museum    14:45–16:00
     Central Food Hall   16:20–17:20
     Nexus City Park     17:40–18:40

T02  Old Town Gate       09:00–10:15
     Riverside Museum    10:35–11:50
     Central Food Hall   12:10–13:10
     Nexus City Park     13:30–14:30
     Departure (DEPARTURE) 15:10–15:30  <- departure is now a hard upper bound

T05  schedule = None                     <- impossible anchor set yields no plan
```

## 3. What is still open in the in-flight tree (actionable)

1. **`app/replanning/feasibility.py` was not touched.** The deterministic gate
   still **accepts** a plan with a flexible activity before ARRIVAL, after
   DEPARTURE, and even for ARRIVAL-after-DEPARTURE — all three measured
   `passed = true, failures = []` against the in-flight tree
   (`_results/gate_probe_inflight_v1923.json`). The scheduler now refuses to
   *produce* such plans, but the gate that revalidates an existing or stale plan
   still would not catch one. The delta prompt required this invariant in **both**
   `anchor_schedule.py` and `feasibility.py`.

2. **The recovery panel is still the Snapshot E version.**
   `frontend/src/features/recovery/RecoveryRequiredPanel.tsx` is byte-identical
   (sha256 `7610dac69f4948ca…` in all three copies) and still contains:

   ```tsx
   function acknowledge() { setDismissed(true); setMessage(null); }
   ...
   if (dismissed) return null;
   ...
   > Continue without changes
   ```

   The new governed `POST …/recovery/acknowledge` endpoint is **not wired to any
   client**. R01 is therefore still open in the in-flight tree, even though the
   backend half now exists.

3. **`/experience` projection inconsistency is structurally unchanged.**
   `recovery_state(is_feasible=True)` still returns `state = "RESOLVED"` while
   `event_status` is `"DETECTED"`, and `recovery_flags()` still hardcodes
   `recovery_state: RECOVERY_REQUIRED`. The in-flight tree adds resolve calls on
   more paths, which reduces reachability, but the projection still decides
   `RESOLVED` from the feasibility argument alone without reading the Event. This
   should be re-verified against the declared-final V19.2.3 package.

4. **D00 (new blocker) status unverified.** The in-flight `db/session.py` reworks
   the migration path, but `app/operations/reservation_identity.py` was **not**
   changed, so `quarantine_duplicate_confirmation_identities()` still writes
   `event_type='RESERVATION_IDENTITY_DUPLICATE'`, which violates the
   `events.event_type` CHECK. It should be re-tested.

5. **P01 (patch portability) cannot be re-tested** until a V19.2.3 patch and a
   declared clean baseline exist.

## 4. Recommendation

- Treat `SNAPSHOT_E_DELTA_GATE_VERDICT.md` as the binding result for V19.2.2:
  **BLOCKED**.
- When the V19.2.3 package lands, run one targeted delta rather than the whole
  historical suite. The probe scripts in `_results/` already accept a
  `CITYNEXUS_TREE` environment override, so the same seven checks can be re-run
  against the V19.2.3 source drop in minutes:

  ```
  set CITYNEXUS_TREE=<v1923_extract>\backend
  %PY% c4_probe.py ; %PY% gate_probe.py ; %PY% recovery_probe.py ; %PY% db_migration_probe.py
  ```

  Do **not** issue `SNAPSHOT_F_ACCEPTED_FOR_PHYSICAL_TRIAL_PRECHECK` from the
  in-flight tree; item 1 above alone would keep the gate closed.
