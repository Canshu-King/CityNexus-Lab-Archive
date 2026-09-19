# V19 Fix Delta — what changed in the main tree mid-run, and what it does not yet fix

**Author:** WorkBuddy V19 capability red team
**Date:** 2026-09-15
**Status:** measured, reproducible, scoped

---

## 0. Why this document exists

All nine V19 reports were measured against a read-only snapshot of
`D:\moodle\CityNexus` taken at **10:23** (`BASELINE_SOURCE.txt`, `repo_copy/`).
While the red team was running, Codex landed a **new capability domain** in the
main tree. Twelve files that the V19 findings depend on changed between
**10:56 and 11:19**.

This document does three things and nothing else:

1. Records exactly what changed, with hashes, so the V19 reports can be read
   with the right baseline in mind. **The nine V19 reports are not rewritten** —
   they remain an accurate description of the 10:23 baseline.
2. Measures the *same 494-case corpus* against the new code, so the delta is
   comparable rather than anecdotal.
3. Reports what the new code still does not do, with failing tests as proof.

**One P0 operational fact first:** as of 11:37 the main tree **cannot be
imported at all**. See §2.

---

## 1. What changed

Twelve files differ from the 10:23 baseline. All twelve were re-verified
byte-identical against the live tree at 11:37 (`evidence/main_tree_changes_during_v19.json`).

| File | Baseline mtime | New mtime |
|---|---|---|
| `backend/app/main.py` | 09-15 02:52:48 | 09-15 11:18:27 |
| `backend/app/replanning/feasibility.py` | 09-13 23:02:30 | 09-15 11:19:37 |
| `backend/app/services.py` | 09-13 18:01:07 | 09-15 11:17:29 |
| `backend/app/agent/mission_plan.py` | 09-15 01:50:10 | 09-15 11:14:10 |
| `backend/app/agent/mission.py` | 09-15 01:39:38 | 09-15 11:13:56 |
| `backend/app/integrations/ai/copilot_contract.py` | 09-14 20:31:51 | 09-15 11:12:45 |
| `backend/app/integrations/ai/semantic_compiler.py` | 09-14 16:12:37 | 09-15 11:12:15 |
| `backend/app/execution/traveler_twin.py` | 09-12 12:31:19 | 09-15 10:57:32 |
| `backend/app/schemas.py` | 09-14 01:08:04 | 09-15 10:56:56 |
| `backend/app/db/models.py` | 09-13 20:07:43 | 09-15 10:56:34 |
| `backend/app/db/session.py` | 09-13 20:08:25 | 09-15 10:56:34 |
| `backend/db/schema.sql` | 09-13 20:07:56 | 09-15 10:56:34 |

Plus one new file: **`backend/app/capabilities.py`** (15,283 bytes, 10:53).

A second read-only snapshot was taken for measurement:
`repo_copy_current/` + `BASELINE_SOURCE_CURRENT.txt`.

### 1.1 What the new module contains

`app/capabilities.py` is a real, well-shaped capability contract — it is close
to the P0-1 recommendation in `CODEX_HANDOFF_AFTER_V19.md`:

- `CAPABILITY_CODES` — 15 codes (`STEP_FREE_REQUIRED`, `AVOID_STAIRS`,
  `MAX_WALKING_PER_LEG_M`, `MIDDAY_REST_WINDOW`, `INFANT_NAP_WINDOW`,
  `TOILET_BREAK_EVERY_MIN`, `STROLLER`, `LARGE_LUGGAGE`, `SLOW_PACE`,
  `QUIET_ENVIRONMENT`, …)
- `CAPABILITY_SEVERITIES = ("HARD", "STRONG", "SOFT")`
- `CAPABILITY_SCOPES = ("TRAVELER", "JOURNEY")`
- `ACCESSIBILITY_STATES` including `ACCESSIBILITY_VERIFIED` /
  `ACCESSIBILITY_UNVERIFIED` / `ACCESSIBILITY_CONFLICT` / `NEEDS_LIVE_EVIDENCE`
- `extract_capabilities_from_text()` — deterministic extractor, documented as
  "a conservative fallback and a post-model safety net"
- `canonicalize_capabilities()` — validates model output; its comment states
  *"A hard accessibility capability may not be downgraded by a model or by an
  API client that mislabeled its class"*
- `capability_constraints()` — projects HARD items into the existing gate shape
- `summarize_capabilities()`, `accessibility_state()`

Supporting wiring also landed: a `traveler_capabilities` table
(`UNIQUE(traveler_id, journey_id, scope, code)`, `severity CHECK IN
('HARD','STRONG','SOFT')`), `SemanticEnvelope.capabilities` with a severity and
scope enum, and `CapabilityInput` in `schemas.py`. `semantic_compiler.py` now
merges model capabilities with the local extractor:

```python
local = extract_capabilities_from_text(message, scope="JOURNEY")
merged = canonicalize_capabilities(
    [*envelope.capabilities, *local], source="SEMANTIC", provenance="USER_STATED"
)
```

---

## 2. P0 BLOCKER — the main tree cannot start

Reproduced at 11:37:

```
$ cd D:\moodle\CityNexus\backend
$ .venv/Scripts/python.exe -c "import app.main"
ImportError: cannot import name 'capability_payload' from 'app.capabilities'
  File "D:\moodle\CityNexus\backend\app\main.py", line 66, in <module>
    from app.capabilities import (
        CAPABILITY_CODES, canonicalize_capabilities, capability_payload, summarize_capabilities,
    )
```

`capability_payload` is referenced at **five** call sites in `main.py`
(lines 66, 1843, 1849, 1895, 8152) and is **not defined anywhere** in
`capabilities.py`. It is the only missing symbol — every other name imported
from `app.capabilities` across the whole backend resolves
(`evidence/main_tree_changes_during_v19.json`, AST check).

Expected shape, from the call sites:

```python
capability_payload(session, traveler_id, journey_id=None) -> list[dict]
```

`list_traveler_capabilities` calls `capability_payload(session, traveler.id)`;
`list_journey_capabilities` calls `capability_payload(session, journey.traveler_id, journey.id)`;
`_replace_capability_rows` returns it; the V8 experience payload embeds it. The
returned rows are fed straight into `summarize_capabilities()`, so each row must
be the `CapabilityItem.as_dict()` shape (`code`/`class`/`severity`/`params`/`scope`/…).

**Consequence:** the backend cannot import, so it cannot start. Ports **8000 and
5173 are not listening** — Codex's own dev instance is down as well. This is not
a V19 finding; it is a one-function blocker in the current tree, and it is why
the 40-test V19 suite and the 23-test post-fix suite could not be run over HTTP
against the live tree.

---

## 3. What the new module gets right

Six contract guards were verified and **pass**:

| Guard | Result |
|---|---|
| `accessibility_state(None)` / `({})` / `({"name": "Wheelchair ramp entrance"})` | all `ACCESSIBILITY_UNVERIFIED` — **unknown is never treated as verified** |
| `accessibility_state({"step_free": True})` | `ACCESSIBILITY_VERIFIED` |
| `accessibility_state({"step_free": False})` / `({"stairs": True})` | `ACCESSIBILITY_CONFLICT` |
| SOFT preference never reaches the gate | `最好少走点楼梯，能坐电梯就坐电梯` → `[]` constraints |
| Unknown capability code is dropped | `NOT_A_REAL_CODE` → `()` |
| Clean hard sentence is understood | `我用轮椅，必须全程 step-free，一步楼梯都不能走` → `STEP_FREE_REQUIRED` + `AVOID_STAIRS`, both `HARD`, both class `HARD_ACCESSIBILITY_NEED` |
| Hard code's class is corrected when mislabeled | `STEP_FREE_REQUIRED` + `class: SOFT_PREFERENCE` → class forced to `HARD_ACCESSIBILITY_NEED` |

Attack #1 from the red-team brief ("UNKNOWN accessibility treated as verified")
is **defeated at the module level**. That is genuine progress and should be kept.

---

## 4. What it does not fix — D1 to D7

Measured against the same 494-case corpus
(`evidence/capability_fix_delta.json`, `evidence/capability_backstop_probe.json`,
`evidence/capability_gate_probe.json`).

### D1 — the hard-downgrade guard is a tautology

```python
# capabilities.py, canonicalize_capabilities()
if code in HARD_ACCESSIBILITY_CODES and str(raw.get("severity") or "").upper() == "HARD":
    severity = "HARD"
```

The condition only fires when the caller **already said HARD**, so it is a
no-op. Of the 24-cell attack matrix (2 hard codes × 4 severities × 3 classes),
**18 cells accept a downgrade**:

| Model sends | Severity kept | Reaches the gate? |
|---|---|---|
| `{"code": "STEP_FREE_REQUIRED", "severity": "HARD"}` | `HARD` | yes |
| `{"code": "STEP_FREE_REQUIRED", "severity": "STRONG"}` | `STRONG` | **no** |
| `{"code": "STEP_FREE_REQUIRED", "severity": "SOFT"}` | `SOFT` | **no** |
| `{"code": "STEP_FREE_REQUIRED"}` (severity omitted) | `STRONG` | **no** |
| `{"code": "AVOID_STAIRS", "severity": "SOFT"}` | `SOFT` | **no** |

The class *is* forced back to `HARD_ACCESSIBILITY_NEED`, but `capability_constraints()`
gates on **severity**, not class — so a mislabeled class is cosmetic while a
mislabeled severity silently removes the need. The omitted-severity row is the
most likely real-world shape, because `default_severity()` returns `STRONG` for
`STEP_FREE_REQUIRED` unless `hard_asserted` is set.

This is the exact attack from the brief — **HARD need downgraded to SOFT** — and
it survived into the fix.

**Reachable end to end** because `canonicalize_capabilities()` does not
de-duplicate (§D3): when the model says `SOFT` and the local extractor also
fires, the merged list carries the code twice and the HARD copy still gates.
But when the local extractor is silent, the model's `SOFT` label is the only
authority — and the extractor is silent on **311 / 494 cases (63.0 %)**.

### D2 — the negation guard is text-global, and it cuts both ways

```python
if not value or any(marker in value for marker in _NEGATED_MARKERS):
    return ()
```

Any one of `没有 / 不需要 / 不用 / 无需 / 不是 / 以前 / 曾经 / 过去 / 历史 /
not wheelchair / used to / historically` **anywhere** in the sentence erases the
whole clause.

**Wrong direction A — a live hard need is erased (5 of the 169 hard-expected
cases):**

| Case | Text | Marker hit |
|---|---|---|
| `HS-003-HARD` | `wheelchair 必须 step-free，没有例外` | 没有 (in "没有例外" = *no exceptions*) |
| `HS-049-HARD` | `这个景点没有无障碍信息就不要排进去` | 没有 |
| `HS-051-HARD` | `没有 step-free 证据的地点 must 排除` | 没有 |
| `ACC-011` | `我坐轮椅，这个景点如果没有无障碍信息就不要排` | 没有 |
| `LUG-003` | `行李多，需要出租车而不是地铁` | 不是 |

`HS-049` and `HS-051` are the product's own accessibility policy — "exclude
places with no step-free evidence" — and both are deleted by the guard. Also
confirmed on constructed mixed sentences, all five returning `[]`:

- `我以前不用轮椅，但现在必须全程 step-free`
- `我没有过敏，但我用轮椅，必须全程无障碍`
- `过去我坐轮椅，现在必须全程无障碍`
- `I used to walk fine but now I use a wheelchair and need every leg step-free`

**Wrong direction B — a denial manufactures a HARD capability that blocks the
Journey.** `_HARD_MARKERS` contains `need` / `需要` / `必须`, which match inside
phrasings that *deny* or *speculate*:

| Case | Text | Result | Gate |
|---|---|---|---|
| `NEG-004-NEG` | `I don't need a wheelchair, I can walk` | `STEP_FREE_REQUIRED` HARD | **FAILS** |
| `NEG-009-NEG` | `朋友说我可能需要轮椅，但我不这么认为` | `STEP_FREE_REQUIRED` HARD | **FAILS** |
| `NEG-010-NEG` | `a friend said I might need a wheelchair, I disagree` | `STEP_FREE_REQUIRED` HARD | **FAILS** |
| `NEG-021-NEG` | `说不定到时候我需要轮椅` | `STEP_FREE_REQUIRED` HARD | **FAILS** |
| `NEG-022-NEG` | `maybe I'll need a wheelchair by then` | `STEP_FREE_REQUIRED` HARD | **FAILS** |
| `NEG-044-NEG` | `if I end up in a wheelchair I'll tell you` | `STEP_FREE_REQUIRED` HARD | **FAILS** |

A traveller who says *"I don't need a wheelchair, I can walk"* is now **blocked
from planning** — because the word `need` inside `don't need` is read as a hard
marker. 12 of 56 NEGATED cases still produce a capability; 6 of them are HARD.

**Separately, coverage:** the remaining **164 of 169** hard-expected-but-silent
cases are lexical gaps, not the guard. **111 of those 164 contain an explicit
hard marker** (`必须` / `must` / `cannot` / `required`) — the hardness signal is
present, the vocabulary table has no matching code path:

- `HS-005-HARD` `I cannot walk more than 500 metres per leg`
- `HS-006-HARD` `走路不能超过 500m，这是硬性要求`
- `HS-007-HARD` `中午 12 点到 14 点必须回酒店休息`
- `HS-008-HARD` `I must rest at the hotel between 12:00 and 14:00`
- `HS-010-HARD` `宝宝下午 1 点到 3 点必须睡午觉，不能安排活动`
- `HS-025-HARD` `严重花生过敏，餐厅必须确认无花生`

`_time_window()` requires two time literals *and* the phrase to match
`午休 / 中午休息 / midday rest`, so `中午 12 点到 14 点…休息` is missed.
`_number_before()` is only reached after a `walking` token from a narrow list
that excludes `不能超过` / `最多走` / `cannot walk more than`.

### D3 — no de-duplication by code

`canonicalize_capabilities()` appends every valid item; it never collapses by
`code`. One code can therefore arrive twice with conflicting severity, and
`summarize_capabilities()` reports it in **both** lists:

```
STEP_FREE_REQUIRED → hard: ["HARD","HARD"]   soft: ["SOFT"]
code_in_both_hard_and_soft: ["STEP_FREE_REQUIRED"]
```

Any consumer reading `summary["soft"]` sees a hard accessibility need listed as
a soft preference.

### D4/D5 — hard care and numeric limits are still not read

| Text | Capabilities extracted | Consequence |
|---|---|---|
| `老人中午 12 点到 14 点必须回酒店休息` | `[]` | need silently ignored |
| `走路不能超过 500m，这是硬性要求` | `[]` | need silently ignored |
| `我最多走 500 米，超过就走不动了` | `[]` | need silently ignored |
| `宝宝下午 1 点到 3 点必须睡午觉，不能安排活动` | `[]` | need silently ignored |
| `我需要每 60 分钟休息一次` | `REST_EVERY_MIN` | works |

V19 finding **F3 (numeric values never read)** is unchanged on this path: the
walking-limit sentence still yields no value at all.

### D6 — the capability layer emits rule codes the gate cannot interpret

`capability_constraints()` projects `rule_code` values from `CAPABILITY_CODES`.
`evaluate_feasibility()` implements nine codes:

```
BUDGET_MAX, JOURNEY_END_BY, JOURNEY_START_AT,
PLACE_UNAVAILABLE, PLACE_CLOSED, SERVICE_UNAVAILABLE, SERVICE_CLOSED,
REQUIRE_PLACE, LOCKED_COMMITMENT
```

The intersection with what the capability layer emits is **empty**
(`evidence/capability_gate_probe.json`):

```
emitted_by_capability_layer:    ["AVOID_STAIRS", "STEP_FREE_REQUIRED"]
interpreted_by_gate:            [9 codes above]
emitted_but_not_interpreted:    ["AVOID_STAIRS", "STEP_FREE_REQUIRED"]
```

So every capability-derived HARD constraint hits the fail-closed branch:

```
UNSUPPORTED_HARD_CONSTRAINT:STEP_FREE_REQUIRED
UNSUPPORTED_HARD_CONSTRAINT:AVOID_STAIRS
```

Measured end to end with a minimal but complete feasibility context (controls
verified healthy — no-constraint and supported-code runs both pass):

| Traveller says | Capabilities | Gate |
|---|---|---|
| `我用轮椅，必须全程 step-free，一步楼梯都不能走` | 2 × HARD | **FAILS** |
| `I use a wheelchair, every leg must be step-free` | 1 × HARD | **FAILS** |
| `我膝盖不行，不能走楼梯，请避免台阶` | 1 × HARD | **FAILS** |
| `老人中午 12 点到 14 点必须回酒店休息` | none | passes (need dropped) |
| `走路不能超过 500m，这是硬性要求` | none | passes (need dropped) |
| `希望安静一点，少刺激` | `QUIET_ENVIRONMENT` SOFT | passes |

**Across the full corpus, 82 of 494 cases (16.6 %) make the feasibility gate
fail**, every one of them with `UNSUPPORTED_HARD_CONSTRAINT`. The net effect of
the capability domain as it stands is to convert V19's *silent* failure into a
*blocking* failure — fail-closed, but unusable. The wheelchair traveller who
previously got a step-filled plan now gets no plan at all.

Also: `feasibility.py` does `from app.capabilities import accessibility_state`
but **never calls it** (0 call sites, verified by source inspection). The gate
does not consult provider accessibility evidence.

### D7 — TRAVELER scope is unreachable from language

`CAPABILITY_SCOPES` defines `TRAVELER` and `JOURNEY`, and `CapabilityInput`
defaults to `TRAVELER`. But `extract_capabilities_from_text()` only honours its
`scope` argument and never infers scope from language — across the corpus,
**201 of 201** emitted items are `JOURNEY`. `我用轮椅，这是永久情况，不只是这次旅行`
still yields `JOURNEY`.

V19 finding **F12 (cross-Journey scope)** therefore still has no language path:
"this trip only" and "always" are indistinguishable from text.

### Coverage and discrimination, before vs after

| Metric | V19 baseline (10:23) | Post-fix deterministic path |
|---|---|---|
| Corpus cases producing any capability | 0 / 494 (no domain existed) | **183 / 494 = 37.0 %** |
| Severity split | — | HARD 87, STRONG 85, SOFT 29 |
| Scope split | — | JOURNEY 201, TRAVELER 0 |
| Pair discrimination (167 pairs) | model 167/167 (100 %), server 82/167 (49.1 %) | **48/167 = 28.7 %** |
| — hard/soft pairs (51) | 51/51 | 14/51 |
| — negation pairs (56) | 56/56 | 9/56 |
| — ambiguous pairs (60) | 60/60 | 25/60 |
| Backstop silent | n/a | **311 / 494 = 63.0 %** |
| Hard-expected cases with no backstop | n/a | **169** |
| Cases that block the feasibility gate | 0 | **82 / 494 = 16.6 %** |

Coverage by bucket: `luggage_stroller` 24/30, `accessibility` 21/30,
`conflicting_needs` 10/20, `hard_soft_pair` 36/102, `elderly_infant` 10/30,
`ambiguous` 37/120, `negation_historical` 31/112, `rest_nap_numeric` 6/30.

The deterministic extractor is documented as a fallback, so 37 % coverage is not
by itself a defect — but note that as a **substitute** for the model it
discriminates 48/167 pairs, which is *worse than the pre-fix server path
(82/167)*. If the model is unavailable, this path must not be relied on.

---

## 5. Failing tests as proof

`repo_copy_current/backend/tests/test_v19_postfix_capability_contract.py`
(308-line patch: `patches/V19_POSTFIX_CAPABILITY_CONTRACT_TESTS.patch`,
`git apply -p1` verified byte-identical).

```
$ python -m pytest tests/test_v19_postfix_capability_contract.py -q
23 failed, 7 passed

$ python -m pytest tests/test_v19_postfix_capability_contract.py -q -k guard
6 passed, 24 deselected
```

- The **7 passing** tests are the guards in §3 (plus `REST_EVERY_MIN`, which
  works). They must stay green.
- The **23 failing** tests are D1–D7, one behaviour each, named
  `test_v19_char_d1a…` through `test_v19_char_d7a…`. Each is a contract
  assertion, not a description of current behaviour, so a correct fix flips them
  green with no test edit.

Full output: `evidence/postfix_test_run.txt`.

---

## 6. What to do, in order

1. **Define `capability_payload(session, traveler_id, journey_id=None)`** in
   `app/capabilities.py`. One function, five call sites, currently blocking the
   whole backend from importing. Nothing else can be verified until this lands.
2. **Make the downgrade guard real.** Force `severity = "HARD"` for any code in
   `HARD_ACCESSIBILITY_CODES`, regardless of what the caller sent — including
   when severity is omitted. Then re-check the 24-cell matrix: 24/24 must be
   `HARD`.
3. **Scope the negation guard to the clause, not the text.** Evaluate
   `_NEGATED_MARKERS` per clause (split on `，,。.;；`), and require a negation
   marker to be adjacent to the capability term rather than anywhere in the
   string. This fixes both directions: `没有例外` stops erasing the need, and
   `don't need a wheelchair` stops manufacturing one.
4. **Add `STEP_FREE_REQUIRED` and `AVOID_STAIRS` to the gate's interpretable
   set** — or stop projecting them as `rule_code` and introduce a dedicated
   capability gate. Right now 82/494 flows fail closed on codes the gate has
   never heard of. `accessibility_state()` is already imported in
   `feasibility.py`; use it.
5. **De-duplicate by `code` in `canonicalize_capabilities()`**, resolving
   conflicts in favour of the highest severity. A code must never appear in both
   `summary["hard"]` and `summary["soft"]`.
6. **Extend the lexical table** for the 111 hard-marker cases: `不能超过 N`,
   `最多走 N`, `cannot walk more than N`, `中午 HH 点到 HH 点…休息`,
   `must rest between HH:MM and HH:MM`, `必须睡午觉`. Use `_time_window()` for
   the rest/nap windows instead of requiring `午休`.
7. **Infer scope from language** (`永久` / `always` / `不只是这次` / `permanently`
   → `TRAVELER`), or drop `TRAVELER` from the extractor's contract and say so.

**Keep:** the accessibility-evidence state machine, the `HARD/STRONG/SOFT`
vocabulary, the `TRAVELER/JOURNEY` scopes, the conservative fail-closed
philosophy, and the class-correction rule. Those are the right shape. The gap is
that the layer is not yet connected to the gate, and its two guards are written
in a way that does not do what their comments say.

---

## 7. Reproduce

```bash
LAB="D:/moodle/CityNexus-Tools/WorkBuddy-V19-CapabilityRedTeam-20260915"
PY="D:/moodle/CityNexus/backend/.venv/Scripts/python.exe"

cd "$LAB"
$PY tools/v19_verify_current_capabilities.py     # -> evidence/capability_fix_delta.json
$PY tools/v19_probe_capability_backstop.py       # -> evidence/capability_backstop_probe.json
$PY tools/v19_probe_capability_gate.py           # -> evidence/capability_gate_probe.json

cd repo_copy_current/backend
$PY -m pytest tests/test_v19_postfix_capability_contract.py -q -p no:cacheprovider
```

All three probes import `app.capabilities` / `app.replanning.feasibility` from
`repo_copy_current` and never touch `D:\moodle\CityNexus`. Run Python with
`PYTHONDONTWRITEBYTECODE=1` if you point them at the live tree.

---

## 8. Honest limits of this delta

- **The delta is measured at the module level, not over HTTP.** `app.main`
  cannot be imported, so no request ever reached the new capability endpoints.
  Everything in §4 is a direct call into `app.capabilities` and
  `app.replanning.feasibility` from `repo_copy_current`, whose hashes match the
  live tree for all twelve changed files.
- **The 82/494 blocking figure uses a minimal feasibility context** (one
  activity, one place, a mock mobility provider). The failures it reports are
  `UNSUPPORTED_HARD_CONSTRAINT`, which is a property of the constraint, not of
  the fixture — controls with no constraints and with a supported code both pass.
- **`repo_copy_current` is not a complete tree.** It was collected with a
  restricted include list, so 5,475 files present in the live tree were not
  copied. Only the 12 changed files that also existed in the 10:23 baseline are
  compared in §1; all 12 match the live tree byte-for-byte.
- **The 23 failing tests describe the tree as of 11:38.** Codex is actively
  editing; re-run before acting on any individual item.
