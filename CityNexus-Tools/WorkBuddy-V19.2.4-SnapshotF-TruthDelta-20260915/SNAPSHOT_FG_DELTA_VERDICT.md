# Snapshot F / G — Narrow Read-Only Truth Delta & Verdict

**Audit date:** 2026-09-15 → 2026-09-16
**Lab:** `D:\moodle\CityNexus-Tools\WorkBuddy-V19.2.4-SnapshotF-TruthDelta-20260915`
**Discipline:** read-only; authoritative `D:\moodle\CityNexus` main tree was **never modified**.
**Method:** for each snapshot, `_treeF` / `_treeG` = main-tree backend copy + the snapshot's
21 authoritative files overlaid (verified byte-identical per sha256). Probes run with
`PYTHONDONTWRITEBYTECODE=1` and `CITYNEXUS_TREE` pointed at the overlay tree.

---

## 0. Snapshot inventory (frozen & sha256-verified)

| Snapshot | Package | sha256 |
|---|---|---|
| **F** (V19.2.3 final) | `CityNexus-EAC-V19.2.3-FinalShadowTrial-CodeGate-20260915.zip` | `8c64a7b7…25cc0b` (inbox) |
| **G** (V19.2.4 landed mid-run) | `CityNexus-EAC-V19.2.4-FinalTruth-CodeGate-20260915.zip` | `b6c521c1…0b017` (inbox) |

G landed during the run (found in `D:\moodle\_v1922_work\`), so it was frozen as
**Snapshot G** and a targeted delta was performed on the three findings — *not* a restart
from Snapshot E. (The prior Snapshot-E BLOCKED verdict was **not** reused as a Snapshot-F verdict.)

---

## 1. Snapshot F (V19.2.3) — truth delta result: **BLOCKED**

The shared deterministic C4 gate, the recovery durable-truth, and the reservation
quarantine helper were each independently replayed against the submitted F source.

### 1.1 Shared C4 feasibility gate — F01–F03 FAIL
Probe: `probes/v1924_truth_probe.py` (provided) → `F_truth_probe.json`

| Case | Expected | Snapshot F actual | Verdict |
|---|---|---|---|
| F01 pre-arrival activity | reject | `passed=true`, `failures=[]` | **FAIL** |
| F02 post-departure activity | reject | `passed=true`, `failures=[]` | **FAIL** |
| F03 ARRIVAL after DEPARTURE | reject (precise C4 conflict) | `passed=true`, `failures=[]` | **FAIL** |
| F04 valid control | pass | `passed=true` | PASS |

Root cause (unchanged from Snapshot E): `app/replanning/feasibility.py::evaluate_feasibility`
only *pins* anchors via the window-widening loop; it never enforces the ARRIVAL/DEPARTURE
boundary against flexible city activity. The narrow scheduler (`anchor_schedule.py`) was
already fixed (see §4), so plan **generation** may reject, but the shared gate used by
generate/select/start/revalidation still accepts impossible plans.

### 1.2 Recovery durable truth — R01–R04 FAIL
Probe: `F_recovery_probe.py` → `F_recovery_results.json`

| ID | Requirement | Snapshot F | Verdict |
|---|---|---|---|
| R01 | `recovery_state(is_feasible=True)` must NOT report RESOLVED while Event is open | projects `RESOLVED`, Event still `DETECTED` | **FAIL** |
| R02 | Event.status / experience / flags must agree | `DETECTED` vs `RESOLVED` vs `RECOVERY_REQUIRED` (3-way clash) | **FAIL** |
| R03 | GET /experience must not mutate durable state | handler calls `resolve_recovery_events` (uncommitted → phantom resolution) | **FAIL** |
| R04 | candidates only from validated replan | exposes arbitrary `CANDIDATE` rows; empty-list `or` fallback bug | **FAIL** |

R03 detail: `main.py` `get_journey_experience` (2297) calls
`resolve_recovery_events(session, journey)` (2320) on a GET. `get_session()` never commits
(close-only), so the resolution is rolled back → phone sees no recovery for that request, every
later request still sees the open event. Worse, because the broken F01–F03 gate reports the
impossible plan `is_feasible=True`, the same GET would "resolve" recovery on a plan that is
actually infeasible — the two defects compose.

### 1.3 Reservation quarantine helper — D02–D03 FAIL (D01 green)
Probe: `F_reservation_probe.py` → `F_reservation_results.json`

| ID | Requirement | Snapshot F | Verdict |
|---|---|---|---|
| D01 | startup migration on legacy dup DB stays green | quarantine + valid `USER_CHANGE` event | PASS |
| D02 | ORM helper writes a valid audit Event | helper uses `event_type='RESERVATION_IDENTITY_DUPLICATE'` → CHECK violation → transaction rolls back (0 quarantined, 0 events) | **FAIL** |
| D03 | idempotent / excludes quarantined | `detect_…` never excludes quarantined rows → re-reports every run | **FAIL** |

Note the inconsistency: the SQL-level startup migration was fixed to emit `USER_CHANGE`, but the
ORM helper `quarantine_duplicate_confirmation_identities()` still emits the invalid type.

### 1.4 Snapshot F verdict
Multiple independent findings (F01–F03, R01–R04, D02–D03) reproduced with executable evidence
→ **BLOCKED**.

---

## 2. Snapshot G (V19.2.4) — targeted delta result: **ALL RESOLVED**

EAC V19.2.4 landed mid-run. Same three probes re-pointed at `_treeG` (Snapshot G overlay).

### 2.1 Shared C4 gate — F01–F04 PASS
`G_truth_probe.json` → exit 0, 4/4 PASS. `evaluate_feasibility` now emits
`C4_ACTIVITY_BEFORE_ARRIVAL`, `C4_ACTIVITY_AFTER_DEPARTURE`, `C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE`.

### 2.2 Recovery durable truth — R01–R04 PASS
`G_recovery_results.json`

| ID | Snapshot G | Verdict |
|---|---|---|
| R01 | `is_feasible=True` → `RECOVERY_REQUIRED` (not RESOLVED) while Event open | PASS |
| R02 | experience + flags agree (`RECOVERY_REQUIRED`); no RESOLVED-without-resolution | PASS |
| R03 | `get_journey_experience` is a pure projection (no `resolve_recovery_events` call; source-scan confirmed); Event unchanged | PASS |
| R04 | no replan → 0 candidates; replan w/ 0 feasible → 0 candidates (`no_alternative`, no arbitrary rows) | PASS |

### 2.3 Reservation quarantine helper — D01–D03 PASS
`G_reservation_results.json`

| ID | Snapshot G | Verdict |
|---|---|---|
| D01 | migration stays green | PASS |
| D02 | helper now emits valid `USER_CHANGE` event; loser quarantined; audit Event written | PASS |
| D03 | `detect_…` excludes quarantined rows → 0 re-detected on second pass → idempotent | PASS |

### 2.4 Patch portability (P01) — GREEN
`git apply --check` of `patches/V19_2_4_GPT_VERIFIED_CLOSURE.patch` against Snapshot F source
→ **APPLY_CHECK_OK**. The patch touches exactly the four modules carrying the F/R/D defects
(feasibility / hard_recovery / main / reservation_identity).

### 2.5 Submitter caveat noted (not a blocker)
The Road-Prep instructed a *semantic* port, not a literal one: the literal starter patch broke a
V19.2 contract test (an 08:00 DEPARTURE on a 09:00 draft Journey must stay plannable). The
port keeps anchor-window widening for *anchor placement* but keeps ARRIVAL/DEPARTURE boundaries
constraining flexible activity. My F01–F04 (4/4 PASS) is consistent with this port.

---

## 3. Already-green areas re-confirmed (targeted only, no full corpus)

| Check | Result |
|---|---|
| Governed Acknowledge wired | frontend `RecoveryRequiredPanel.tsx` `acknowledge()` → `POST /recovery/acknowledge` (main.py:2024); backend helper correct (ACKNOWLEDGED ≠ RESOLVED) |
| Scheduler ARRIVAL/DEPARTURE boundaries | `F_c4_scheduler_probe.py` → T01–T05 all PASS |
| Startup partial unique-index migration | D01 PASS (both snapshots) |
| Patch portability claim truthful | P01 `git apply --check` OK |
| Stale start blocked | `/start` (main.py:5145) 409 guards: already-ACTIVE / not-PLANNED / missing-SELECTED / stale evidence |

---

## 4. Final verdict

**SNAPSHOT_G_ACCEPTED_FOR_PHYSICAL_TRIAL_PRECHECK**

- Snapshot F (V19.2.3) alone would have been **BLOCKED** (F01–F03, R01–R04, D02–D03 all reproduced).
- Snapshot G (V19.2.4) landed and the targeted delta proves all three findings are **closed
  with executable evidence** (F01–F04, R01–R04, D01–D03 all PASS), and the already-green areas
  remain green.
- **A01 — physical device** is explicitly **NOT** part of this code gate and must remain
  **PENDING**. This is a narrow truth delta, not a full broad-regression re-audit; the
  submitter's claim of 61/61 contract + 13/13 closure + 0 new broad failures was *not*
  independently re-run here and is carried forward, not verified.

### Deliverables in this package
- `SNAPSHOT_FG_DELTA_VERDICT.md` (this file)
- `_results/v1924_truth_probe.py` (provided) + `F_truth_probe.json`, `G_truth_probe.json`
- `_results/F_recovery_probe.py` + `F_recovery_results.json`, `G_recovery_results.json`
- `_results/F_reservation_probe.py` + `F_reservation_results.json`, `G_reservation_results.json`
- `_results/F_c4_scheduler_probe.py` + `F_c4_results.txt` (F05 scheduler boundaries)
- `_inbox/` frozen zip copies + sha256 manifests
- `_snapshotF/`, `_snapshotG/` frozen authoritative sources
