# CityNexus Snapshot-E Delta Gate — Independent Red-Team Verdict

**Reviewer:** WorkBuddy AI (independent read-only red-team)
**Date:** 2026-09-15 21:5x (local)
**Task:** `WORKBUDDY_DELTA_PROMPT.md` from `CityNexus-V19.2.3-FinalShadowTrial-Closure-RoadPrep-20260915.zip`

---

## Final verdict

```
BLOCKED
```

All seven independent findings are **reproduced**. Six of seven hard gates fail.
One **new, previously unreported** blocker was found (D00 below).

The V19.2.2 self-verdict `SHADOW_TRIAL_CODE_READY` is **not accepted**.
No physical-device trial should begin from Snapshot E.

---

## 1. Frozen artefacts

| Artefact | sha256 |
|---|---|
| `CityNexus-EAC-V19.2.2-RealPhone-CodeGate-Final-20260915.zip` (Snapshot E) | `20b91aa97b523d97b83a44bed1d810bea7dde4578da1a2bde792388a7465ab36` |
| `CityNexus-V19.2.1-RealPhone-ShadowTrial-Gate-20260915(1).zip` (declared patch baseline) | `797239dc2652a38f96cf1b37aa03cc432188d3d6b485e86ff5344c97d9e8839e` |

Snapshot E's submitted `source/` contains 17 changed files. All 17 were compared
byte-for-byte against the live main tree `D:\moodle\CityNexus`:

```
SAME   backend/app/capabilities.py
SAME   backend/app/integrations/mobility/snapshot_capture.py
SAME   backend/app/main.py
SAME   backend/app/operations/reservation_identity.py
SAME   backend/app/operations/v9.py
SAME   backend/app/planning/anchor_schedule.py
SAME   backend/app/planning/anchors.py
SAME   backend/app/planning/hard_recovery.py
SAME   backend/app/replanning/feasibility.py
SAME   backend/app/replanning/protected_commitments.py
SAME   backend/app/replanning/provider_snapshots.py
SAME   backend/app/services.py
SAME   contracts/openapi.yaml
SAME   frontend/src/app/V8Experience.tsx
SAME   frontend/src/app/v8Types.ts
SAME   frontend/src/features/recovery/RecoveryRequiredPanel.tsx
SAME   frontend/src/generated/api.ts
```

17/17 identical → the frozen Snapshot E source is the same code that was
measured here. All measurements below were taken against a private read-only
copy (`_tree/`) built from that content; the authoritative main tree was never
modified.

---

## 2. Gate results

| # | Gate | Verdict | Evidence |
|---|---|---|---|
| 1 | C4 temporal ordering | **FAIL** | T01/T02/T04/T05 reproduce; gate also accepts the impossible plan |
| 2 | HARD recovery governance | **FAIL** | R01 — client-only dismissal, no backend surface exists |
| 3 | Recovery resolution lifecycle | **FAIL** | R02 — projection says RESOLVED while Event stays DETECTED |
| 4 | No-alternative state | **FAIL** | R03 — derived from `is_feasible is None` with a candidate present |
| 5 | Stale candidate listing | **FAIL** | S01 — no flag/filter anywhere; S02 passes |
| 6 | Legacy duplicate migration | **FAIL** | D01–D03 + new blocker D00 |
| 7 | Patch portability | **FAIL** | P01 — `git apply --check` exits 1 on `contracts/openapi.yaml` |

---

## 3. Finding 1 — C4 temporal ordering (FAIL)

### 3.1 Direct execution of `schedule_template_with_anchors()`

Probe: `_results/c4_probe.py` → `_results/c4_probe.json`
Uses the real production template (`app/services.py::_templates()`), real
`ResolvedAnchor` objects, the real `effective_journey_window()`, and the
deterministic 20-minute default travel gap. **Actual activity timestamps are
asserted**, not plan counts.

| Case | Verdict | Detail |
|---|---|---|
| T01 ARRIVAL 12:30 | **FAIL** | `Old Town Gate 09:00–10:15`, `Riverside Museum 10:35–11:50` both start **before** arrival |
| T02 DEPARTURE 15:30 | **FAIL** | `Nexus River Cruise Pier 15:50–16:50`, `Skyline Dinner House 17:10–18:40` both end **after** departure |
| T03 MID_TRIP 13:00 | PASS | anchor pinned at exactly 13:00, surrounding POIs feasible |
| T04 ARRIVAL 10:00 + MID_TRIP 13:00 + DEPARTURE 17:00 | **FAIL** | `Skyline Dinner House 17:20–18:50` runs **after** the 17:00 departure |
| T05 ARRIVAL 17:00 + DEPARTURE 10:00 | **FAIL** | a **fabricated plan** is produced; no conflict raised |

T01 produced schedule (verbatim):

```
Old Town Gate           09:00–10:15
Riverside Museum        10:35–11:50
Arrival (ARRIVAL)       12:30–12:50
Nexus City Park         13:20–14:20
Nexus River Cruise Pier 15:30–16:30
Skyline Dinner House    17:00–18:30
```

T02 produced schedule (verbatim):

```
Old Town Gate           09:00–10:15
Riverside Museum        10:35–11:50
Central Food Hall       12:10–13:10
Nexus City Park         13:30–14:30
Departure (DEPARTURE)   15:10–15:30
Nexus River Cruise Pier 15:50–16:50
Skyline Dinner House    17:10–18:40
```

T04 produced schedule (verbatim):

```
Arrival (ARRIVAL)       10:00–10:20
Riverside Museum (MID)  13:00–14:00
Nexus City Park         14:20–15:20
Departure (DEPARTURE)   16:40–17:00
Skyline Dinner House    17:20–18:50
```

T05 produced schedule (verbatim — impossible anchor set):

```
Departure (DEPARTURE)   09:40–10:00
Riverside Museum        10:30–11:45
Central Food Hall       12:05–13:05
Nexus City Park         13:25–14:25
Nexus River Cruise Pier 15:30–16:30
Arrival (ARRIVAL)       17:00–17:20
```

### 3.2 The deterministic gate also accepts the impossible plan

Probe: `_results/gate_probe.py` → `_results/gate_probe.json`.
Every input is valid **except** the temporal boundary question, so a PASS is
decisive.

| Case | Gate result | Failures |
|---|---|---|
| A: ARRIVAL 12:30 with a 09:00 flexible POI | **passed = true** | `[]` |
| B: DEPARTURE 15:30 with a 17:00 flexible POI | **passed = true** | `[]` |
| C: control — genuinely clean plan | passed = true | `[]` |
| D: ARRIVAL 17:00 + DEPARTURE 10:00 | **passed = true** | `[]` — no conflict of any kind |

Case C is a working control: the gate is not simply always-passing. Cases A, B
and D prove it has **no ARRIVAL lower bound, no DEPARTURE upper bound and no
anchor-ordering invariant**.

### 3.3 Root cause (confirmed in source)

`app/planning/anchor_schedule.py`:
- `_merge_anchors()` sorts optional POIs and anchors together by `start_at`, then
  `schedule_template_with_anchors()` re-times optional items with
  `start_at = max(item.start_at, cursor + gap)`. **Nothing bounds them from below
  by the ARRIVAL anchor or from above by the DEPARTURE anchor.**
- `effective_journey_window()` (lines 411–438) only widens the window with
  `min(start, anchor_start)` / `max(end, anchor_end)` — it can never tighten it.

`app/replanning/feasibility.py`:
- lines 547–565 do the same `min`/`max` widening of `effective_start` /
  `effective_end` over `LOCKED_COMMITMENT` anchors.
- the window check at lines 674–677 fires `JOURNEY_END_BY_EXCEEDED` **only if a
  `JOURNEY_END_BY` constraint exists**, which no C4 anchor creates.

The `LOCKED_COMMITMENT` anchors are honoured as *pinned slots* but never as
*boundaries*. The V19.2.2 acceptance evidence ("generation/select/start has
executable acceptance evidence") proves only that a plan exists — exactly the
insufficiency the delta prompt warned about.

---

## 4. Finding 2 — HARD recovery can still be hidden client-side (FAIL, R01)

`frontend/src/features/recovery/RecoveryRequiredPanel.tsx` (Snapshot E, verbatim):

```tsx
  function acknowledge() {
    setDismissed(true);          // line 75-78
    setMessage(null);
  }
  ...
  if (dismissed) return null;    // line 42 — the entire warning disappears
  ...
          <button
            type="button"
            data-testid="recovery-acknowledge"
            onClick={acknowledge}
            disabled={busy !== null}
          >
            Continue without changes   // line 123 — the exact wording to be replaced
          </button>
```

- The only network call in the component is the `Generate new options` POST.
  `acknowledge()` performs **no** request, **no** persistence, **no** state
  change of any kind on the backend.
- One click removes the entire panel, including the failure list, for both the
  **HARD capability** case and the **stale evidence** case (both share this
  button).
- There is **no backend acknowledgement surface to call**:
  `contracts/openapi.yaml` contains no path matching `acknowledg`; the only
  recovery-related path is
  `/journeys/{journey_id}/stay-options/{option_id}/autopilot/recover`.
- `RecoveryState.actions` advertises `["REPLAN", "ACKNOWLEDGE_NO_ALTERNATIVE"]`,
  but nothing in the UI or API implements the second action.

The required wording (`Acknowledge warning`), a persisted acknowledgement, and a
surviving unverified/infeasible banner are all absent. A traveller can make an
infeasible plan look healthy with one click.

---

## 5. Finding 3 — recovery Event lifecycle does not resolve (FAIL, R02)

### 5.1 Call-site analysis

`resolve_recovery_events()` is referenced exactly twice in the whole backend:

```
backend/app/main.py:262    resolve_recovery_events,        # import
backend/app/main.py:2008            resolve_recovery_events(session, journey)
```

Line 2008 lives in `POST /api/v1/journeys/{journey_id}/capabilities/confirm`
(defined at line 1931) and runs **only in the `elif passed is True:` branch** —
i.e. when the capability change itself immediately makes the existing plan
feasible again.

**No plan-selection, plan-activation or replan endpoint calls it.** Selecting a
freshly generated feasible replacement therefore leaves the durable Event
`DETECTED` forever.

### 5.2 Measured state disagreement

Probe: `_results/recovery_probe.py` → `_results/recovery_probe.json`
(real SQLite DB, real `recovery_state()` / `recovery_flags()`, one `DETECTED`
recovery Event, one feasible active plan, one `CANDIDATE` plan):

```json
{
  "R02_event_status_at_start":              "DETECTED",
  "R02_experience_recovery_state":          "RESOLVED",
  "R02_experience_recovery_event_status":   "DETECTED",
  "R02_event_status_after_projection":      "DETECTED",
  "R02_DISAGREEMENT": "projection says RESOLVED but event_status is still DETECTED",
  "R02_flags_disagree_with_projection":     true,
  "R02_experience_flags": {
    "needs_review": true,
    "recovery_required": true,
    "recovery_state": "RECOVERY_REQUIRED"
  }
}
```

So `/experience` simultaneously reports:
- `recovery.state = RESOLVED`, `recovery.event_status = DETECTED`
- `experience_flags.recovery_required = true`, `needs_review = true`

`recovery_flags()` (hard_recovery.py:183–196) hardcodes
`"recovery_state": ACTIVE` regardless of the projection, so the two surfaces can
never agree by construction. `recovery_state()` line 165 decides `RESOLVED` from
the *feasibility argument alone*, without ever touching the Event.

This is exactly the inconsistency the acceptance matrix row **R02** forbids
("durable recovery Event resolves; flags/UI agree").

---

## 6. Finding 4 — NO_ALTERNATIVE is inferred, not attempted (FAIL, R03)

`app/planning/hard_recovery.py:165` (verbatim):

```python
state = ACTIVE if is_feasible is False else NO_ALTERNATIVE if is_feasible is None else RESOLVED
```

Measured (same probe):

```json
{
  "R03_state_when_is_feasible_is_None": "RECOVERY_REQUIRED_NO_ALTERNATIVE",
  "R03_NO_ALTERNATIVE_without_any_replan_attempt": true,
  "R03_candidate_plan_count_at_that_moment": 1,
  "R03_state_when_is_feasible_is_False": "RECOVERY_REQUIRED"
}
```

A durable `RECOVERY_REQUIRED_NO_ALTERNATIVE` state is produced while a
`CANDIDATE` plan exists and **no replan was attempted at all**. The state is
derived purely from a missing feasibility boolean — the exact anti-pattern the
gate forbids.

`recovery_state()` also counts proposals with
`PlanVersion.status == "CANDIDATE"` and exposes them as `candidate_plan_ids`
without any feasibility check against the current HARD capability + active C4
set, so unvalidated candidates are advertised as alternatives.

---

## 7. Finding 5 — stale candidates remain ordinary CANDIDATE rows (FAIL, S01)

`backend/app/main.py:3857–3865` (verbatim):

```python
@app.get("/api/v1/journeys/{journey_id}/plans")
def list_plans(journey_id: UUID, session: Session = Depends(get_session)):
    require(session, Journey, str(journey_id), "Journey")
    items = session.scalars(
        select(PlanVersion)
        .where(PlanVersion.journey_id == str(journey_id))
        .order_by(PlanVersion.version_no)
    ).all()
    return [plan_schema(session, item) for item in items]
```

Every `PlanVersion` is returned with no staleness projection and no filter.
Corroborating facts:

- `plan_schema` exposes no stale/expiry field.
- `contracts/openapi.yaml` `PlanVersion` has no stale/expiry field — only the
  `status` enum (`CANDIDATE, SELECTED, ACTIVE, SUPERSEDED, REJECTED`).
- `frontend/src/app/V8Experience.tsx` contains no candidate staleness marking.
- Snapshot E's own evidence (`evidence/stale_candidates_d.json`) **admits it**:
  `"candidate_still_listed": true`, `"candidate_listed_status": "CANDIDATE"`.

**S02 PASSES**: `/start` with stale evidence correctly returns `409`
(`STALE_RECOMPOSE_REQUIRED: … evidence expired`), and selection revalidation
raises. The final guard is intact — but it is the *only* guard, which is what
the gate rejected.

---

## 8. Finding 6 — legacy duplicate migration (FAIL, D01–D03 + new D00)

Probes: `_results/db_migration_probe.py`, `_results/db_migration_probe2.py`
(real SQLite DB, real `app.db.session.ensure_schema()`).

### D00 (NEW — not in the review) — the quarantine helper cannot run at all

`app/operations/reservation_identity.py::quarantine_duplicate_confirmation_identities()`
writes:

```python
event_type=QUARANTINE_EVENT,   # "RESERVATION_IDENTITY_DUPLICATE"
```

but `events.event_type` is constrained by `db/schema.sql`:

```
CHECK (event_type IN ('TRAFFIC_DELAY','CLOSURE','WEATHER','SCHEDULE_DELAY',
                      'SERVICE_UNAVAILABLE','USER_CHANGE','OTHER'))
```

Measured:

```json
{
  "c_quarantine_committed": false,
  "c_quarantine_error": "IntegrityError: CHECK constraint failed: event_type IN (...)",
  "c_status_after": [["RES-1","CONFIRMED"], ["RES-2","CONFIRMED"]],
  "c_events_written": 0
}
```

The whole quarantine transaction rolls back. **0 events written, 0 statuses
changed.** The claimed repair path is dead code against the shipped schema. This
alone falsifies the V19.2.2 claim that historical duplicate migration is closed.

### D01 — the migration does not survive a legacy duplicate DB; startup aborts

Scenario: schema present, unique index absent (a pre-index deployment), two
bookings sharing one `(journey_id, confirmation_ref)`.

```json
{
  "step1_legacy_index_present": false,
  "step1_legacy_duplicate_groups": [["J-LEGACY","REF-DUP",2]],
  "step2_ensure_schema_raised": true,
  "step2_error": "IntegrityError: UNIQUE constraint failed: transport_reservations.journey_id, transport_reservations.confirmation_ref",
  "step2_index_present_after_migration": false,
  "step2_duplicates_still_present": [["J-LEGACY","REF-DUP",2]]
}
```

`ensure_schema()` **raises**. The backend cannot start on such a database at all.
There is no migration, only a crash.

### The `except Exception: pass` is real and reachable in isolation

`app/db/session.py:69–78` (verbatim):

```python
try:
    connection.exec_driver_sql(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation "
        "ON transport_reservations(journey_id, confirmation_ref)"
    )
except Exception:
    # Existing historical duplicates are retained for read-only
    # compatibility; new confirmations still use the model/API
    # guard and clean databases receive the DB-level constraint.
    pass
```

Measured in isolation against the same duplicate DB:

```json
{
  "b_manual_index_creation": "raised IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: transport_reservations.journey_id, transport_reservations.confirmation_ref",
  "b_would_be_silently_swallowed_by_session_py": true,
  "b_index_present": false
}
```

Note also that `db/schema.sql` **line 902** already contains the same
non-partial `CREATE UNIQUE INDEX IF NOT EXISTS`, and it runs inside
`executescript` *before* the guarded block — which is why the failure surfaces as
a hard crash rather than a silent pass. Either way the outcome is wrong: the
guarded block swallows, the unguarded one aborts.

### D02 — uniqueness is not enforceable

`step2_index_present_after_migration = false`. No index, no constraint.

### D03 — new duplicates are accepted

```json
{ "step3_new_duplicate_accepted": true, "step3_new_duplicate_error": null }
```

A brand-new duplicate `(journey_id, confirmation_ref)` was written with no error.
**There is no DB-level serialization point for concurrent confirmation.**

### Why quarantine could never have worked anyway

Even if the Event insert were fixed, `quarantine_duplicate_confirmation_identities()`
only changes `row.status` and `row.draft_id`:

```python
row.status = QUARANTINE_MARKER
row.draft_id = None
```

It never changes `(journey_id, confirmation_ref)`, so a **non-partial** unique
index over those two columns still cannot be created while the losers remain.
The review's reading is confirmed.

---

## 9. Finding 7 — patch portability (FAIL, P01)

`git apply --check patches/V19_2_2_CODE.patch` against the exact declared clean
V19.2.1 baseline (fresh `git init` + commit of the extracted package,
`core.autocrlf=false`, **no path exclusions**):

```
exit=1
error: patch failed: contracts/openapi.yaml:1
error: contracts/openapi.yaml: patch does not apply
```

17 files are checked; **16 pass**, 1 fails.

| Experiment | Exit |
|---|---|
| full patch, clean baseline | **1** |
| `--exclude=contracts/openapi.yaml` | 0 |
| full patch, baseline `openapi.yaml` normalised to LF | 0 |

Line-ending measurements:

| File | bytes | CRLF | bare LF |
|---|---|---|---|
| baseline `contracts/openapi.yaml` | 89,911 | **792** | **1,551** (mixed) |
| Snapshot E `source/contracts/openapi.yaml` | 92,813 | 0 | 2,426 |
| `V19_2_2_CODE.patch` | 234,480 | 0 | 6,282 |

The patch was emitted against LF-normalised content while the declared baseline
carries mixed CRLF/LF. The claimed portable patch is **not** portable; the
exclusion experiment and the LF-normalisation experiment together isolate the
root cause exactly.

---

## 10. Reproduction

```
LAB = D:\moodle\CityNexus-Tools\WorkBuddy-V19.2.3-SnapshotE-DeltaGate-20260915
PY  = D:\moodle\CityNexus\.venv\Scripts\python.exe

cd %LAB%\_results
set PYTHONDONTWRITEBYTECODE=1
%PY% c4_probe.py              -> c4_probe.json              (Finding 1, T01-T05)
%PY% gate_probe.py            -> gate_probe.json            (Finding 1, gate)
%PY% recovery_probe.py        -> recovery_probe.json        (Findings 2,3,4)
%PY% db_migration_probe.py    -> db_migration_probe.json    (Finding 6)
%PY% db_migration_probe2.py   -> db_migration_probe2.json   (Finding 6, D00)

cd %LAB%\_p01_check
git apply --check --verbose "%LAB%\_snapshotE\...\patches\V19_2_2_CODE.patch"
                              -> ..\_results\p01_apply_check.txt   (Finding 7)
```

All probes import Snapshot E's own source from `%LAB%\_tree\backend`. The
authoritative main tree was read once (to verify the 17 files are identical) and
never written to.

---

## 11. What genuinely improved in Snapshot E (fair credit)

- T03: `MID_TRIP` is correctly pinned at its exact committed time with feasible
  surrounding POIs. This gate passes.
- S02: `/start` correctly returns `409 STALE_RECOMPOSE_REQUIRED` for expired or
  inconsistent frozen evidence, and selection revalidation raises. The final
  guard works.
- `contracts/openapi.yaml` in the package is internally LF-consistent, and the
  runtime/contract parity claim was not contradicted by anything measured here.
- The package contains no DB/log/cache payload pollution.

These do not offset six failing hard gates.

---

## 12. Required before any physical-phone trial

1. **C4 boundaries** — enforce ARRIVAL as a hard lower bound and DEPARTURE as a
   hard upper bound on every flexible activity, in both
   `anchor_schedule.py` and `feasibility.py`; add an explicit anchor-ordering
   invariant that returns a precise conflict (e.g. `ANCHOR_ORDER_INVALID`) for
   ARRIVAL-after-DEPARTURE; assert real ordered timestamps in the tests.
2. **Recovery governance** — replace `Continue without changes` with
   `Acknowledge warning`; persist the acknowledgement server-side; keep an
   unverified/infeasible banner until the recovery is genuinely resolved.
3. **Recovery lifecycle** — resolve the durable Event transactionally when a
   feasible replacement is selected/activated; make
   `recovery_state()` / `recovery_flags()` / `Event.status` / UI agree by
   construction (stop hardcoding `recovery_state: ACTIVE` in `recovery_flags`).
4. **NO_ALTERNATIVE** — persist the outcome of a real replan attempt; never infer
   it from `is_feasible is None`; feasibility-check candidates against the
   current HARD capability and active C4 set before advertising them.
5. **Stale candidates** — add a stale/recompose-required projection or filter to
   the list API and UI; keep selection revalidation as the final guard.
6. **Duplicate migration** — fix D00 (the quarantine Event's `event_type`
   violates the schema CHECK), make the quarantine actually free
   `(journey_id, confirmation_ref)`, remove the silent `except Exception: pass`,
   and make `ensure_schema()` survive a legacy duplicate DB instead of aborting.
7. **Patch portability** — normalise line endings deliberately and regenerate the
   release patch from the exact declared baseline so `git apply --check` passes
   with no exclusions.

---

## 13. Verdict

```
BLOCKED
```

Snapshot E is **not** accepted for the final code gate. Seven independent
findings: six hard gates fail, one new blocker (D00) discovered. Do not begin the
physical-device trial from V19.2.2.
