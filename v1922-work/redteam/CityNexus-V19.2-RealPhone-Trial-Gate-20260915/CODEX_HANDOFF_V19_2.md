# Codex handoff — V19.2 Real-Phone Shadow-Trial Gate

Baseline for every line number below: **Snapshot A, 2026-09-15 17:29:11**
(`capabilities.py` `23,668 B` / `9b68b17997f4cf4e`; `main.py` `f352ff55fd1f3c6a`;
`replanning/feasibility.py` `8a0de9106818725d`). Snapshot B (17:50:44) is byte-identical for
`capabilities.py` and `feasibility.py`, and reproduces every finding — so these are not
mid-edit artifacts.

Verdict: **BLOCKED**. Three P0 groups. Fix in the order below; the first one is a single
decision that unblocks the entire product.

---

## P0-1 — A confirmed reservation blocks all planning

**Symptom.** Any confirmed `C4_Anchored` commitment → `POST /plans/generate` **422**, `plans: 0`,
`select` 422, `/start` never reachable, journey stuck `DRAFT`. Reproduces on 4/4 anchor
configurations (ARRIVAL, DEPARTURE, MID_TRIP with a real place key, out-of-window ARRIVAL).
Control with no reservation: 201 / 3 plans / 200 / 200.

**Where.**

| Step | File | What happens |
|---|---|---|
| 1 | `app/operations/v9.py` → `confirm_reservation_draft()` | ARRIVAL / DEPARTURE get a **synthetic UUID** `semantic_key` (`ea06631e-f5b4-598a-8a96-2483c271a825`, `21493e6c-9533-5d97-9f04-9dcf9384f2e0`); MID_TRIP gets a real key (`place-old-town`) and blocks just the same |
| 2 | `app/replanning/protected_commitments.py` → `active_c4_hard_constraints()` | emits `rule_code: "LOCKED_COMMITMENT"`, `params.semantic_ref = semantic_key` |
| 3 | `app/replanning/feasibility.py:412` → `_locked_commitments()` | requires a plan activity whose key matches `semantic_ref` |
| 4 | every generator | **never emits such an activity** → `LOCKED_COMMITMENT_LOST:<key>` for every candidate |

`LOCKED_COMMITMENT` is wired as a veto only. Nothing in the pipeline tries to *satisfy* the anchor.

**Minimal change — pick one, they are not equivalent:**

- **(a) Preferred.** Stop synthesising keys. In `confirm_reservation_draft()`, resolve
  `anchor_role` to a real catalogue place (`ARRIVAL` → the journey's arrival place,
  `DEPARTURE` → the departure place) and use that place key as `semantic_key`. Falls back to (c)
  when no place resolves.
- **(b) Strongest.** Make the generator *inject* the anchor activity: before feasibility
  validation, add a synthetic activity carrying `semantic_ref` at `scheduled_start_at` with the
  commitment's `time_boundary`. Then the anchor becomes a schedulable constraint instead of an
  impossibility.
- **(c) Cheapest.** When `semantic_ref` does not resolve to a known place, emit a pure time
  constraint (`time_boundary` + `scheduled_start_at`) instead of `LOCKED_COMMITMENT`.

**Acceptance.**

```
python tools/v191_probe_c4_start.py A
  -> all four anchor cases: generate 201, plans >= 1, select 200, start 200
     (the control case must stay 201 / 3 / 200 / 200)
python tools/v192_probe_c4_lifecycle.py A
  -> start_statuses is non-empty and any_start_5xx stays false
cd backend && python -m pytest tests/test_v192_shadow_trial_gate.py -q -k c4_anchor
  -> 3 passed
```

**Do not** regress the idempotency that already works: same `confirmation_ref` imported twice → 2
drafts; same draft confirmed twice → 200/200 with commitment count staying **1**; sibling draft →
409. Guarded by `test_v192_guard_c4_confirmation_is_idempotent`.

---

## P0-2 — Numeric truth is destroyed before the parser runs

**Symptom.** `走路不能超过 1.5 公里` → `MAX_WALKING_PER_LEG_M HARD {'max_m': 1, 'needs_clarification': False}`
(a 1500× error presented as authoritative). `连续走不能超过 20 分钟` → a HARD **20-metre** cap
alongside the correct 20-minute cap. `走路不能超过 0 米` → `max_m: 0`, `needs_clarification: false`, `HARD`.

**Root cause — one line.**

`app/capabilities.py:240`

```python
clauses = [part.strip() for part in re.split(r"[,，。；;.!?！？\n]+|\bbut\b|\bhowever\b|但|但是|不过", raw_value) if part.strip()]
```

The character class contains `.`, so `1.5` splits into `1` and `5`:

```
raw_value : '走路不能超过 1.5 公里'
clauses   : ['走路不能超过 1', '5 km']
value     : '走路不能超过 1 5 km'
```

`_number_before("1.5 km")` called directly returns **1500** — the parser is fine, the input is
already destroyed. V19.2's new `不能超过` trigger (`line 250`) made this path reachable for the
first time, which is why it looks new.

**Minimal change.** Keep `.` only as a sentence terminator, not between digits:

```python
re.split(r"[,，。；;!?！？\n]+|(?<!\d)\.(?!\d)|\bbut\b|\bhowever\b|但|但是|不过", raw_value)
```

**Then two independent follow-ups in the same area:**

1. **Unit gating.** `line 250`'s `explicit_limit` token list drives both `MAX_WALKING_PER_LEG_M`
   and `MAX_CONTINUOUS_WALKING_MIN`. Gate on the unit token: `分钟` / `min` → duration codes;
   `米` / `m` / `km` / `公里` → distance codes. Today a duration becomes a distance cap.
2. **Scope gating.** `每天` / `daily` / `per day` must suppress `MAX_WALKING_PER_LEG_M`
   (`我每天走路不能超过 3000 米` currently publishes the daily budget as a per-leg cap too).
3. **`0 m` policy (`DEFECT_MATRIX.md` P0-7, stated but not implemented).** When the parsed bound is
   `0` (or below any plausibility floor), emit `needs_clarification: True` and do not persist it as
   a clean authoritative cap.

**Acceptance.**

```
python tools/v192_probe_p0_numeric.py A
  -> n2_n3_defects: 0   (was 6/6)
  -> n1_violations: 0   (was 3/7)
python tools/v192_probe_capability_semantics.py A
  -> G4_zero_policy ok; G4_numeric 8/8
python tools/v192_probe_km_trace.py
  -> clauses no longer contain a split '1' + '5'
cd backend && python -m pytest tests/test_v192_shadow_trial_gate.py -q -k "numeric or decimal or zero or daily or minutes"
  -> 5 passed
```

---

## P0-3 — Safety-relevant needs are silently dropped

**Symptom.** 7 of 8 probe sentences produce **no capability at all**. Three of them are
**regressions** against V19.1 C:

| Sentence | V19.1 C | V19.2 A |
|---|---|---|
| `if possible I need step-free access` | HARD | *(nothing)* |
| `我妈妈要午休` | STRONG | *(nothing)* |
| `如果能推婴儿车就方便多了` | STRONG | *(nothing)* |
| `如果可能的话我需要无障碍通道` | — | *(nothing)* |
| `我可能需要轮椅` | — | *(nothing)* |
| `maybe I need a wheelchair` | — | *(nothing)* |
| `我父亲走不了远路` | — | *(nothing)* |

**Root cause.** `app/capabilities.py:251`

```python
if speculative or third_party or facility_only: continue
```

A whole-sentence discard, driven by three marker sets that are too broad:

- `line 112` `_SPECULATIVE_MARKERS` contains `如果`, `if `, `maybe`, `might` — a hedged *request* is
  not a hypothetical.
- `line 113` `_THIRD_PARTY_MARKERS` contains `我妈妈`, `我父亲`, `my mother`, `my father` — a
  **travelling companion** is not an unrelated third party.
- `line 88` `_NEGATED_MARKERS` contains `可能`, `也许`, so `我可能需要轮椅` reads as a denial.

**Minimal change — downgrade, never discard.**

```python
if facility_only:
    continue
if speculative or third_party:
    severity = "STRONG"                 # surfaced, never silently HARD
    needs_confirmation = True
```

plus, in the negation test at `line 243`, do not treat a clause as negated when it also carries a
first-person need marker and a capability token (`我可能需要轮椅`, `maybe I need a wheelchair`).

For companions, the discriminator is whether the clause **excludes** the traveller
(`not me`, `不是我要`, `我不需要`) — only then is it a third-party sentence. `我妈妈要午休` and
`我父亲走不了远路` describe the journey's own party and must produce a capability.

**Acceptance — all three must hold at once.**

```
python tools/v192_probe_p0_numeric.py A
  -> n4_empty: 0   (was 8/8 empty)
python tools/v192_probe_capability_semantics.py A
  -> G1_false_hard 9/9 still clean      (do NOT re-introduce false-HARD)
  -> G1_mandated_guard 2/2 still HARD   (do NOT over-filter)
cd backend && python -m pytest tests/test_v192_shadow_trial_gate.py -q -k "dropped or third_party or speculation or mandated"
  -> 11 passed
```

---

## P1-1 — A journey starts on expired provider evidence

`POST /start` (`main.py:4879`) does not re-validate the selected plan's frozen mobility evidence.
Measured: candidate path 4/4 staleness shapes → 409 with a distinct message, and
`validate_selected_plan_feasibility` correctly raises
`ValueError: STALE_RECOMPOSE_REQUIRED: PlanVersion frozen mobility evidence expired` — but
`/start` on that same plan returns **200**, the journey stays `ACTIVE`, and `/experience` says
nothing (`experience_flags_staleness: false`).

**Minimal change.** Call the existing guard before activating, exactly as the select path does
(`_assert_selected_plan_feasible`, `main.py:4469`, wired into `operations` at 8720 / 8796), and
surface the same signal through `/experience`.

**Acceptance.** `tests/test_v192_shadow_trial_gate.py -k start_refuses_expired` passes; the four
`select` staleness shapes stay 409 (`test_v192_guard_stale_candidate_is_refused`).

---

## P1-2 — A mid-trip HARD need has no consequence

The good guard holds: plans are **not** silently rewritten (`plans_mutated_silently: false`, plan
signatures identical before/after), `/confirm` is correctly required
(`409 "hard capability needs require /confirm"`), and the mutation is audited
(`traveler.capability.created`). What is missing is the positive consequence: after confirming a
HARD need on an `ACTIVE` journey, `replan_proposals: 0` and `experience_mentions_review: false`.

**Minimal change.** On HARD capability confirmation against an `ACTIVE` journey, create a replan
proposal (or set a `needs_review` flag that `/experience` reports). Do **not** mutate the active
plan in place — that behaviour is correct today and is guarded.

**Acceptance.** `tests/test_v192_shadow_trial_gate.py -k midtrip` passes.

---

## P2 — still reproducible, lower priority

| # | Item | Location | Note |
|---|---|---|---|
| 1 | `{"evidence_status": "VERIFIED"}` → `ACCESSIBILITY_UNVERIFIED` → 422 / 0 plans | `capabilities.py:490` `evaluate_accessibility_requirement` | never reads `evidence_status`; only the legacy `accessibility_state()` does. Also fails on V19.1 C — long-standing |
| 2 | top-level `step_free_verified` is dropped | `replanning/feasibility.py:265-273` whitelist | add `step_free_verified`, `route_step_free`, `route_step_free_verified`, `has_stairs`, `step_count`, `steps`, `highway`. **This is the one half of `V19_2_VERIFIED_STARTER.patch` that was never merged** |
| 3 | nested `osm_tags` contradiction → `UNVERIFIED` not `CONFLICT` | `capabilities.py:490` area | reads only top-level `facts.get("step_count", facts.get("steps"))`; the flat forms already work |
| 4 | natural `不超过 N 米` phrasing | `capabilities.py:250` trigger list | `每段不超过 100 米` / `单段步行不超过 100 米` / `每次走路不超过 100 米` / `不要走超过 100 米` produce nothing |
| 5 | `INFANT_NAP_WINDOW` has no `defaulted_window` flag | `capabilities.py:316` | `MIDDAY_REST_WINDOW` does; add parity |
| 6 | `generate` folds all failure reasons into one sentence | `main.py:3635` | `select` already returns an accurate `LOCKED_COMMITMENT_LOST:<key>`; `generate` returns `details: null` |
| 7 | `test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]` | — | the **only** regression this round; resolved by P0-2 |

---

## Patch status

| Patch | Verdict |
|---|---|
| `V19_1_LOW_CONFLICT_FIXES.patch` | **do not apply** — `patch does not apply` at `capabilities.py:326` |
| `V19_2_VERIFIED_STARTER.patch` | **do not apply** — `capabilities.py:110` fails; its `capabilities.py` substance is already merged. Re-derive **only** the `feasibility.py` whitelist half against the current file |
| `V19_1_TESTS_ONLY.patch` | safe, all `new file mode` — apply if not already |
| **`V19_2_TESTS_ONLY.patch`** | **apply this** — 2 new files under `backend/tests/`, 818 lines, `git apply --check` PASS, no production module touched |

Once `V19_2_TESTS_ONLY.patch` is applied, the loop is mechanical:

```
cd backend && python -m pytest tests/test_v192_shadow_trial_gate.py -q
```

`24 failed, 37 passed` today. Every fix turns its own `test_v192_defect_*` green; rename it to a
guard when that happens, and re-check that the `test_v192_guard_*` set stays at 37/37.
