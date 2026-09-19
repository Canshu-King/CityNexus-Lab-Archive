# CityNexus V19.2 — Real-Phone Shadow-Trial Gate

**Verdict: `BLOCKED`**

Read-only red-team. The authoritative main tree `D:\moodle\CityNexus` was never modified;
every measurement below comes from a byte-copy in
`D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915`.

| | |
|---|---|
| Round | V19.2 Real-Phone Shadow-Trial Gate (continues V19.1, does not restart it) |
| Baseline | Snapshot **A** `2026-09-15 17:29:11`, Snapshot **B** `17:50:44` (the one authorised delta check) |
| `capabilities.py` | `23,668 B`, sha16 `9b68b17997f4cf4e` — **byte-identical in A and B** |
| `main.py` | `f352ff55fd1f3c6a` (A) → `c17f74c4867a1a1d` (B, 17:29:43) |
| `operations/v9.py` | `e3427bffe7a886fa` (A) → `8a18af376260d98b` (B, 17:40:21) |
| DB layer (`db/models.py`, `db/session.py`, `db/schema.sql`) | all three moved at 17:30:35, i.e. **after** A and **before** B — B runs on the new DB layer and reproduces every finding |
| `replanning/feasibility.py` | `8a0de9106818725d`, unchanged since 13:16:26 |
| Verdict | **BLOCKED** — not `SHADOW_TRIAL_READY` |

---

## 1. Protocol compliance

| Requirement | Status |
|---|---|
| Never mutate the main tree | ✅ all writes confined to the lab; `node_modules` via junction; Vite cache in `%TEMP%`; `PYTHONDONTWRITEBYTECODE=1` everywhere |
| Do not restart the 494-case sweep | ✅ focused probes only (64 + 8 + 6 + 120-case corpus differential) |
| Validate the supplied starter patches independently | ✅ `PATCH_VALIDATION.md` — 2 of 3 no longer apply; re-measured, not trusted |
| One targeted delta snapshot if Codex lands V19.2 | ✅ Snapshot B taken 21 min after A; **every finding reproduced identically** |
| Final verdict from `{BLOCKED, SHADOW_TRIAL_READY}` | ✅ `BLOCKED` |

`import app.main` succeeds on both snapshots; no path in the tested surface returns 5xx.

---

## 2. Before / after delta

### Focused contract suite (identical files, identical command)

| Baseline | Result |
|---|---|
| V19.1 snapshot C (13:05) | 54 failed / 119 passed / 15 skipped |
| **V19.2 snapshot A** | **14 failed / 161 passed / 13 skipped** |
| V19.2 snapshot B | 14 failed / 161 passed / 13 skipped |

By unique test function: **22 failing → 9 failing**, i.e. **13 FIXED / 1 REGRESSED / 8 STILL_REPRODUCIBLE**.
Full per-item table: `REGRESSION_LIST.md`. No previously-passing guard was broken apart from the one
regression below.

### This round's own gate suite (`patches/V19_2_TESTS_ONLY.patch`)

| | |
|---|---|
| `test_v192_guard_*` | **37 / 37 PASS** |
| `test_v192_defect_*` | **24 / 24 FAIL** (locked on purpose — each one goes green when the defect is fixed) |
| Combined with the V19.1 four files | 38 failed / 198 passed / 13 skipped (= +24 / +37 exactly; no interference) |

### Corpus differential, V19.1 C → V19.2 A (120 raw-language cases)

| Outcome | Count |
|---|---|
| `IDENTICAL` | 98 |
| `A_ADDS_HARD` | 12 |
| `A_REMOVES_HARD` | 2 |
| `A_CODE_CHANGE` | 6 |
| `A_PARAM_CHANGE` | 2 |

---

## 3. The three independent blockers

### B1 — A confirmed reservation makes the product unusable

`P0_GATE_TABLE.md` rows **1.2** and **2.2**. The V19.1 `/start` → 500 is gone, but the journey can
no longer be *planned* at all, so `/start` is unreachable and the journey stays `DRAFT`.

Measured on 4/4 anchor configurations — ARRIVAL@12:30, DEPARTURE, MID_TRIP `place-old-town`,
MID_TRIP `place-riverside-museum`, plus an out-of-window ARRIVAL@07:00:

| Anchor | commitment | `generate` | plans | `select` | `/start` |
|---|---|---|---|---|---|
| ARRIVAL | `C4_Anchored` / `ACTIVE` | **422** | 0 | n/a | never reached |
| DEPARTURE | `C4_Anchored` / `ACTIVE` | **422** | 0 | n/a | never reached |
| MID_TRIP `place-old-town` | `C4_Anchored` / `ACTIVE` | **422** | 0 | n/a | never reached |
| ARRIVAL@07:00 | `C4_Anchored` / `ACTIVE` | **422** | 0 | n/a | never reached |
| **control, no reservation** | — | 201 | 3 | 200 | 200 / `ACTIVE` |

Root cause chain (four steps, each verified):

1. `app/operations/v9.py` → `confirm_reservation_draft()` synthesises a **UUID** `semantic_key` for
   ARRIVAL / DEPARTURE (`ea06631e-f5b4-598a-8a96-2483c271a825`, `21493e6c-9533-5d97-9f04-9dcf9384f2e0`).
   Only MID_TRIP gets a real place key (`place-old-town`).
2. `app/replanning/protected_commitments.py` → `active_c4_hard_constraints()` emits
   `rule_code: "LOCKED_COMMITMENT"`, `params.semantic_ref = semantic_key`.
3. `app/replanning/feasibility.py:412` → `_locked_commitments()` requires a plan activity whose key
   matches `semantic_ref`.
4. **No generator ever emits an activity keyed by a synthetic UUID**, so every candidate plan fails
   with `LOCKED_COMMITMENT_LOST:<semantic_key>`. `LOCKED_COMMITMENT` acts only as a veto — nothing
   attempts to *satisfy* the anchor.

Exact reproduction:

```
python tools/v191_probe_c4_start.py A          # 6-case anchor matrix
python tools/v192_probe_c4_lifecycle.py A      # generate-then-anchor, keeps the reason visible
```

Reason propagation is **PARTIAL**: `select` returns an accurate
`LOCKED_COMMITMENT_LOST:ea06631e-…`, but `generate` still folds everything into
`"No feasible plan candidates satisfy the journey constraints"` with `details: null`.

### B2 — Numeric truth is silently corrupted

`P0_GATE_TABLE.md` row **5.1**, **5.2**, **5.3**. Not a rounding issue — the value is destroyed
*before* the numeric parser runs.

```
raw_value : '走路不能超过 1.5 公里'
clauses   : ['走路不能超过 1', '5 km']          <- the '.' in the split character class
value     : '走路不能超过 1 5 km'
result    : MAX_WALKING_PER_LEG_M HARD {'max_m': 1, 'needs_clarification': False}
```

The clause splitter is
`re.split(r"[,，。；;.!?！？\n]+|\bbut\b|\bhowever\b|但|但是|不过", raw_value)` — the character class
contains `.`. Calling `_number_before("1.5 km")` directly returns **1500**, which is why this looked
like a parser bug and is not one. V19.2's new `不能超过` trigger made the path reachable for the
first time.

| Input | Extracted `max_m` | Correct |
|---|---|---|
| `走路不能超过 1.5 公里` | **1** | 1500 |
| `走路不能超过 2.5 公里` | **2** | 2500 |
| `走路不能超过 0.5 公里` | **0** | 500 |
| `走路不能超过 1.5 米` | 1 | 1.5 |
| `走路不能超过 0.5 米` | 0 | 0.5 |
| `走路不能超过 0 米` | **0**, `needs_clarification: false`, `severity: HARD` | refused or clarified |

Unit mixing is a second, independent defect: `连续走不能超过 20 分钟` produces **both**
`MAX_WALKING_PER_LEG_M HARD max_m=20` (a duration read as metres) **and**
`MAX_CONTINUOUS_WALKING_MIN max_min=20`. `我每天走路不能超过 3000 米` publishes a daily budget as a
per-leg cap as well.

`0 m` being persisted as a clean authoritative HARD cap is a direct violation of the road-prep's own
policy in `DEFECT_MATRIX.md` P0-7. The policy is stated; it is not implemented.

Exact reproduction:

```
python tools/v192_probe_p0_numeric.py A
python tools/v192_probe_km_trace.py          # step-by-step trace of the 1.5 km corruption
python tools/v192_cross_snapshot_numeric.py  # V19.1 C vs V19.2 A, three snapshots side by side
```

### B3 — Safety-relevant needs are silently dropped

`P0_GATE_TABLE.md` row **3.3**. 7 of 8 probe sentences produce **no capability at all**, so the
planner is free to route the traveller onto stairs with no constraint to violate:

| Sentence | Result | vs V19.1 |
|---|---|---|
| `如果可能的话我需要无障碍通道` | *(nothing)* | — |
| `if possible I need step-free access` | *(nothing)* | **REGRESSED** (was HARD) |
| `我可能需要轮椅` | *(nothing)* | — |
| `maybe I need a wheelchair` | *(nothing)* | — |
| `我妈妈要午休` | *(nothing)* | **REGRESSED** (was STRONG) |
| `我父亲走不了远路` | *(nothing)* | — |
| `如果能推婴儿车就方便多了` | *(nothing)* | **REGRESSED** (was STRONG) |

Mechanism: the six new marker sets added in V19.2 are applied as a **whole-sentence discard**.
`_SPECULATIVE_MARKERS` contains `如果` / `if ` / `maybe` / `might`; `_THIRD_PARTY_MARKERS` contains
`我妈妈` / `我父亲` (so a travelling companion is indistinguishable from an unrelated third party);
`_NEGATED_MARKERS` contains `可能` / `也许`, so `我可能需要轮椅` reads as a denial.

This is the same over-filtering class that fixed the nine false-HARD sentences in 3.2 — the fix went
one step too far. Note that the two mandated sentences still produce HARD, so the guard is intact;
the loss is confined to hedged and companion language.

Exact reproduction:

```
python tools/v192_probe_p0_numeric.py A     # n4_filtering group
python tools/v192_probe_capability_semantics.py A
```

---

## 4. Two supporting failures

**S1 — a live journey runs on expired provider evidence** (`P0_GATE_TABLE.md` 7.4). The candidate
path is correct: all four staleness shapes (expired / missing `snapshot_id` / inconsistent reference
/ invalid timestamp) return 409 with a distinct message, and `validate_selected_plan_feasibility`
raises `ValueError: STALE_RECOMPOSE_REQUIRED: PlanVersion frozen mobility evidence expired`. But
`POST /start` on that same selected plan returns **200**, the journey stays `ACTIVE`, and
`/experience` does not mention it (`experience_flags_staleness: false`). The check exists and is
simply not wired into the start path.

**S2 — a mid-trip HARD need has no consequence** (`P0_GATE_TABLE.md` 6.2). The correct guard holds —
plans are **not** silently rewritten (`plans_mutated_silently: false`, signatures identical). What is
missing is the positive consequence: `replan_proposals: 0`, `experience_mentions_review: false`, and
the journey keeps running on a plan that no longer satisfies a HARD need. `/confirm` is correctly
required (`409 "hard capability needs require /confirm"`) and the mutation is audited
(`traveler.capability.created`).

---

## 5. What V19.2 genuinely fixed

1. `/start` → 500 is gone; no 5xx anywhere on the tested surface (`any_start_5xx: false`).
2. The V19.1 cross-scope canonicalization **regression** is fixed — `(scope, code)` dedup keeps
   TRAVELER and JOURNEY rows apart with their own params.
3. All nine V19.1 residual false-HARD sentences are clean (9/9), and the two mandated sentences still
   produce HARD (2/2).
4. C4 confirmation idempotency holds: same reference imported twice → 2 drafts; same draft confirmed
   twice → 200/200 with the commitment count staying **1**; sibling draft → **409**.
5. Reversed time windows are rejected (`午休 15:00 到 13:00` → `needs_clarification`, no window).
6. The four planning paths share one constraint set — `generator_produced_plans_the_validator_rejects: []`.
7. Integer and km walking limits are extractable for the first time (`100 米` → 100, `1 km` → 1000).
8. Facility tags (12/12), route-without-evidence (2/2), explicit positive evidence (4/4) and
   list/tuple tag shapes (5/5) all behave correctly.

## 6. Still reproducible

| Item | Status |
|---|---|
| `{"evidence_status": "VERIFIED"}` → `ACCESSIBILITY_UNVERIFIED` → 422 / 0 plans | `STILL_REPRODUCIBLE` (also fails on V19.1 C — long-standing). `evaluate_accessibility_requirement` never reads `evidence_status`; only the legacy `accessibility_state()` does |
| top-level `step_free_verified` dropped by `_accessibility_metadata` | `STILL_REPRODUCIBLE` — the whitelist still omits `step_free_verified`, `route_step_free`, `route_step_free_verified`, `has_stairs`, `step_count`, `steps`, `highway` |
| nested `osm_tags` contradiction (`step_count`, `steps`) → `UNVERIFIED` not `CONFLICT` | `STILL_REPRODUCIBLE` — `evaluate_accessibility_requirement` reads only the top level |
| natural `不超过 N 米` phrasing (4/6) | `STILL_REPRODUCIBLE` — trigger-token coverage |
| `INFANT_NAP_WINDOW` has no `defaulted_window` flag while `MIDDAY_REST_WINDOW` does | `STILL_REPRODUCIBLE` |
| `generate` folds failure reasons into one sentence | `STILL_REPRODUCIBLE` |
| `test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]` | **`REGRESSED`** — the only regression this round |

## 7. Real-phone trial verdict

**Do not run the shadow trial.** Two of the three blockers are reachable from the first screen a
trial participant would touch:

- Importing a train ticket — the flagship journey-anchor feature — yields `generate` 422 and a
  journey that can never start. A trial participant cannot complete a single end-to-end journey.
- Typing a walking limit such as `走路不能超过 1.5 公里` silently stores a **1-metre** HARD cap
  presented as authoritative, and `连续走不能超过 20 分钟` stores a 20-metre cap.

The mobile shell itself is in good shape and is **not** the blocker — see `WEB_MOBILE_RESULTS.md`:
8 routes × 4 viewports × 2 reduced-motion settings = **64/64 load, 0 page errors, 0 horizontal
overflow** including 390×844 and 430×932, no overflow at 200% zoom, visible focus rings, and no
state communicated by colour alone. The defects above propagate to the phone unchanged, which is
exactly why the phone is the wrong place to discover them.

---

## 8. Deliverables

### Reports (lab root)

| File | Contents |
|---|---|
| `P0_GATE_TABLE.md` | the 7 gate groups, 34 rows, per-row verdict and evidence pointer |
| `PATCH_VALIDATION.md` | independent re-measurement of all three supplied patches + this round's own patch |
| `NUMERIC_TIME_BOUNDARY_RESULTS.md` | decimal corruption trace, unit mixing, cross-snapshot table, 6 fix proposals |
| `CAPABILITY_SEMANTICS_RESULTS.md` | false-HARD 9/9, over-filtering regressions, scope dedup, provider evidence matrix, projection gap |
| `C4_ANCHOR_AND_IDEMPOTENCY_RESULTS.md` | the anchor matrix, the four-step root cause, reason propagation, idempotency |
| `MIDTRIP_AND_STALE_LIFECYCLE_RESULTS.md` | mid-trip consequences, capability↔C4 conflict, four staleness shapes, start path |
| `FEASIBILITY_TRUTH_RESULTS.md` | the four paths' constraint sets, split-brain closure, booking 422 explained |
| `WEB_MOBILE_RESULTS.md` | 390×844 / 430×932 trial flow, 64-cell matrix, a11y gaps |
| `OPENAPI_DRIFT_RESULTS.md` | 4 targets, `/api/v1` parity, **PASS** |
| `SNAPSHOT_AND_DELTA_RESULTS.md` | snapshot ledger, watched-file drift, A→B delta, method notes |
| `REGRESSION_LIST.md` | 13 FIXED / 1 REGRESSED / 8 STILL_REPRODUCIBLE, per test function |
| `CODEX_HANDOFF_V19_2.md` | prioritised fix list with file, line and minimal change |
| `EVIDENCE_MANIFEST.md` | every evidence artifact with the command that produced it |
| `RELEASE_TRUTH_RESULTS.md` | post-gate: V19.2.1 status files vs. measured V19.2 baseline (hash proof + 2-layer discrepancy) |

### Patch

`patches/V19_2_TESTS_ONLY.patch` — two new files under `backend/tests/`, 818 added lines, no
production module touched. `git apply --check` **PASS**; applied bytes identical to the sources
under the main tree's own `core.autocrlf=false`.

### Evidence (`evidence/`)

`snapshot_a.json`, `snapshot_b.json`, `capability_semantics_a.json`, `p0_numeric_a.json`,
`cross_snapshot_numeric.json`, `corpus_delta_c_to_a.json`, `feasibility_truth_{a,b}.json`,
`c4_lifecycle_{a,b}.json`, `c4_start_a.json`, `stale_candidates_{a,b}.json`, `lifecycle_a.json`,
`openapi_drift.json`, `web_mobile_{results,summary,zoom200,focus,bootstrap,capability}.json`,
`screenshots/` (72 PNG — the 64-cell matrix plus 8 at 200% zoom), `_cross/` (V19.1 comparison), `_db/`.

---

## 9. Release-truth discrepancy (post-gate finding)

After the gate closed, Codex wrote top-level status files into the main tree declaring
**V19.2.1** `SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE` and claiming a
"conservative capability fallback" fix in `capabilities.py`. A read-only hash re-check of
the **live** tree shows `capabilities.py` is byte-identical to the BLOCKED baseline
(`9b68b17997f4cf4e`), as are `main.py`, `operations/v9.py`, and `feasibility.py`. So all
three P0 blockers are **reproduced on the current live tree**, and the advertised fix is
absent from the code. Separately, `PACKAGE-MANIFEST.json` still advertises `v18.3` while
its sibling status files say `V19.2.1` — the unresolved P1-4 "release truth" gate. Note
Codex itself states the physical-device trial was **not performed**, so even on its own
terms the required `SHADOW_TRIAL_READY` verdict is not met. Full evidence in
`RELEASE_TRUTH_RESULTS.md`. **Verdict unchanged: `BLOCKED`.**
