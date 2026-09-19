# Numeric / Time Boundary Semantics — V19.2

Evidence: `evidence/p0_numeric_a.json`, `evidence/p0_numeric_b.json`,
`evidence/cross_snapshot_numeric.json`, `evidence/corpus_delta_c_to_a.json`.
All rows were produced by calling the live extractor, never by reading a diff.

**Summary: V19.2 made numeric extraction reachable for the first time, and in doing so exposed
three silent-corruption defects that are worse than the previous silence.**

---

## The headline: a decimal walking limit becomes a 1500× understated HARD cap

```
走路不能超过 1.5 公里
  -> MAX_WALKING_PER_LEG_M  HARD  JOURNEY  {'max_m': 1, 'needs_clarification': False}
```

A traveller says they cannot walk more than **1.5 km**. The system records a HARD
**1 metre** per-leg cap and marks it as *not needing clarification*. Every plan leg longer than
one metre is infeasible, so the trip cannot be planned at all — and the UI presents the wrong
number as authoritative rather than asking.

### Root cause (confirmed by step trace, `tools/v192_probe_km_trace.py`)

`extract_capabilities_from_text` splits the sentence into clauses with:

```python
re.split(r"[,，。；;.!?！？\n]+|\bbut\b|\bhowever\b|但|但是|不过", raw_value)
```

`.` is a member of that character class, so `1.5` is split into `1` and `5`:

```
raw_value : '走路不能超过 1.5 km'
clauses   : ['走路不能超过 1', '5 km']
value     : '走路不能超过 1 5 km'
number_before TERMS2 : 1
```

`_number_before` itself is correct — called directly on the raw sentence it returns **1500**.
The value is destroyed before the parser ever sees it. The regex is unchanged from V19.1
(`snapshot_c/app/capabilities.py:224`), so the bug is old — but V19.1 never reached this code
path for walking limits, because `不能超过` was not a walking trigger. V19.2 added that trigger,
so the defect is **newly reachable**: it changes the product from "silently produces nothing"
to "silently produces a confident wrong value".

## Full decimal / zero matrix

| Input | Expected `max_m` | Actual | `needs_clarification` | Verdict |
|---|---|---|---|---|
| `走路不能超过 1.5 公里` | 1500 | **1** | false | DEFECT |
| `走路不能超过 2.5 公里` | 2500 | **2** | false | DEFECT |
| `走路不能超过 0.5 公里` | 500 | **0** | false | DEFECT |
| `走路不能超过 1.5 米` | 2 | **1** | false | DEFECT |
| `走路不能超过 0.5 米` | 1 | **0** | false | DEFECT |
| `走路不能超过 0 米` | rejected or flagged | **0** | **false** | DEFECT (road-prep P0-7 policy) |

`0.5 公里` producing `max_m: 0` is the specific case `DEFECT_MATRIX.md` P0-7 names: *"local
fallback must not persist `0 m` as a clean authoritative numeric cap."* It does.

## Unit confusion: minutes become metres

| Input | Capabilities produced |
|---|---|
| `连续走不能超过 20 分钟` | `MAX_WALKING_PER_LEG_M **HARD** max_m=20` **and** `MAX_CONTINUOUS_WALKING_MIN HARD max_min=20` |
| `连续走不能超过 45 分钟` | `MAX_WALKING_PER_LEG_M **HARD** max_m=45` **and** `MAX_CONTINUOUS_WALKING_MIN HARD max_min=45` |
| `我每天走路不能超过 3000 米` | `MAX_WALKING_PER_LEG_M HARD max_m=3000` **and** `MAX_DAILY_WALKING_M HARD max_m=3000` |
| `走路不能超过 500 米` | `MAX_WALKING_PER_LEG_M HARD max_m=500` ✅ (no minutes cap — correct) |

`_number_before` returns a bare number and discards the unit; the walking branch then feeds that
number into a metres parameter regardless of the unit that followed it. A 20-**minute**
continuous-walking limit therefore becomes a HARD 20-**metre** per-leg cap — every leg over 20 m
is infeasible.

## Cross-snapshot comparison (`evidence/cross_snapshot_numeric.json`)

| Input | FINAL_V19 (B) | V19.1 (C) | V19.2 (A) |
|---|---|---|---|
| `走路不能超过 100 米` | MISSING | MISSING | **100** |
| `走路不能超过 500 / 501 米` | MISSING | MISSING | **500 / 501** |
| `走路不能超过 1 km / 1 公里` | MISSING | MISSING | **1000** |
| `走路不能超过 1.5 km` | MISSING | MISSING | **1** ❌ |
| `走路不能超过 0.5 km` | MISSING | MISSING | **0** ❌ |
| `走路不能超过 0 米` | MISSING | MISSING | **0** ❌ |
| `连续走路不能超过 30 分钟` | 30 | 30 | 30 ✅ |
| `每天走路不能超过 5000 米` | 5000 | 5000 | 5000 ✅ |
| `每隔 60 分钟休息一次` | MISSING | 60 | 60 ✅ |
| `每隔 90 分钟上厕所` | MISSING | 90 | 90 ✅ |
| `午休 12:00 到 14:00` | 12:00 | 12:00 | 12:00 ✅ |
| `午休 15:00 到 13:00` (reversed) | `12:00` (invented) | `15:00` (reversed) | **MISSING + `needs_clarification`** ✅ |

**FIXED in V19.2:** reversed windows are rejected rather than silently defaulted or reversed.
**NEW in V19.2:** integer and km walking limits are extracted for the first time.
**NEW DEFECT in V19.2:** decimals are corrupted by the clause splitter.

## Time windows

| Behaviour | V19.2 |
|---|---|
| Reversed window (`15:00 到 13:00`) | rejected, `needs_clarification: true` ✅ |
| Explicit window (`12:00 到 14:00`) | `{'start': '12:00', 'end': '14:00'}` ✅ |
| Rest with no stated times (`午休从 13 点开始`) | `defaulted_window: true` ✅ (new in V19.2) |
| Nap with no stated times (`宝宝需要午睡`) | `{'start': '13:00', 'end': '15:00'}`, **no flag** ❌ |

`MIDDAY_REST_WINDOW` gained the `needs_clarification` / `defaulted_window` transparency flags;
`INFANT_NAP_WINDOW` (the very next statement) did not. The merge is asymmetric.

## Trigger-token coverage

`evidence/capability_semantics_a.json` → `G4b_natural_phrasing` (2/6):

| Phrasing | Result |
|---|---|
| `walk no more than 100 m` | ✅ extracted |
| `cannot walk more than 100 m` | ✅ extracted |
| `每段不超过 100 米` | ❌ nothing |
| `单段步行不超过 100 米` | ❌ nothing |
| `每次走路不超过 100 米` | ❌ nothing |
| `不要走超过 100 米` | ❌ nothing |

The trigger list contains `不能超过` but not `不超过`, so the more idiomatic Chinese phrasing —
`不超过 N 米` — is invisible. Not a regression (V19.1 had no trigger at all), but a coverage gap
that will bite on a real phone where travellers type naturally.

## Exact reproduction

```
cd D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915
python tools/v192_probe_capability_semantics.py a     # G4_numeric, G4_zero_policy, G4_nap, G4b
python tools/v192_probe_p0_numeric.py a               # N1 unit confusion, N2/N3 decimals
python tools/v192_probe_km_trace.py a                 # the clause-split trace
python tools/v192_cross_snapshot_numeric.py           # B / C / A comparison
python tools/v192_corpus_delta.py                     # 120-case corpus, C -> A
```

## What Codex should do

1. **Stop `.` from splitting numbers.** The minimal change is to make the separator conditional:
   `(?<!\d)\.(?!\d)` instead of a bare `.` in the character class. That preserves sentence
   splitting (`1.5 km. Then`) while protecting `1.5`.
2. **Refuse a numeric cap below the unit's floor.** `max_m < 1` and `max_min < 1` must become
   `needs_clarification: true` rather than a clean HARD value. This single guard fixes `0 米`,
   `0.5 公里 → 0`, and the `-5` family together.
3. **Make `_number_before` unit-aware.** It must return `(number, unit)` and the caller must
   reject a minutes value for a metres parameter. `连续走不能超过 20 分钟` must not produce
   `MAX_WALKING_PER_LEG_M`.
4. **Do not double-count a daily cap as a per-leg cap** (`我每天走路不能超过 3000 米`).
5. Add `不超过` to the walking trigger list.
6. Give `INFANT_NAP_WINDOW` the same `defaulted_window` / `needs_clarification` treatment as
   `MIDDAY_REST_WINDOW`.
