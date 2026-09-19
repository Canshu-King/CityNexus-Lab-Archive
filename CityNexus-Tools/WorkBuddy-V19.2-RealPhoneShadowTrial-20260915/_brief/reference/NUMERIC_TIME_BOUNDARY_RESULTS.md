# NUMERIC_TIME_BOUNDARY_RESULTS.md

**Scope:** numeric walking limits and time windows — extraction, validation, and enforcement.
**Evidence:** `evidence/boundaries_a.json`, `evidence/boundaries_b.json`,
`evidence/boundaries.jsonl` (158 rows), `evidence/gate_codes_{a,b}.json`,
`evidence/eac_differential.jsonl`
**Probes:** `tools/v191_probe_boundaries.py`, `tools/v191_probe_gate_codes.py`,
`tools/v191_eac_differential.py`

**Delta targets:** `D4` walking/rest numerics — **6 `FIXED_IN_CURRENT` / 19
`STILL_REPRODUCIBLE`**; `D5` rest/nap windows — **2 / 6**. Identical at Snapshot A and B.

---

## 1. Every numeric and window case is blocked — including absurd ones

`tools/v191_probe_boundaries.py` drives the real HTTP surface (confirm → generate) per
`(code, params)` case:

| Family | Cases | Outcome |
|---|---|---|
| `MAX_WALKING_PER_LEG_M` | 15 | **422 / 0 plans** |
| `MAX_CONTINUOUS_WALKING_MIN` | 6 | **422 / 0 plans** |
| `MAX_DAILY_WALKING_M` | 4 | **422 / 0 plans** |
| `MIDDAY_REST_WINDOW` | 12 | **422 / 0 plans** |
| `INFANT_NAP_WINDOW` | 12 | **422 / 0 plans** |
| `REST_EVERY_MIN` | 6 | 422 / 0 plans (except the `max_min` case — §3) |
| `TOILET_BREAK_EVERY_MIN` | 6 | 422 / 0 plans |

Every case fails — **including `max_m = 10**12` and a whole-day `00:00–23:59` window.** A
limit of one trillion metres, or a rest window covering the entire day, is treated exactly
like a 300 m limit.

### Why: the gate never compares the value

The mock mobility matrix provides no walking distances, so every leg emits
`NEEDS_LIVE_EVIDENCE:MAX_WALKING_PER_LEG_M:{pair}` before the configured limit is ever
consulted. From `evidence/gate_codes_a.json`, the gate produced per call:

| Gate failure code | Observed |
|---|---|
| `NEEDS_LIVE_EVIDENCE:MAX_WALKING_PER_LEG_M:{pair}` | ×9 per call |
| `CAPABILITY_PARAMS_INVALID:{code}` | present |
| `REST_WINDOW_UNSATISFIED:{code}` | present |
| `ACCESSIBILITY_UNVERIFIED:{place}` | present |
| `NEEDS_LIVE_EVIDENCE:{place}` | present |
| `BREAK_INTERVAL_UNSATISFIED:{code}` | present |
| `LOCKED_COMMITMENT_LOST:{key}` | present |

So "numeric limits are enforced" is really **"planning is always blocked when a numeric
capability is present"**. The configured number has no effect on the outcome — the failure is
an evidence failure, not a limit violation. `MAX_WALKING_PER_LEG_EXCEEDED` was never observed.

---

## 2. A missing numeric parameter makes the journey permanently unplannable

| Params | Result |
|---|---|
| `MAX_WALKING_PER_LEG_M` with **no** `max_m` | `CAPABILITY_PARAMS_INVALID` → **422** |
| `MAX_WALKING_PER_LEG_M` with `max_m: 500` | `NEEDS_LIVE_EVIDENCE` → **422** |

Both block, but for different reasons, and the first is unrecoverable by waiting for provider
data — the capability itself is malformed and nothing validates it at confirm time. A user who
says "I can't walk far" without a number creates a journey that can never be planned.

---

## 3. The parameter-key contract is inverted — the canonicalizer's own key is the silent one

`feasibility.py:701-703`:

```python
if code == "REST_EVERY_MIN":
    interval = int(params.get("max_min"))       # <- reads "max_min"
if code == "TOILET_BREAK_EVERY_MIN":
    interval = int(params.get("max_min"))
```

`capabilities.py` emits exactly `{"max_min": rest_every}` (line 272) — so the extractor and the
gate agree on `max_min`. But:

| Params sent | Result |
|---|---|
| `{"max_min": 30}` (the canonical key) | **201 / 3 plans — accepted and NOT enforced** |
| `{"every_min": 30}` (a plausible key) | 422 `CAPABILITY_PARAMS_INVALID` |
| `{}` | 422 `CAPABILITY_PARAMS_INVALID` |

So the **correct** key is silently accepted without being enforced, while a wrong key is
loudly rejected. Nothing validates `params` on the confirm path, so an unenforceable
capability can be persisted as if it were active.

---

## 4. `EAC_REFERENCE` — numeric parsing works, validation is absent

EAC recovers **16 walking-numeric cases** and **4 window cases** that `FINAL_V19` lost
(`eac_differential.jsonl`). But `_bounded_number()` is not applied to the walking term:

| Text | `FINAL_V19` | `EAC_REFERENCE` | Problem |
|---|---|---|---|
| `走路不能超过 500 米` | `[]` | `MAX_WALKING_PER_LEG_M` | correct |
| `走路不能超过 0 米` | `[]` | `MAX_WALKING_PER_LEG_M` | **0 m** |
| `走路不能超过 1 米` | `[]` | `MAX_WALKING_PER_LEG_M` | 1 m |
| `走路不能超过 -5 米` | `[]` | `MAX_WALKING_PER_LEG_M` | **negative** |
| `走路不能超过 10000 米` | `[]` | `MAX_WALKING_PER_LEG_M` | **10 km per leg** |
| `我每天走路不能超过 3000 米` | `MAX_DAILY_WALKING_M` | `MAX_DAILY_WALKING_M` + `MAX_WALKING_PER_LEG_M` | over-extraction |
| `连续走不超过 15 分钟` | `MAX_CONTINUOUS_WALKING_MIN` | `MAX_CONTINUOUS_WALKING_MIN` + `MAX_WALKING_PER_LEG_M` | over-extraction |
| `中午能休息一下就更好了` | `[]` | `MIDDAY_REST_WINDOW` | hedged wish → care requirement |
| `我最多走 500 米，尽量吧` | `[]` | `MAX_WALKING_PER_LEG_M` | hedged wish |

In `FINAL_V19` these were **silent no-ops**; EAC converts them into **active wrong
constraints**. `0`, `1` and `-5` metres as a HARD `MAX_WALKING_PER_LEG_M` make the journey
unplannable, and per §1 the gate will never explain why.

---

## 5. Window parsing

`_window_from_params()` accepts `"HH:MM"` or an integer minute count, requires
`0 <= value <= 1440`, and requires `end > start`; otherwise it returns `None`. Measured
behaviour:

| Input | Result |
|---|---|
| `{"start":"12:00","end":"14:00"}` | accepted; window logic runs |
| `{"start":"00:00","end":"23:59"}` | accepted — a whole-day window is not rejected |
| invalid window (e.g. `end <= start`) | `d5[invalid window]` now **`FIXED_IN_CURRENT`** |
| `{"start":"13:00","end":"15:00"}` for `INFANT_NAP_WINDOW` | `d5[naptime 13:00-15:00]` now **`FIXED_IN_CURRENT`** |

`D5` therefore improved by 2 assertions but 6 remain `STILL_REPRODUCIBLE`.

---

## 6. Verdict table

| # | Finding | Result | Tag |
|---|---|---|---|
| 1 | Configured numeric limits are actually compared | **VIOLATED** — all cases blocked by missing evidence, never by the limit | `FINAL_V19` |
| 2 | An absurd limit (`10**12`) is rejected or behaves differently | **VIOLATED** — identical to a 300 m limit | `FINAL_V19` |
| 3 | A missing numeric parameter is validated at confirm time | **VIOLATED** — persisted, then permanently unplannable | `FINAL_V19` |
| 4 | `params` keys are validated against the gate's contract | **VIOLATED** — correct key silently unenforced, wrong key rejected | `FINAL_V19`, `NEW` |
| 5 | Numeric values are range-checked | `FINAL_V19` n/a; **`EAC_REFERENCE` VIOLATED** (0 / −5 / 10000 m) | `NEW` |
| 6 | One clause emits one code | `FINAL_V19` yes; **`EAC_REFERENCE` VIOLATED** (over-extraction) | `NEW` |
| 7 | Walking numerics are extracted from text | **VIOLATED** in `FINAL_V19` (16/20 lost); **FIXED** in `EAC_REFERENCE` | `FINAL_V19`, `EAC_REFERENCE` |
| 8 | Rest / nap windows are extracted from text | **VIOLATED** in `FINAL_V19` (6/10 lost); **FIXED** in `EAC_REFERENCE` | `FINAL_V19`, `EAC_REFERENCE` |
| 9 | Invalid time windows are rejected | **FIXED_IN_CURRENT** | — |
| 10 | A whole-day window is rejected | **VIOLATED** | `FINAL_V19` |

## 7. Recommendation (not applied)

1. Apply `_bounded_number(value, minimum=1, maximum=100_000)` to every extracted numeric
   walking term; drop the capability when the value is out of range.
2. Validate `params` on the confirm path against the gate's key contract
   (`max_m` / `max_min` / `start`+`end`) and return `422` naming the offending code and key.
3. Emit exactly one code per clause — prefer the most specific (`MAX_DAILY_WALKING_M` for a
   daily limit, `MAX_CONTINUOUS_WALKING_MIN` for a duration).
4. Distinguish "limit exceeded" from "limit unverifiable" in the gate's failure codes, and
   surface the distinction to the client (`MAX_WALKING_PER_LEG_EXCEEDED` vs
   `NEEDS_LIVE_EVIDENCE:…`), which also fixes the single-generic-message problem in
   `FEASIBILITY_EVIDENCE_RESULTS.md`.
