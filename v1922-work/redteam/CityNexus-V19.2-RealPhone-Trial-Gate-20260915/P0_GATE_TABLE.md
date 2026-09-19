# V19.2 Real-Phone Shadow-Trial Gate — P0 Gate Table

Baseline: `D:\moodle\CityNexus` read-only snapshots
**A = 2026-09-15 17:29:11**, **B = 2026-09-15 17:50:44** (the single authorised delta check).
`capabilities.py` is byte-identical in A and B (`23668 B`, sha16 `9b68b17997f4cf4e`).
Every verdict below was reproduced on both snapshots unless stated otherwise.

Verdict column: **PASS** = the gate is met, **FAIL** = the gate is not met, **PARTIAL** = some
sub-cases pass and some do not.

---

## Group 1 — Planning truth

| # | Gate | Verdict | Evidence |
|---|------|---------|----------|
| 1.1 | One feasibility truth across `generate` / generic compose / `select` / booking revalidation | **PASS** | `evidence/feasibility_truth_a.json`, `_b.json` — `generator_produced_plans_the_validator_rejects: []`; all four paths now build their constraint set from `_journey_constraints_with_capabilities(..., include_c4=True)` (the V19.1 split is closed) |
| 1.2 | A C4-anchored commitment can be honoured by plan generation | **FAIL** | `evidence/c4_lifecycle_a.json` — 4/4 anchor configurations make **every** existing plan infeasible with `LOCKED_COMMITMENT_LOST:<semantic_key>`; `generate` returns 422 |
| 1.3 | A blocked plan tells the client *why* | **PARTIAL** | `select` → 422 `"PlanVersion … is infeasible: LOCKED_COMMITMENT_LOST:<key>"` ✅; `generate` → 422 `"No feasible plan candidates satisfy the journey constraints"` with `details: null` ❌ |

## Group 2 — C4 / Journey start

| # | Gate | Verdict | Evidence |
|---|------|---------|----------|
| 2.1 | No 5xx when starting a journey with a confirmed anchor | **PASS** | `evidence/c4_lifecycle_a.json` — `any_start_5xx: false`. The V19.1 `/start` → 500 is gone |
| 2.2 | A journey with a confirmed anchor can actually start | **FAIL** | `evidence/c4_lifecycle_a.json` — `start_statuses: {}`. `select` returns 422 first, so `/start` is never reachable. The journey is `DRAFT` and stuck |
| 2.3 | Every anchor role behaves consistently | **PASS (consistently blocking)** | ARRIVAL, DEPARTURE, MID_TRIP, and an out-of-window ARRIVAL all block identically |
| 2.4 | One logical confirmation ⇒ one active commitment | **PASS** | `evidence/c4_lifecycle_a.json` — same `confirmation_ref` imported twice → 2 drafts; same draft confirmed twice → 200/200, commitments stay **1**; confirming the sibling draft → **409** |

## Group 3 — Capability semantics

| # | Gate | Verdict | Evidence |
|---|------|---------|----------|
| 3.1 | HARD accessibility cannot be downgraded | **PASS** | `evidence/lifecycle_a.json` → `rows_after_downgrade_attempt` keeps `severity: HARD`; focused suite `test_v19_char_d6b` |
| 3.2 | Third-party / facility / speculative language does not create a HARD need | **PASS** | `evidence/capability_semantics_a.json` — G1 `9/9` (all nine V19.1 residual false-HARD sentences are now clean) |
| 3.3 | Real first-person needs are **not** over-filtered away | **FAIL** | `evidence/p0_numeric_a.json` → `n4_filtering` — 7 of 8 probe sentences produce **nothing**, including `如果可能的话我需要无障碍通道`, `if possible I need step-free access`, `我可能需要轮椅` |
| 3.4 | Scope-aware canonicalization (`(scope, code)` dedup) | **PASS** | `evidence/capability_semantics_a.json` — G2 `4/4`; TRAVELER + JOURNEY same code survive as two rows with their own params |
| 3.5 | Permanent language → TRAVELER, this-trip language → JOURNEY | **PASS** | G2 `permanence_scope` / `this_trip_scope`; corpus case `scope_permanence-0091` now `TRAVELER` (was `JOURNEY`) |
| 3.6 | Duplicate same-scope numeric limits merge to the stricter bound | **PASS** | G2 `numeric_merge` — 400 wins over 800 |

## Group 4 — Provider evidence

| # | Gate | Verdict | Evidence |
|---|------|---------|----------|
| 4.1 | Facility tags never satisfy `STEP_FREE_REQUIRED` | **PASS** | `evidence/capability_semantics_a.json` — G3 `facility_tags 12/12` (toilet / ramp / elevator / kerb / tactile / entrance / `wheelchair=*`) |
| 4.2 | Route without route evidence stays unknown | **PASS** | G3 `route 2/2` → `NEEDS_LIVE_EVIDENCE` |
| 4.3 | Explicit step-free assertions verify | **PASS** | G3 `positive 4/4` |
| 4.4 | Provider data that contradicts itself surfaces as CONFLICT | **FAIL** | G3 `contradiction 5/7` — `wheelchair=yes` beside nested `step_count=5`, and beside `steps=yes`, both return `ACCESSIBILITY_UNVERIFIED` instead of `ACCESSIBILITY_CONFLICT` |
| 4.5 | List/tuple tag values are not silently dropped | **PASS** | G3 `tag_shapes 5/5` |
| 4.6 | The canonical `evidence_status: VERIFIED` signal is honoured | **FAIL** | `evidence/lifecycle_a.json` → `capability_evidence_verified_string` → **422 / 0 plans** while `{"step_free": true}` → 201 / 3 plans. `evaluate_accessibility_requirement` never reads `evidence_status` |
| 4.7 | A top-level `step_free_verified` in place metadata reaches the gate | **FAIL** | focused suite `test_v191_eac_defect_top_level_step_free_verified_is_seen` — `_accessibility_metadata` whitelist still omits it |

## Group 5 — Numeric / time constraints

| # | Gate | Verdict | Evidence |
|---|------|---------|----------|
| 5.1 | Numeric parameters are real semantics (no unit mixing) | **FAIL** | `evidence/p0_numeric_a.json` → `n1_unit_confusion` 3 violations: `连续走不能超过 20 分钟` yields `MAX_WALKING_PER_LEG_M HARD max_m=20` **and** `MAX_CONTINUOUS_WALKING_MIN max_min=20`; `我每天走路不能超过 3000 米` duplicates the daily cap as a per-leg cap |
| 5.2 | Decimal values survive extraction | **FAIL** | `evidence/p0_numeric_a.json` → `n2_n3_decimal` 6/6 defects: `1.5 公里` → **1**, `2.5 公里` → **2**, `0.5 公里` → **0**, `1.5 米` → 1, `0.5 米` → 0 — all with `needs_clarification: false` |
| 5.3 | A local fallback never persists `0 m` as a clean authoritative cap | **FAIL** | `走路不能超过 0 米` → `{'max_m': 0, 'needs_clarification': False}`, `severity: HARD`. Explicit road-prep policy violation |
| 5.4 | Reversed time windows are rejected, not defaulted | **PASS** | `evidence/cross_snapshot_numeric.json` — `午休 15:00 到 13:00` → `needs_clarification: true`, no window (V19.1 returned a reversed or invented window) |
| 5.5 | km → m conversion | **PASS** | `1 km` → 1000, `1 公里` → 1000 |
| 5.6 | Negative / unparseable values are refused or flagged | **PASS** | `-5 米` → `needs_clarification: true`; `五百 米` → `needs_clarification: true` |
| 5.7 | Rest / nap windows are flagged when defaulted | **PARTIAL** | `MIDDAY_REST_WINDOW` carries `defaulted_window: true` ✅; `INFANT_NAP_WINDOW` does not ❌ |
| 5.8 | Natural `不超过 N 米` phrasing is recognised | **FAIL** | `evidence/capability_semantics_a.json` → `G4b_natural_phrasing 2/6` — `每段不超过 100 米`, `单段步行不超过 100 米`, `每次走路不超过 100 米`, `不要走超过 100 米` all produce no walking limit |

## Group 6 — Mid-trip behaviour

| # | Gate | Verdict | Evidence |
|---|------|---------|----------|
| 6.1 | The active plan is not silently rewritten when a HARD need appears mid-trip | **PASS** | `evidence/lifecycle_a.json` → `plans_mutated_silently: false`; plan signatures identical before/after |
| 6.2 | A mid-trip HARD need produces a governed consequence | **FAIL** | `evidence/lifecycle_a.json` → `replan_proposals: 0`, journey stays `ACTIVE` on the old plan, `experience_mentions_review: false` |
| 6.3 | HARD capability needs require explicit `/confirm` | **PASS** | `midtrip_put_status: 409 "hard capability needs require /confirm"` |
| 6.4 | Capability mutations are audited | **PASS** | `audit_capability: ["traveler.capability.created"]` |

## Group 7 — Contract / release

| # | Gate | Verdict | Evidence |
|---|------|---------|----------|
| 7.1 | Runtime OpenAPI matches the checked-in contract | **PASS** | `evidence/openapi_drift.json` — V19.2 snapshot: runtime 137 pairs, contract 137, `missing=0 extra=0 parity_ok=True`; the live main tree is also `parity_ok=True` |
| 7.2 | `/api/v1` prefix handling is correct | **PASS** | `servers[0].url` declares the prefix; parity computed with it. Not a defect |
| 7.3 | Stale candidates are refused with a precise reason | **PASS** | `evidence/stale_candidates_a.json` → `all_shapes_refused: true` (expired / missing snapshot_id / inconsistent reference / invalid timestamp → 409 with a distinct message each) |
| 7.4 | A journey cannot start on expired provider evidence | **FAIL** | `evidence/stale_candidates_a.json` → `start_with_stale_selected: 200`, `journey_status: ACTIVE`, `experience_flags_staleness: false` |
| 7.5 | The shipped starter patches apply to the current tree | **FAIL** | 2 of 3 do not — see `PATCH_VALIDATION.md` |

---

## Verdict

**BLOCKED.**

Three independent groups contain at least one **FAIL** that directly prevents a real-phone
shadow trial:

1. **C4 anchors make the product unusable** (1.2, 2.2). Any confirmed reservation — the
   flagship use case — blocks planning and starting, with no recovery path.
2. **Numeric truth is corrupted silently** (5.1, 5.2, 5.3). `1.5 公里` becomes a HARD 1-metre
   per-leg cap presented as authoritative; `连续走不能超过 20 分钟` becomes a HARD 20-metre cap.
3. **Safety-relevant needs are silently dropped** (3.3). `if possible I need step-free access`
   and `我可能需要轮椅` produce no capability at all, so the planner is free to route the
   traveller onto stairs.

Plus two supporting failures that would each be trial-blocking on their own: a live journey can
run on **expired** provider evidence (7.4), and a mid-trip HARD need has **no consequence** (6.2).

## What V19.2 genuinely fixed

- The V19.1 `/start` → 500 is gone (2.1) and no path returns 5xx.
- The V19.1 cross-scope canonicalization **regression** is fixed (3.4).
- All nine residual false-HARD sentences are clean (3.2).
- C4 confirmation idempotency holds (2.4).
- Reversed time windows are rejected (5.4).
- The four planning paths now share one constraint set (1.1).
- Focused contract suite: **V19.1 = 54 failed / 119 passed / 15 skipped → V19.2 = 14 failed / 161 passed / 13 skipped**.
