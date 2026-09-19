# WORKBUDDY_V19_1_CONVERGENCE_REPORT.md

**CityNexus WorkBuddy V19.1 — Moving-Baseline Convergence Red-Team**

| | |
|---|---|
| Round | V19.1 (original 6H road-prep brief **+** EAC-Aware Validation Update) |
| Lab root | `D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915` |
| Subject | `D:\moodle\CityNexus` — **read-only throughout; never modified** |
| Snapshots | A `12:38:11` · B `13:05:57` · C `13:47:07` |
| Focused suite | 188 assertions, byte-identical test bytes across A/B/C |
| Semantic corpus | 182 discriminating raw-language cases (brief asked 150–220) |
| Main tree touched | **No** (verified by mtime sweep; `PYTHONDONTWRITEBYTECODE=1` on every invocation) |

---

## 0. Executive summary

Five findings matter.

**1. The moving-baseline protocol earned its keep.** Snapshot A caught
`GET /journeys/{id}/experience` returning **HTTP 500** (`NameError: traveler_twin`).
Twenty minutes later Codex had fixed it and Snapshot B showed **200**. Without two
snapshots this round would have reported a dead defect. Every A→B delta is recorded
and attributed in `SNAPSHOT_A_RESULTS.md` / `SNAPSHOT_B_RESULTS.md`.

**2. The two sentences the brief singled out are broken in EAC and fixed in Codex.**
The EAC-Aware Update said an independent review confirmed the **EAC capability
patch** still produces a wrong HARD need for `I don't need a wheelchair, I can walk`
and `朋友说我可能需要轮椅，但我不这么认为`. Measured on all four trees: **EAC still
produces the false HARD; FINAL_V19 still produces it; Codex V19.1 does not.** This
is the round's headline result — and it is the opposite of what the EAC report
implies.

**3. The EAC reference implementation fails the very demand the brief names.**
`toilets:wheelchair=yes` **is** promoted to a verified step-free requirement by EAC:
its fact carries `subject: TOILET`, but `overall_accessibility_state()` aggregates
every fact without reading `subject` or `code`, and `accessibility_state()` then
reads only that aggregate. The `subject` field is recorded and never consulted.
Codex V19.1's independent per-requirement evaluator gets this right.

**4. Two P0 defects survive into Codex V19.1.** An ARRIVAL-anchored C4 commitment
still makes `POST /start` return **500** and strands the journey in `PLANNED`; and
`generate`/`select` still ignore the C4 while `POST /bookings` enforces it, so the
product lets a traveller select a plan it will then refuse to let them use.

**5. Codex V19.1 fixed 52 of 106 failing assertions and introduced exactly one
regression** — its new duplicate-code dedup keys on `code` alone, so a
`TRAVELER`-scoped and a `JOURNEY`-scoped need of the same code collapse into one row
and the journey-scoped one is silently discarded.

---

## 1. What was asked, and what was delivered

### 1.1 Original V19.1 brief

| Requirement | Status |
|---|---|
| Do **not** modify the main tree | ✅ verified by mtime sweep |
| Two read-only snapshots, same tests on both | ✅ A, B — **plus C** for the authorised delta check |
| **No** repeat of the 494-case / 168-flow sweep | ✅ not repeated |
| First step: `python -c "import app.main"` | ✅ on all three snapshots, `missing_symbols: {}` |
| Re-run the previous round's post-fix assertions | ✅ 188 assertions, classified FIXED / STILL / REGRESSED / STALE / NEW |
| 120–180 highest-value raw-language hard pairs | ✅ **182** discriminating cases |
| Classify every old finding | ✅ `evidence/postfix_classification.json` |
| Tests-only patch | ✅ `patches/V19_1_TESTS_ONLY.patch` (validates with `git apply --check`) |
| 13 named reports + 6 evidence artefacts | ✅ see §7 |

### 1.2 EAC-Aware Update

| Item | Status |
|---|---|
| 1. Validate the EAC patch, don't trust the report | ✅ `EAC_PATCH_VALIDATION.md` — **report falsified** |
| 2. Attack provider evidence scope | ✅ `ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md` |
| 3. Confirm semantics / concurrent / cross-scope / same-code | ✅ `SCOPE_AUDIT_RESULTS.md` |
| 4. Review `audit` / `catalog` / `extract` | ✅ `EAC_PATCH_VALIDATION.md` §7 |
| 5. OpenAPI drift auto-check | ✅ `OPENAPI_DRIFT_RESULTS.md` |
| 6. 150–220 discriminating cases | ✅ 182 |
| 7. Tag findings FINAL_V19 / EAC_REFERENCE / CODEX_V19_1 | ✅ every table carries its tag |
| 3 extra reports | ✅ `EAC_PATCH_VALIDATION.md`, `ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md`, `OPENAPI_DRIFT_RESULTS.md` |
| If Codex V19.1 lands late, **one** targeted read-only delta check | ✅ Snapshot C — `CODEX_V19_1_DELTA_RESULTS.md` |
| Do not modify the main tree | ✅ |

---

## 2. Snapshot ledger

| | A | B | C |
|---|---|---|---|
| Taken | 2026-09-15 12:38:11 | 2026-09-15 13:05:57 | 2026-09-15 13:47:07 |
| Tree | FINAL_V19 | FINAL_V19 | **Codex V19.1** |
| Files copied | 339 | 341 | 341 |
| `import app.main` | OK | OK | OK |
| `capabilities.py` bytes | 15,283 | 15,283 | **19,890** |
| `capabilities.py` sha16 | `7e3ff4cb3a85b7b6` | `7e3ff4cb3a85b7b6` | **`b342df348c0d62a7`** |
| Missing symbols | `{}` | `{}` | `{}` |
| Suite result | 37 P / 106 F / 45 S | 37 P / 106 F / 45 S | **119 P / 54 F / 15 S** |

**Watched-file diff A → B: exactly one file changed** —
`backend/app/stay_mobility.py`, where Codex added `traveler_snapshot = refresh_snapshot(...)`
and moved `traveler_twin = snapshot_payload(...)` into `experience_payload()`. That
single edit is the whole reason `/experience` went from 500 to 200.

Snapshot C is the authorised single delta check, taken because Codex wrote
`capabilities.py`, `replanning/feasibility.py` and `main.py` after B. Snapshot C is a
**copy**; the live tree was never imported from directly.

---

## 3. Delta-target scoreboard

### 3.1 A → B (FINAL_V19 drift)

| Target | FIXED | STILL |
|---|---:|---:|
| D1 hard-downgrade guard | 2 | 19 |
| D2 clause-local negation / history | 2 | 18 |
| D3 duplicate capability codes | 0 | 8 |
| D4 walking / rest numerics | 6 | 19 |
| D5 rest & nap windows | 2 | 6 |
| D6 gate interprets capability | 2 | 1 |
| D7 TRAVELER scope reachable | 2 | 7 |
| guards | 13 GUARD_HOLDS | 0 |

### 3.2 B → C (Codex V19.1)

| Target | FIXED | STILL | other |
|---|---:|---:|---|
| D1 hard-downgrade guard | **21** | 0 | — |
| D2 clause-local negation / history | **18** | 2 | — |
| D3 duplicate capability codes | **8** | 0 | — |
| D4 walking / rest numerics | 6 | 19 | — |
| D5 rest & nap windows | 2 | 6 | — |
| D6 gate interprets capability | 1 | 1 | 1 STALE_TEST |
| D7 TRAVELER scope reachable | 2 | 7 | — |
| EAC / provider-evidence scope | 22 | 9 | 8 new defects, 22 new guards hold, 1 REGRESSED |
| guards (must not regress) | — | 0 | **13/13 GUARD_HOLDS** |

**No guard regressed. One defect probe regressed** (§5.3).

### 3.3 The one harness defect found and fixed in this round

The first pass of the suite reported **108** assertions. The EAC test file used a
*module-level* `pytest.importorskip("app.integrations.accessibility.osm")`. That
package does not exist on any tree, so collection raised `Skipped` and pytest
silently dropped **every test in the file** — including the two mandated-sentence
tests the brief explicitly asked for. It is now a `try/except ImportError` binding
plus a `@requires_osm` marker; the module collects **81** tests instead of 0, and
the suite is **188** assertions. Any earlier "108" figure from this round is
superseded.

---

## 4. The four trees, side by side

| Dimension | EAC reference | FINAL_V19 (B) | **Codex V19.1 (C)** |
|---|---|---|---|
| `capabilities.py` size | 19,910 B | 15,283 B | 19,890 B |
| HARD accessibility downgradable | no ✅ | yes ❌ | **no ✅** |
| Duplicate codes merged | yes ✅ | no ❌ | **yes ✅** |
| Cross-scope dedup safe | no ❌ | n/a (no dedup) | **no ❌ (regression)** |
| Strictest numeric limit wins | no ❌ | n/a | **yes ✅** |
| `toilets:wheelchair=yes` verifies step-free | **yes ❌** | yes ❌ | **no ✅** |
| `overall_state` cross-subject leak | **yes ❌** | yes ❌ | **no ✅** |
| Route step-free without route evidence stays unknown | yes ✅ | no ❌ | **yes ✅** |
| `wheelchair=yes + step_count=5` is CONFLICT | yes ✅ | no ❌ | **no ❌** |
| list/tuple tag value not dropped | no ❌ | no ❌ | **no ❌** |
| `I don't need a wheelchair, I can walk` false-HARD | **yes ❌** | yes ❌ | **no ✅** |
| `朋友说我可能需要轮椅，但我不这么认为` false-HARD | **yes ❌** | yes ❌ | **no ✅** |
| Third-party / facility / speculation false-HARD | yes ❌ | yes ❌ | **yes ❌ (9 cases)** |
| TRAVELER scope reachable from text | no ❌ | no ❌ | **no ❌** |
| Clause-local negation keeps the live need | yes ✅ | no ❌ | **yes ✅** |
| Walk / rest numerics | partial | partial | **partial** |

**Read this table as the convergence verdict:** Codex V19.1 dominates FINAL_V19 on
every row except the four it has not yet touched, and it beats the EAC reference on
the two rows the brief cared about most (toilet-tag scope, cross-subject leak).

---

## 5. The findings that matter

### 5.1 P0 — an ARRIVAL-anchored C4 commitment strands the journey
`STILL_REPRODUCIBLE` on Codex V19.1 · tag `CODEX_V19_1_IF_AVAILABLE`

`inbox/import` → 201, `inbox/{draft}/confirm` → 200 producing a real
`C4_Anchored`/`ACTIVE` commitment. Then `POST /start` → **500**:

```
main.py:4894 start_journey
  -> main.py:4769 _twin_snapshot
    -> integrations/mobility/runtime.py:54 capture_runtime_mobility_snapshot
      -> integrations/mobility/snapshot_capture.py:94 capture_mobility_snapshot
        -> integrations/mobility/runtime.py:31 _place_lookup
KeyError: 'no routable coordinates for ea06631e-f5b4-598a-8a96-2483c271a825'
```

The journey is left **stranded in `PLANNED`**. Only **ARRIVAL**-anchored C4s trigger
it — an ARRIVAL anchor stores a random UUID as its mobility `semantic_key`, and
`_twin_snapshot` then tries to route to it. DEPARTURE and MID_TRIP pass; an ARRIVAL
whose `scheduled_start_at` is already past is filtered out and also passes.
`GET /twin` on the same journey returns 200. Evidence: `evidence/c4_start_c.json`.

### 5.2 P0 — three code paths, two definitions of feasibility
`STILL_REPRODUCIBLE` on Codex V19.1

```
generate  -> 201 / 3 plans        (ignores the C4)
select    -> 200                  (ignores the C4)
bookings  -> 422  "selected plan is no longer feasible:
                   LOCKED_COMMITMENT_LOST:ea06631e-…"
```

`generator_produced_plans_the_validator_rejects: true`,
`product_let_user_select_a_plan_it_will_not_let_them_use: true`.
Root cause: `generate_plans` (`services.py:847`) and `select_plan`
(`main.py:3693`) build constraints from capabilities only, while
`_assert_selected_plan_feasible` (`main.py:4458`) →
`validate_plan_feasibility(..., include_active_c4=True)` includes them.
Evidence: `evidence/c4_gate_c.json`.

### 5.3 Regression — cross-scope dedup collapse
`REGRESSED` on Codex V19.1

```python
# snapshot_c/backend/app/capabilities.py:329, 365
seen: dict[str, dict[str, Any]] = {}
...
previous = seen.get(code)          # <-- scope is NOT part of the key
```

```
B: [AVOID_STAIRS HARD TRAVELER, AVOID_STAIRS HARD JOURNEY] -> 2 rows
C: -> 1 row  {scope: TRAVELER, params: {note: traveler}}    # JOURNEY row discarded
```

Latent today (D7 is still open, so natural language usually yields one `JOURNEY`
row), but it becomes live data loss the moment D7 is fixed. Fix: key on
`(scope, code)`.

### 5.4 Provider-evidence scope — what holds and what does not
tag `CODEX_V19_1_IF_AVAILABLE`

Holds on Codex V19.1: toilet / ramp / elevator / kerb / tactile / entrance tags do
**not** verify step-free; route step-free without route evidence stays
`NEEDS_LIVE_EVIDENCE`; a place `wheelchair=yes` no longer leaks into a route
requirement.

Does **not** hold:
- `wheelchair=yes + step_count=5` → `ACCESSIBILITY_UNVERIFIED`, not `CONFLICT`.
  `step_count`, `steps` and `highway=steps` are simply not read. Not a fail-open
  (the journey is still blocked) but the wrong reason, and a numeric provider
  contradiction is exactly what an operator needs surfaced.
- A list/tuple used as a mapping **value** is silently dropped:
  `{"wheelchair": ["yes"]}` → `{"wheelchair": "['yes']"}`. The sequence and nested
  forms *are* handled, so the brief's demand is half met.
- `step_free_verified` at the metadata **top level** is dropped by
  `_accessibility_metadata`'s key whitelist, while the same value nested under
  `tags`/`osm_tags` verifies. One key short.

### 5.5 Residual false-HARD — 9 cases Codex V19.1 did not fix

Third-party, facility-description and speculation statements still manufacture a
HARD `STEP_FREE_REQUIRED`, verified live against Snapshot C:

| text | class |
|---|---|
| `my friend needs a wheelchair, not me` | third party |
| `my mother uses a wheelchair` | third party |
| `我朋友需要轮椅` | third party |
| `我妈妈坐轮椅` | third party |
| `I am not a wheelchair user` | first-person denial |
| `the station has an accessible toilet` | facility description |
| `车站有无障碍厕所` | facility description |
| `说不定到时候我需要轮椅` | speculation |
| `if I end up in a wheelchair I'll tell you` | conditional / deferred |

Codex **did** fix the same classes elsewhere (`my colleague said I might need a
wheelchair` ✅, `同事说我也许需要轮椅` ✅, `if I get tired I might need a wheelchair` ✅,
`no stairs problem for me, I'm fine` ✅), so this is a **marker-coverage gap**:
a relational subject (`my friend` / `我妈妈` / `not me`) and a possibility marker
without a modal verb (`说不定`, `if I end up`) both defeat the guard.

### 5.6 Still open from FINAL_V19, untouched by Codex V19.1

| Finding | Verdict |
|---|---|
| D4 — walking numerics (19 of 25 forms yield no capability) | `STILL_REPRODUCIBLE` |
| D5 — rest / nap windows (6 residual) | `STILL_REPRODUCIBLE` |
| D7 — TRAVELER scope unreachable from natural language | `STILL_REPRODUCIBLE` |
| Numeric limits enforced but never validated (`max_m: 10**12` blocks the same as `max_m: 500`) | `STILL_REPRODUCIBLE` |
| Gate computes rich failure codes; client sees exactly one message | `STILL_REPRODUCIBLE` |
| Evidence semantics asymmetric (`STROLLER`/`LARGE_LUGGAGE` fail open; `STEP_FREE_REQUIRED` fails closed) | `STILL_REPRODUCIBLE` |
| Hermes exposes no capability tool (`v1: 6`, `v2: 11`, `any_capability_tool: false`) | `STILL_REPRODUCIBLE` |
| Model codes and server codes live in different namespaces (98 of 103 dropped silently) | `STILL_REPRODUCIBLE` |

---

## 6. Recommended actions, in priority order

1. **Fix the ARRIVAL-anchor crash** (§5.1). Either resolve the anchor's
   `semantic_key` to a routable place before `_twin_snapshot`, or degrade
   gracefully. Today a paid, confirmed reservation makes the journey unstartable.
2. **Unify the three planning paths** (§5.2). `generate_plans` and `select_plan`
   must load active C4 commitments the same way `validate_plan_feasibility` does.
3. **Key the dedup on `(scope, code)`** (§5.3). One-line fix; prevents silent loss
   of a journey-scoped need once D7 lands.
4. **Read `step_count` / `steps` / `highway=steps`** (§5.4) and force `CONFLICT`.
5. **Unwrap list/tuple mapping values** in `normalize_osm_tags` (§5.4), and add
   `step_free_verified` to `_accessibility_metadata`'s key whitelist.
6. **Extend the negation guard** with third-party subjects, `not me`, and
   modal-free possibility markers (§5.5).
7. **Surface the gate's failure codes.** The gate already computes
   `ACCESSIBILITY_UNVERIFIED:*`, `NEEDS_LIVE_EVIDENCE:*`, `CAPABILITY_PARAMS_INVALID:*`,
   `REST_WINDOW_UNSATISFIED:*`, `MAX_WALKING_PER_LEG_EXCEEDED:*` and
   `LOCKED_COMMITMENT_LOST:*` — and the client sees
   `"No feasible plan candidates satisfy the journey constraints"` for all of them.
8. **Validate numeric params** rather than only enforcing them.
9. **Make TRAVELER scope reachable** (D7) — until then the scope field is
   decorative.

---

## 7. Deliverables

### Reports (16)

| File | Tag |
|---|---|
| `WORKBUDDY_V19_1_CONVERGENCE_REPORT.md` | this file |
| `SNAPSHOT_A_RESULTS.md` | `FINAL_V19` |
| `SNAPSHOT_B_RESULTS.md` | `FINAL_V19` |
| `CAPABILITY_CANONICALIZATION_RESULTS.md` | `FINAL_V19` |
| `SEMANTIC_HARDPAIR_RESULTS.md` | `FINAL_V19` |
| `NUMERIC_TIME_BOUNDARY_RESULTS.md` | `FINAL_V19` |
| `FEASIBILITY_EVIDENCE_RESULTS.md` | `FINAL_V19` |
| `MIDTRIP_RECOVERY_RESULTS.md` | `FINAL_V19` |
| `CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md` | `FINAL_V19` |
| `SCOPE_AUDIT_RESULTS.md` | `FINAL_V19` |
| `HERMES_CAPABILITY_RESULTS.md` | `FINAL_V19` |
| `WEB_MOBILE_RESULTS.md` | `FINAL_V19` |
| `CODEX_HANDOFF_V19_1.md` | `FINAL_V19` + `CODEX_V19_1_IF_AVAILABLE` |
| **`EAC_PATCH_VALIDATION.md`** | `EAC_REFERENCE` + addendum |
| **`ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md`** | `EAC_REFERENCE` + addendum |
| **`OPENAPI_DRIFT_RESULTS.md`** | `EAC_REFERENCE` + `CODEX_V19_1_IF_AVAILABLE` |
| **`CODEX_V19_1_DELTA_RESULTS.md`** | `CODEX_V19_1_IF_AVAILABLE` |

### Evidence

| File | Contents |
|---|---|
| `evidence/snapshot_{a,b,c}.json` | manifests, per-file hashes, import status, symbol check |
| `evidence/snapshot_watched/{a,b,c}/` + `MANIFEST.json` | the 11 capability-relevant files at each snapshot timestamp, plus the a→b / b→c change table |
| `evidence/snapshot_a_first_attempt.json`, `snapshot_b_prev.json` | superseded takes, kept for provenance |
| `evidence/_junit_{a,b,c}.xml` | JUnit XML for the three suite runs |
| `evidence/postfix_classification.json` | 188 assertions × A/B/C verdicts |
| `evidence/hardpairs.jsonl` + `hardpairs_{a,b}.jsonl` | semantic corpus with model / canonical / local / merged / gate columns |
| `evidence/boundaries.jsonl` | walking / rest / break / window boundary cases |
| `evidence/e2e_results.jsonl` | end-to-end lifecycle cases |
| `evidence/semantic_cases.jsonl` | the 182-case corpus |
| `evidence/semantic_analysis_{a,b}.json` | per-bucket analysis |
| `evidence/canonicalization_{a,b}.json` | canonicalization probes |
| `evidence/lifecycle_{a,b}.json` | lifecycle + mid-trip + Hermes |
| `evidence/c4_gate_{a,b,c}.json` | the three-planning-paths probe |
| `evidence/c4_start_{a,b,c}.json` | the ARRIVAL-anchor matrix |
| `evidence/commitment_conflict_{a,b}.json` | C4 ↔ capability conflict |
| `evidence/gate_codes_{a,b}.json` | gate codes vs API message |
| `evidence/boundaries_{a,b}.json` | boundary matrices |
| `evidence/accessibility_evidence_scope.json` | EAC / A / B / C tag matrix + sentence replay |
| `evidence/codex_v19_1_evidence.json` | Codex V19.1 provider-evidence matrix |
| `evidence/codex_v19_1_delta.json` | Codex V19.1 module-level delta |
| `evidence/codex_v19_1_corpus_delta.json` | 182-case B vs C comparison |
| `evidence/eac_live.json` | live EAC lab probe |
| `evidence/eac_differential.jsonl` + `_summary.json` | EAC vs FINAL_V19 corpus differential |
| `evidence/openapi_drift.json` | runtime vs checked-in OpenAPI, four trees |
| `evidence/web_mobile_*.json` + `evidence/screenshots/` | 72 screenshots, 4 viewports, focus / zoom / capability probes |

### Patches

| File | Notes |
|---|---|
| `patches/V19_1_TESTS_ONLY.patch` | 4 files, 1,595 added lines, `backend/tests/` only. Validates with `git apply --check` against the main tree. **Not applied.** |
| `patches/V19_1_LOW_CONFLICT_FIXES.patch` | `backend/app/capabilities.py`, +40 / −7: dedup key `(scope, code)`, list/tuple unwrapping, `step_count`/`steps`/`highway=steps` as stair evidence. Measured on a scratch copy of Snapshot C: 54 F / 119 P → **46 F / 127 P**. Validates with `git apply --check`. **Not applied.** |

---

## 8. Method notes

- **Isolation.** Narrow include-list snapshots; `PYTHONDONTWRITEBYTECODE=1` on every
  Python invocation (importing the main tree would otherwise write `.pyc` files,
  i.e. modify it); one throwaway SQLite per snapshot under `evidence/_db/`; the
  Web/Mobile lab on ports 8050 / 4203 so it can never collide with Codex's
  8000 / 5173.
- **Moving-baseline discipline.** Every conclusion is bound to a snapshot
  timestamp. The A→B drift is recorded in full rather than silently folded into the
  result, so a future reader can tell "Codex fixed this" from "this was never
  broken".
- **One authorised delta check.** Snapshot C was taken once, for the reasons in
  §2, and only the focused suite, the 182-case corpus, the two C4 probes and the
  tag matrix were run against it. The 494-case / 168-flow sweep was not repeated.
- **Self-corrections in this round.** (a) The module-level `importorskip` that hid
  81 tests. (b) An initially-wrong claim that Codex V19.1's canonicalizer had no
  scope bug — the classification flagged `merge_respects_scope` as REGRESSED and
  direct measurement confirmed it; the report was corrected rather than left as
  written.
