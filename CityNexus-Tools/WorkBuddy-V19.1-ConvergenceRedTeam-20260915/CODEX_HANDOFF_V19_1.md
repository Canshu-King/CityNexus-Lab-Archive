# CODEX_HANDOFF_V19_1.md

**From:** WorkBuddy V19.1 Convergence Red-Team (read-only, moving baseline)
**To:** Codex
**Baseline:** Snapshot A `2026-09-15 12:38:11`, Snapshot B `2026-09-15 13:05:57`
**Main tree:** **never modified.** All work in
`D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915`.
**Patch to apply:** `patches/V19_1_TESTS_ONLY.patch` — 4 files, 1,405 added lines,
`git apply --check` verified against the live main tree. Tests only; no production module.

---

## 0. What changed while we were measuring

Exactly one production file changed between Snapshot A and B, and both changes were yours:

| File | Change | Effect |
|---|---|---|
| `backend/app/stay_mobility.py` | bound `traveler_twin` at line 854 | **`GET /journeys/{id}/experience` 500 → 200** |
| `contracts/openapi.yaml` | added the 6 capability routes | **OpenAPI parity 131/137 → 137/137** |

Both are confirmed improvements and both are recorded as `FIXED_IN_CURRENT`. Nothing
regressed. **Every finding below is stated against the snapshot it was measured on.**

---

## 1. P0 — fix before merging the EAC patches

### P0-1 A user can select a plan the product will not let them book

```
POST /journeys/{id}/plans/generate                       -> 201 / 3 plans   (C4 ignored)
validate_plan_feasibility(each plan)                     -> feasible: false
                                                            ["LOCKED_COMMITMENT_LOST:<key>"]
POST /journeys/{id}/plans/{plan}/select                  -> 200             (C4 ignored)
POST /journeys/{id}/bookings                             -> 422 "selected plan is no longer
                                                            feasible: LOCKED_COMMITMENT_LOST:…"
```

Three paths, two definitions of feasibility:

| Path | C4 included |
|---|---|
| `services.py:847 generate_plans()` | **no** |
| `main.py:3693 select_plan()` | **no** |
| `main.py:4458 _assert_selected_plan_feasible()` | **yes** |

`validate_plan_feasibility()` already defaults to `include_active_c4=True`
(`services.py:706`); the two planning entry points simply never load commitments.
**Fix:** one shared constraint-assembly function used by all four paths, and run
`_assert_selected_plan_feasible()` inside `select`. Evidence:
`CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md` §1-2.

### P0-2 `POST /journeys/{id}/start` returns 500 for an ARRIVAL-anchored C4

```
main.py:4891 start_journey -> main.py:4766 _twin_snapshot
  -> runtime.py:54 capture_runtime_mobility_snapshot -> snapshot_capture.py:121
MobilitySnapshotCaptureError: KeyError: 'no routable coordinates for <uuid>'
```

The journey is left **stranded in `PLANNED`**. Only ARRIVAL-anchored C4s trigger it
(DEPARTURE and MID_TRIP pass). An ARRIVAL anchor stores `semantic_key = _uuid("place:…")`,
a random UUID with no coordinates. `GET /twin` on the same journey returns 200.
**Fix:** give an ARRIVAL anchor the arrival place's coordinates, or make `_twin_snapshot`
tolerate an unroutable key. Evidence: `CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md` §3.

### P0-3 A HARD accessibility need can be downgraded through the public API

```
POST /journeys/{id}/capabilities/confirm
     [{"code":"STEP_FREE_REQUIRED","severity":"STRONG"}]   -> 200
     persisted: severity="STRONG", class="HARD_ACCESSIBILITY_NEED"
POST /journeys/{id}/plans/generate                         -> 201 / 3 plans
```

18 of 24 probe cells accept a downgrade; omitting `severity` yields `STRONG` via
`default_severity(code, hard_asserted=False)`. The gate keys on **severity**, so the need
stops blocking.

**The EAC patch already fixes exactly this** and the fix is 6 lines
(`EAC_PATCH_VALIDATION.md` §5.1). Port it on its own:

```python
if code in HARD_ACCESSIBILITY_CODES:
    klass = capability_class_for(code)
    severity = "STRONG" if params.get("needs_confirmation") else "HARD"
```

### P0-4 EAC provider evidence: a toilet tag satisfies `STEP_FREE_REQUIRED`

If you merge `02_ACCESSIBILITY_EVIDENCE_REFERENCE.patch`, this comes with it:

| Place tags | `overall_state` | `STEP_FREE_REQUIRED` |
|---|---|---|
| `toilets:wheelchair=yes` | **ACCESSIBILITY_VERIFIED** | **satisfied → plan allowed** |
| `entrance:wheelchair=yes` | **ACCESSIBILITY_VERIFIED** | **satisfied → plan allowed** |
| `ramp=yes` / `elevator=yes` | ACCESSIBILITY_UNVERIFIED | blocked (correct) |
| `wheelchair=yes` + `step_count=5` | ACCESSIBILITY_CONFLICT | blocked (correct) |

Cause: `overall_accessibility_state()` (`integrations/accessibility/osm.py:284`) aggregates
**every** fact without filtering `subject`/`code`, and `feasibility.py:278` feeds that single
string into `accessibility_state()`. A `TOILET`-scoped fact is indistinguishable from a
place-level step-free verification. Confirmed live on both the read endpoint **and** the gate.
**Fix:** project step-free from `{WHEELCHAIR_ACCESS, ENTRANCE_STEP_FREE}` only. Evidence:
`ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md` §1-3.

### P0-5 ~20 raw-language cases manufacture a HARD need that does not exist

Identical in the current tree **and** in EAC:

| Class | Cases | Both emit HARD | Examples |
|---|---|---|---|
| denial | 28 | **11** | `I don't use a wheelchair`, `I am not a wheelchair user` |
| third party | 6 | **6** | `my friend needs a wheelchair, not me`, `我妈妈坐轮椅` |
| hypothetical | 3 | **3** | `if I get tired I might need a wheelchair` |
| facility description | 5 | **2** | `车站有无障碍厕所` |

Including **both sentences the EAC-Aware Update named**:

- `I don't need a wheelchair, I can walk` → `STEP_FREE_REQUIRED` HARD
- `朋友说我可能需要轮椅，但我不这么认为` → `STEP_FREE_REQUIRED` HARD

`_NEGATED_MARKERS` is **byte-identical** between the two implementations and is applied
**text-globally**. EAC's `_split_clauses()` fixed the erase direction but not this one.
**Fix:** a per-clause subject/polarity guard before the hard-marker check — third-party
subject, explicit denial, hypothetical marker (`needs_confirmation`), or facility subject must
not assert a traveller capability. Evidence: `SEMANTIC_HARDPAIR_RESULTS.md` §2.2.

---

## 2. P1 — correctness and explainability

| # | Finding | Where | Evidence |
|---|---|---|---|
| P1-1 | Numeric limits are **never compared** — `max_m = 10**12` behaves like 300 m, every case 422s on missing evidence | `feasibility.py` walking branch | `NUMERIC_TIME_BOUNDARY_RESULTS.md` §1 |
| P1-2 | 7 gate failure-code families collapse to **one** client message; `failures` is discarded | `services.py:1003`; `main.py` never reads `failures` | `FEASIBILITY_EVIDENCE_RESULTS.md` §4 |
| P1-3 | `REST_EVERY_MIN`/`TOILET_BREAK_EVERY_MIN` read `max_min`; the **correct** key is accepted-but-unenforced, a wrong key 422s | `feasibility.py:701-703` | `NUMERIC_TIME_BOUNDARY_RESULTS.md` §3 |
| P1-4 | Evidence semantics asymmetric: `STROLLER`/`LARGE_LUGGAGE` **fail open**, `STEP_FREE_REQUIRED`/`AVOID_STAIRS` fail closed | `feasibility.py:291-296` | `FEASIBILITY_EVIDENCE_RESULTS.md` §3 |
| P1-5 | A TRAVELER-scoped need leaves `constraints: []` yet blocks **every** future journey | `_journey_constraints_with_capabilities()` | `SCOPE_AUDIT_RESULTS.md` §3 |
| P1-6 | Permanent language (`终身`/`长期`/`permanently`) never yields `TRAVELER` scope — 0/15 in both implementations | `extract_capabilities_from_text` | `SCOPE_AUDIT_RESULTS.md` §2 |
| P1-7 | A mid-trip HARD capability change produces **no** replan and no warning (`replan_proposals: 0`) | Guardian path not wired to capability changes | `MIDTRIP_RECOVERY_RESULTS.md` §3 |
| P1-8 | Stale `CANDIDATE` plans remain listed after regeneration fails feasibility | plan lifecycle | `FEASIBILITY_EVIDENCE_RESULTS.md` §5 |
| P1-9 | Duplicate `confirmation_ref` creates two separate C4s | `inbox/import` | `CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md` §5 |
| P1-10 | Deactivated capability rows are still returned (with `active: false`) | listing endpoint | `SCOPE_AUDIT_RESULTS.md` §4 |

---

## 3. P1 — defects that would arrive **with** the EAC patches

Do not merge these as-is:

| # | Defect | Location | Evidence |
|---|---|---|---|
| E-1 | `canonicalize_capabilities` dedupes by **`code` only** — TRAVELER + JOURNEY `AVOID_STAIRS` collapse to one row with the wrong scope and the other row's params | `capabilities.py` `merged: dict[str, CapabilityItem]` | `CAPABILITY_CANONICALIZATION_RESULTS.md` §4.3 |
| E-2 | Duplicate merge lets the **looser** numeric limit win (`400` + `800` → `800`) | `merged_params = {**existing, **item}` | §4.4 |
| E-3 | Numeric parser has **no range check** — `0 m`, `-5 m`, `10000 m` become HARD `MAX_WALKING_PER_LEG_M` | `_number_before()` | `NUMERIC_TIME_BOUNDARY_RESULTS.md` §4 |
| E-4 | Over-extraction: a daily limit and a duration limit each also emit `MAX_WALKING_PER_LEG_M` | same | same |
| E-5 | Hedged wishes become capabilities (`中午能休息一下就更好了` → `MIDDAY_REST_WINDOW`) | same | same |
| E-6 | `confirm A` → `confirm B` **loses A** — `_replace_capability_rows()` overwrites the whole scope instead of upserting | `main.py` | `SCOPE_AUDIT_RESULTS.md` §5.1 |
| E-7 | Concurrent confirm **silently loses one capability**, and which one varies between runs (all three calls return 200) | same | §5.2 |
| E-8 | `/capabilities/catalog` advertises `default_severity: "STRONG"` for `STEP_FREE_REQUIRED` while the server stores `HARD` | `main.py:1857` + `default_severity()` | `EAC_PATCH_VALIDATION.md` §7.1 |
| E-9 | Read endpoint and gate **disagree** about the same place — 6 of 9 shapes, 3 in the dangerous direction | `main.py:2049` vs `feasibility.py:257` | `ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md` §4 |
| E-10 | `place.tags_json` is parsed by the read endpoint but never read by the gate → "verified" in the UI, blocked in planning | `models.py:468` | same |
| E-11 | Route-level `ROUTE_STEP_FREE` unknown is reported but never consulted — `generate` returns 201 | `main.py:2134` | same §5 |
| E-12 | The EAC patch adds 6 capability/accessibility routes and updates `contracts/openapi.yaml` with **none** — merging regresses parity from 137/137 to 12 missing | `contracts/openapi.yaml` | `OPENAPI_DRIFT_RESULTS.md` §4.3 |

---

## 4. P2 — accessibility debt in the UI

| Measure | Value |
|---|---|
| Status nodes with no accessible name | **248** |
| Interactive controls with no accessible name | **40** |
| Clipped text nodes | **24** |
| Colour-only status nodes | **0** (good) |
| Focus visibility | 16/16 tabbable elements, 3 px solid outline (good) |
| 200 % zoom horizontal overflow | 0/8 routes (good) |

Evidence: `WEB_MOBILE_RESULTS.md` §2-3.

---

## 5. What to keep

- **`_CAPABILITY_GATE_CODES`** and `_capability_failure_for_record()` — the gate now genuinely
  interprets capability. `UNKNOWN != ACCESSIBLE` holds: missing / UNKNOWN / CONFLICT all 422.
- **OpenAPI parity** — `contracts/openapi.yaml` is now 137/137 with the runtime. Wire
  `tools/verify_openapi_parity.py` into CI as a blocking gate; it already exits 1 on drift.
- **Hermes** — no capability tool in v1 (6) or v2 (11); `any_capability_tool: false`. The
  agent surface is correctly read-only w.r.t. capability context.
- **`_split_clauses()` in EAC** — it recovers 32 cases the current tree loses, with **0**
  regressions. Port it, then add the P0-5 guard on top.
- **The focused contract suite** — 107 assertions, 28 pass / 79 fail, **identical on both
  snapshots**; 16 defect probes flipped to passing this round and **no `REGRESSED` verdicts**.

---

## 6. How to reproduce

```bash
LAB="D:/moodle/CityNexus-Tools/WorkBuddy-V19.1-ConvergenceRedTeam-20260915"

# apply the tests-only patch to the main tree
git apply --check "$LAB/patches/V19_1_TESTS_ONLY.patch"
git apply         "$LAB/patches/V19_1_TESTS_ONLY.patch"

# focused contract suite (in both snapshots and the main tree)
cd backend && python -m pytest tests/test_v191_capability_contract.py \
    tests/test_v19_postfix_capability_contract.py \
    tests/test_v191_eac_evidence_scope.py -q

# re-measure every finding in this handoff
PYTHONDONTWRITEBYTECODE=1 python "$LAB/tools/v191_probe_accessibility_evidence.py"
PYTHONDONTWRITEBYTECODE=1 python "$LAB/tools/v191_eac_differential.py"
PYTHONDONTWRITEBYTECODE=1 python "$LAB/tools/v191_probe_openapi_drift.py"
PYTHONDONTWRITEBYTECODE=1 python "$LAB/tools/v191_probe_eac_live.py"
```

**Read-only guarantee.** Snapshots are narrow include-list copies; every Python invocation used
`PYTHONDONTWRITEBYTECODE=1`; the EAC lab backend was imported for its code only and pointed at
a throwaway SQLite file inside the lab. `git apply --check` was used, never `git apply`.
`D:\moodle\CityNexus` is byte-identical to its state at `13:05:57` except for Codex's own edits.

---

# ADDENDUM — after `CODEX_V19_1_IF_AVAILABLE` (Snapshot C, 2026-09-15 13:47:07)

Everything above was written before Codex V19.1 landed. This addendum is the
delta: what Codex already fixed (so do not redo it), what regressed, and what is
still open. Full detail in `CODEX_V19_1_DELTA_RESULTS.md`.

## 7. Already fixed by Codex V19.1 — do not re-do

| Finding from §1/§3 above | Status on Snapshot C |
|---|---|
| D1 — HARD accessibility severity could be downgraded | **FIXED** — 21/21 cells force `HARD` |
| D3 — duplicate capability codes not merged | **FIXED** — 8/8 |
| D6 — gate did not interpret capability | **FIXED** — `_CAPABILITY_GATE_CODES` wired |
| Clause-local negation / history erasing a live need | **FIXED** — 18 of 20 |
| `I don't need a wheelchair, I can walk` false-HARD | **FIXED** |
| `朋友说我可能需要轮椅，但我不这么认为` false-HARD | **FIXED** |
| Facility tag (`toilets:wheelchair=yes`) satisfying `STEP_FREE_REQUIRED` | **FIXED** — new `evaluate_accessibility_requirement(code, facts)` |
| `overall_state` cross-subject leak | **FIXED** — the generic `accessibility_state(metadata)` call is gone |
| Route step-free without route evidence | **FIXED** — stays `NEEDS_LIVE_EVIDENCE` |
| Duplicate merge weakening the numeric limit | **FIXED** — the stricter `max_m` wins |
| `/journeys/{id}/experience` → 500 | **FIXED** at 12:40:39 (`stay_mobility.py`) |

Suite result: **119 passed / 54 failed / 15 skipped** on C, up from
37 / 106 / 45 on A and B. **No guard regressed.**

## 8. NEW regression introduced by Codex V19.1 — fix this first

**Cross-scope dedup collapse.** `canonicalize_capabilities` keys its dedup map on
`code` alone:

```python
# backend/app/capabilities.py:329, 365
seen: dict[str, dict[str, Any]] = {}
...
previous = seen.get(code)          # <-- scope is NOT part of the key
```

```
B: [AVOID_STAIRS HARD TRAVELER, AVOID_STAIRS HARD JOURNEY] -> 2 rows
C: -> 1 row  {scope: TRAVELER, params: {note: traveler}}    # JOURNEY row + params discarded
```

This is the same defect the EAC patch introduced, reproduced independently.
It is **latent** today only because D7 is still open (natural language almost always
resolves to `JOURNEY`, so there is usually one row to collapse). It becomes silent
data loss the moment D7 is fixed. Fix: `seen` keyed on `(scope, code)`.

Assertion: `test_v191_eac_defect_merge_respects_scope` — `PASSED` on A/B,
`FAILED` on C. It is the only regression in the 188-assertion suite.

## 9. Still open on Codex V19.1

| # | Finding | Verdict | Evidence |
|---|---|---|---|
| 1 | **P0** ARRIVAL-anchored C4 → `POST /start` 500, journey stranded in `PLANNED` | `STILL_REPRODUCIBLE` | `evidence/c4_start_c.json` |
| 2 | **P0** `generate`/`select` ignore the C4; `POST /bookings` enforces it | `STILL_REPRODUCIBLE` | `evidence/c4_gate_c.json` |
| 3 | **NEW** cross-scope dedup collapse | `REGRESSED` | §8 above |
| 4 | `wheelchair=yes + step_count=5` → `UNVERIFIED`, not `CONFLICT` | `STILL_REPRODUCIBLE` | `evidence/codex_v19_1_evidence.json` |
| 5 | list/tuple used as a mapping **value** is silently dropped | `STILL_REPRODUCIBLE` | same |
| 6 | `step_free_verified` at metadata top level is dropped | `STILL_REPRODUCIBLE` | same |
| 7 | 9 residual false-HARD (third-party / facility / speculation) | `STILL_REPRODUCIBLE` | §10 below |
| 8 | D4 walking numerics — 19 of 25 forms yield nothing | `STILL_REPRODUCIBLE` | `postfix_classification.json` |
| 9 | D5 rest / nap windows — 6 residual | `STILL_REPRODUCIBLE` | same |
| 10 | D7 TRAVELER scope unreachable from text | `STILL_REPRODUCIBLE` | same |
| 11 | Numeric params enforced but never validated (`max_m: 10**12` blocks like `max_m: 500`) | `STILL_REPRODUCIBLE` | `NUMERIC_TIME_BOUNDARY_RESULTS.md` |
| 12 | Gate computes rich codes; client sees one opaque message | `STILL_REPRODUCIBLE` | `FEASIBILITY_EVIDENCE_RESULTS.md` |
| 13 | Hermes exposes no capability tool (`v1: 6`, `v2: 11`) | `STILL_REPRODUCIBLE` | `HERMES_CAPABILITY_RESULTS.md` |
| 14 | Model capability codes dropped silently (98 of 103) | `STILL_REPRODUCIBLE` | `SEMANTIC_HARDPAIR_RESULTS.md` |

## 10. The 9 residual false-HARD sentences (fix list for the guard)

Verified live against Snapshot C's `extract_capabilities_from_text` — all still
produce HARD `STEP_FREE_REQUIRED`:

```
my friend needs a wheelchair, not me      -> STEP_FREE_REQUIRED   (third party, "not me")
my mother uses a wheelchair               -> STEP_FREE_REQUIRED   (third party)
我朋友需要轮椅                              -> STEP_FREE_REQUIRED   (third party)
我妈妈坐轮椅                                -> STEP_FREE_REQUIRED   (third party)
I am not a wheelchair user                -> STEP_FREE_REQUIRED   (first-person denial)
the station has an accessible toilet      -> STEP_FREE_REQUIRED   (facility description)
车站有无障碍厕所                             -> STEP_FREE_REQUIRED   (facility description)
说不定到时候我需要轮椅                        -> STEP_FREE_REQUIRED   (speculation)
if I end up in a wheelchair I'll tell you -> STEP_FREE_REQUIRED   (conditional, deferred)
```

Codex already handles the *same classes* elsewhere (`my colleague said I might need
a wheelchair` ✅, `同事说我也许需要轮椅` ✅, `if I get tired I might need a wheelchair` ✅,
`no stairs problem for me, I'm fine` ✅). The gap is marker coverage:

- **relational subject** not in the guard: `my friend`, `my mother`, `my father`,
  `my colleague`, `我朋友`, `我妈妈`, `我父亲`, `我同事`, plus the `not me` tail
- **first-person denial** form `I am not a … user`
- **possibility marker without a modal verb**: `说不定`, `搞不好`, `if I end up`,
  `I'll tell you`

All nine are already encoded as failing regression tests in
`patches/V19_1_TESTS_ONLY.patch`
(`test_v191_eac_defect_third_party_does_not_create_need`,
`test_v191_eac_defect_denial_does_not_create_need`,
`test_v191_eac_defect_facility_description_is_not_a_need`,
`test_v191_eac_defect_speculation_does_not_create_hard`).

## 11. Revised read-only guarantee

`D:/moodle/CityNexus` is byte-identical to its state at `13:47:07` except for
**Codex's own edits**. Verified by mtime sweep: the only file changed after
Snapshot C was `frontend/src/styles.css` at 13:54:24 (Codex). No lab test file,
config or cache exists anywhere under the main tree; the Web/Mobile lab's
`vite.v191-local.config.ts` and `node_modules` junction live inside
`snapshot_b/frontend/`, and Vite's dependency cache was directed to `%TEMP%`.

## 12. Re-measure the delta check

```bash
LAB="D:/moodle/CityNexus-Tools/WorkBuddy-V19.1-ConvergenceRedTeam-20260915"
cd "$LAB"

PYTHONDONTWRITEBYTECODE=1 python tools/snapshot.py C          # read-only copy of the live tree
PYTHONDONTWRITEBYTECODE=1 python tools/sync_tests.py C
cd snapshot_c/backend && PYTHONDONTWRITEBYTECODE=1 python -m pytest \
    tests/test_v191_capability_contract.py \
    tests/test_v19_postfix_capability_contract.py \
    tests/test_v191_eac_evidence_scope.py -q
cd "$LAB"

PYTHONDONTWRITEBYTECODE=1 python tools/v191_classify_postfix.py
PYTHONDONTWRITEBYTECODE=1 python tools/v191_probe_codex_v191_evidence.py
PYTHONDONTWRITEBYTECODE=1 python tools/v191_codex_corpus_delta.py
PYTHONDONTWRITEBYTECODE=1 python tools/v191_probe_c4_gate.py C
PYTHONDONTWRITEBYTECODE=1 python tools/v191_probe_c4_start.py C
```
