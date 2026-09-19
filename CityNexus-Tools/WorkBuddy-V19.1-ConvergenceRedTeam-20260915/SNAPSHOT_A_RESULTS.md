# SNAPSHOT_A_RESULTS.md

**Snapshot A:** taken `2026-09-15 12:38:11`
**Path:** `snapshot_a/` (narrow include-list copy of `D:\moodle\CityNexus`, read-only)
**Manifest:** `evidence/snapshot_a.json`

| Property | Value |
|---|---|
| Files copied | 339 |
| `import app.main` | **OK** (`import_status.ok: true`, `missing_symbols: {}`) |
| `app/capabilities.py` sha256_16 | `7e3ff4cb3a85b7b6` (15,283 bytes, mtime `09-15 10:53:32`) |
| Backend test files present | 86 |
| Vite config present | yes (`frontend/vite.config.ts` added to the include list) |
| Focused contract suite | **28 passed / 79 failed** (107 tests) |
| Post-fix assertion classification | 16 `FIXED_IN_CURRENT`, 0 `REGRESSED`, 13/13 `GUARD_HOLDS` |

---

## 1. D0 — the import blocker is fixed

The previous round's headline defect — `ImportError: cannot import name 'capability_payload'
from 'app.capabilities'` at `backend/app/main.py:66` — **no longer reproduces at Snapshot A**.
Codex moved the function to `app/execution/traveler_twin.py:160` at `12:37:09`, one minute
before this snapshot. `import app.main` succeeds and an AST sweep finds no other missing
symbol. Tag: `FIXED_IN_CURRENT`.

This is why the brief's "first step: check `import app.main`" mattered — the whole baseline
was unimportable an hour earlier.

---

## 2. NEW P0 found at Snapshot A — `/experience` returns HTTP 500

`GET /api/v1/journeys/{id}/experience` → **500** at Snapshot A.

```
NameError: name 'traveler_twin' is not defined
  app/stay_mobility.py:923   experience_payload()
```

`experience_payload()` (line 851) referenced `traveler_twin` at line 923, but the name was
bound at line **617 in a different function**. Any journey with a capability set could not
load its experience surface. Tag: `NEW`, `FIXED_IN_CURRENT` at Snapshot B (§SNAPSHOT_B_RESULTS).

---

## 3. Focused contract suite — identical failure set at A and B

```
backend/tests/test_v191_capability_contract.py          (guards + defect probes)
backend/tests/test_v19_postfix_capability_contract.py   (previous round's 23 assertions)
```

`evidence/_junit_a.xml` → **28 passed / 79 failed**. The same byte-identical test stream
(`tools/sync_tests.py` records per-file sha256) produces the **same** 107 outcomes at
Snapshot B, so every failure below is a property of the code, not of the snapshot.

### 3.1 Delta-target classification (`evidence/postfix_classification.json`)

| Target | `FIXED_IN_CURRENT` | `STILL_REPRODUCIBLE` |
|---|---|---|
| D1 HARD downgrade guard | 2 | 19 |
| D2 clause-local negation / history | 2 | 18 |
| D3 duplicate capability codes | 0 | 8 |
| D4 walking / rest numerics | 6 | 19 |
| D5 rest / nap time windows | 2 | 6 |
| D6 gate interprets capability | 2 | 1 |
| D7 TRAVELER scope | 2 | 7 |
| guards | 13 (`GUARD_HOLDS`) | 0 |
| **total** | **16 defect probes now pass** | **79** |

**No `REGRESSED` verdicts.** 16 defect probes that failed in the previous round now pass:
`d1[HARD-*]`, `d2c`, `d2d`, four malformed `d4` cases, `d4[en_under 400]`,
`d5[invalid window]`, `d5[naptime 13:00-15:00]`, two `d7[this-trip zh]`, `d6a`, `d6c`,
`d4a[REST_EVERY_MIN]`.

---

## 4. NEW P0 at Snapshot A — the product lets the user select an unusable plan

Measured end-to-end at Snapshot A (`evidence/c4_gate_a.json`):

| Step | Result |
|---|---|
| `POST /journeys/{id}/plans/generate` | **201 / 3 plans** — C4 ignored |
| `validate_plan_feasibility()` on all 3 plans | `feasible: false`, `["LOCKED_COMMITMENT_LOST:ea06631e-f5b4-598a-8a96-2483c271a825"]` |
| `POST /journeys/{id}/plans/{plan}/select` | **200** — C4 ignored again |
| `POST /journeys/{id}/bookings` on that plan | **422** `"selected plan is no longer feasible: LOCKED_COMMITMENT_LOST:…"` |

`generator_produced_plans_the_validator_rejects: true`,
`generation_includes_locked_commitment: false`. Three code paths, two definitions of
feasibility. See `CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md`.

## 5. NEW P0 at Snapshot A — `start` crashes on an ARRIVAL-anchored C4

`POST /journeys/{id}/start` → **500**, journey stranded in `PLANNED`:

```
MobilitySnapshotCaptureError: mobility fact unavailable for place-old-town|ea06631e-…
  main.py:4891 start_journey -> main.py:4766 _twin_snapshot
  -> runtime.py:54 capture_runtime_mobility_snapshot -> snapshot_capture.py:121
KeyError: 'no routable coordinates for ea06631e-f5b4-598a-8a96-2483c271a825'
```

Only ARRIVAL-anchored C4s trigger it; DEPARTURE and MID_TRIP pass. `GET /twin` on the same
journey returns 200.

## 6. NEW at Snapshot A — numeric limits are never compared

All 15 walking cases and all 12 window cases return **422 / 0 plans**, including
`max_m = 10**12` and a whole-day `00:00–23:59` window — because the mock mobility matrix has
no walking distances, so every leg emits `NEEDS_LIVE_EVIDENCE:MAX_WALKING_PER_LEG_M:{pair}`.
"Enforced" is really "always blocked".

## 7. A/B probe diff (Snapshot A as the reference side)

| Probe | A vs B |
|---|---|
| `canonicalization` | 494 / 495 leaves identical |
| `boundaries` | 661 / 662 identical |
| `gate_codes` | 110 / 111 identical |
| `c4_start` | 5 / 7 (only traceback text differs) |
| `c4_gate` | 26 / 28 (only `booking_body` trace id) |
| `lifecycle` | **11 differences — all `experience_*`** |
| `commitment_conflict` | **12 differences — all `experience_*`** |

Every delta is downstream of the single `stay_mobility.py` fix. See `SNAPSHOT_B_RESULTS.md`.
