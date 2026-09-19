# ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md

**Round:** CityNexus WorkBuddy V19.1 Convergence Red-Team — EAC-Aware Update
**Subject under test:** EAC reference implementation (`DSH-EAC-V19.1-AutonomousProductLab-20260915`)
and the current tree (Snapshot B / main tree, `app.capabilities` sha16 `7e3ff4cb3a85b7b6`)
**Evidence:** `evidence/accessibility_evidence_scope.json`, `evidence/eac_live.json`,
`evidence/openapi_drift.json`
**Probes:** `tools/v191_probe_accessibility_evidence.py`, `tools/v191_probe_eac_live.py`
**Verdict summary:** 5 of 26 tag-shape cases violate the brief. The brief's headline
requirement — *`toilets:wheelchair=yes` must never satisfy `STEP_FREE_REQUIRED`* — is
**violated on both the read endpoint and the feasibility gate**.

Finding tags: `FINAL_V19` (present in the current tree), `EAC_REFERENCE` (present in the
EAC lab), `NEW` (not previously reported).

---

## 1. Root cause (one sentence)

`overall_accessibility_state()` aggregates **every** provider fact into a single string
without filtering by `subject` or `code`, and `accessibility_state()` then reads only that
string — so a facility-scoped `VERIFIED` fact (`toilet`, `entrance`) is indistinguishable
from a place-scoped step-free verification.

```python
# EAC: app/integrations/accessibility/osm.py:284
def overall_accessibility_state(facts):
    states = {fact.state for fact in facts}          # <- no subject/code filter
    if "ACCESSIBILITY_CONFLICT" in states: return "ACCESSIBILITY_CONFLICT"
    if "NEEDS_LIVE_EVIDENCE" in states:    return "NEEDS_LIVE_EVIDENCE"
    if "ACCESSIBILITY_UNVERIFIED" in states: return "ACCESSIBILITY_UNVERIFIED"
    if "ACCESSIBILITY_VERIFIED" in states: return "ACCESSIBILITY_VERIFIED"
    return "NEEDS_LIVE_EVIDENCE"
```

```python
# EAC: app/replanning/feasibility.py:268-280  -> the bridge into the gate
raw_tags = metadata.get("tags")
if isinstance(raw_tags, Mapping) or isinstance(raw_tags, (list, tuple)):
    facts = evidence_from_osm_tags(raw_tags)
    if facts:
        return {"evidence_status": overall_accessibility_state(facts),
                "raw_tags": raw_tags}
```

```python
# app/capabilities.py:490  -> accessibility_state() reads only the aggregate
status = str(value.get("evidence_status") or value.get("status") or "").upper()
if status in ACCESSIBILITY_STATES:
    return status
```

`_capability_failure_for_record()` then treats `ACCESSIBILITY_VERIFIED` as
"need satisfied" and returns no failure, so the plan is allowed.

---

## 2. Tag-shape matrix — pure function, EAC implementation

`evidence/accessibility_evidence_scope.json`, 26 shapes, 21 PASS / 5 FAIL.

| Case | Tags | `overall_state` | facts (subject/code) | Verdict |
|---|---|---|---|---|
| `toilet_only` | `toilets:wheelchair=yes` | **ACCESSIBILITY_VERIFIED** | VERIFIED `TOILET`/`ACCESSIBLE_TOILET` | **FAIL — leak** |
| `entrance_wheelchair_only` | `entrance:wheelchair=yes` | **ACCESSIBILITY_VERIFIED** | VERIFIED `ENTRANCE`/`ENTRANCE_STEP_FREE` | **FAIL — leak** |
| `ramp_only` | `ramp=yes` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED `VERTICAL_ACCESS`/`RAMP_PRESENT` | PASS |
| `ramp_wheelchair_only` | `ramp:wheelchair=yes` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED `VERTICAL_ACCESS` | PASS |
| `elevator_only` | `elevator=yes` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED `VERTICAL_ACCESS`/`ELEVATOR_PRESENT` | PASS |
| `highway_elevator_only` | `highway:elevator=yes` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED `VERTICAL_ACCESS` | PASS |
| `wheelchair_yes_step_count_5` | `wheelchair=yes`+`step_count=5` | ACCESSIBILITY_CONFLICT | CONFLICT `STEP_COUNT`+`CONFLICTING_TAGS` | PASS |
| `wheelchair_yes_steps_yes` | `wheelchair=yes`+`steps=yes` | ACCESSIBILITY_CONFLICT | CONFLICT `STAIRS`+`CONFLICTING_TAGS` | PASS |
| `wheelchair_yes_highway_steps` | `wheelchair=yes`+`highway=steps` | ACCESSIBILITY_CONFLICT | CONFLICT `STAIRS`+`CONFLICTING_TAGS` | PASS |
| `wheelchair_yes_only` | `wheelchair=yes` | ACCESSIBILITY_VERIFIED | VERIFIED `PLACE`/`WHEELCHAIR_ACCESS` | PASS |
| `wheelchair_no_only` | `wheelchair=no` | ACCESSIBILITY_CONFLICT | CONFLICT `PLACE` | PASS |
| `wheelchair_limited` | `wheelchair=limited` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED `PLACE` | PASS |
| `kerb_only` | `kerb=lowered` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED `KERB` | PASS |
| `tactile_only` | `tactile_paving=yes` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED `ROUTE` | PASS |
| `empty_tags` | `{}` | NEEDS_LIVE_EVIDENCE | NEEDS_LIVE_EVIDENCE `PLACE` | PASS |
| `toilet_plus_ramp` | toilet + ramp | ACCESSIBILITY_UNVERIFIED | TOILET + VERTICAL | PASS |
| `toilet_plus_wheelchair_no` | toilet=yes + wheelchair=no | ACCESSIBILITY_CONFLICT | — | PASS |
| `toilet_plus_ramp_plus_wheelchair_yes` | toilet + ramp + **wheelchair=yes** | **ACCESSIBILITY_UNVERIFIED** | PLACE+TOILET+VERTICAL | **FAIL — over-block** |
| `list_value_wheelchair` | `{"wheelchair": ["yes"]}` | NEEDS_LIVE_EVIDENCE | **none (0 facts)** | **FAIL — silent drop** |
| `list_value_toilets` | `{"toilets:wheelchair": ["yes"]}` | NEEDS_LIVE_EVIDENCE | **none (0 facts)** | **FAIL — silent drop** |
| `tuple_value_ramp` | `{"ramp": ("yes",)}` | ACCESSIBILITY_UNVERIFIED | UNVERIFIED, `raw_value="('yes',)"` | PASS (garbage payload) |
| `list_value_step_count` | `{"step_count": [5]}` | ACCESSIBILITY_CONFLICT | CONFLICT, `raw_value="[5]"` | PASS (by accident) |
| `sequence_of_kv_strings` | `["wheelchair=yes","ramp=yes"]` | NEEDS_LIVE_EVIDENCE | placeholder only | PASS (masked drop) |
| `tags_nested_under_key` | `{"tags": {"wheelchair":"yes"}}` | NEEDS_LIVE_EVIDENCE | placeholder only | PASS (masked drop) |

### 2.1 `toilets:wheelchair=yes` satisfies `STEP_FREE_REQUIRED` — brief requirement violated

The EAC report documents this row as:

> `| toilets:wheelchair=yes | ACCESSIBILITY_VERIFIED | TOILET | scoped to the facility, not the route |`

The `subject: TOILET` scoping exists **on the fact**, but nothing downstream honours it.
Because `overall_accessibility_state()` discards `subject`, a place whose only tag is
`toilets:wheelchair=yes` yields `overall_state == ACCESSIBILITY_VERIFIED`, and the gate
returns **no failure** for `STEP_FREE_REQUIRED`. Same for `entrance:wheelchair=yes`.

**`ramp=yes` and `elevator=yes` behave correctly** (UNVERIFIED → blocked), and
**`wheelchair=yes + step_count=5` correctly conflicts** — those two brief requirements hold.
The toilet/entrance case is the one that fails.

### 2.2 A genuinely verified place is blocked by an unrelated partial tag

`{"wheelchair":"yes", "ramp":"yes"}` → `ACCESSIBILITY_UNVERIFIED`, because
`ACCESSIBILITY_UNVERIFIED` is tested **before** `ACCESSIBILITY_VERIFIED` in the precedence
chain. A place with explicit place-level `wheelchair=yes` evidence becomes unplannable the
moment any `ramp`/`elevator`/`kerb`/`tactile_paving` tag is also present.

This is a **false negative in production terms**: wheelchair users cannot plan to places
that genuinely are accessible. `wheelchair=yes + ramp=yes` is the *most common* real-world
OSM combination for an accessible venue.

### 2.3 List/tuple tag forms are silently dropped

`_text()` coerces with `str(value).lower()`, so a list value becomes the literal
`"['yes']"`, which matches none of the accepted literals:

| Shape | Result |
|---|---|
| `{"wheelchair": ["yes"]}` | no fact at all → 0 facts → `NEEDS_LIVE_EVIDENCE` |
| `{"toilets:wheelchair": ["yes"]}` | no fact at all → 0 facts → `NEEDS_LIVE_EVIDENCE` |
| `{"ramp": ("yes",)}` | bogus UNVERIFIED fact, `raw_value` `"('yes',)"` recorded in provenance |
| `{"step_count": [5]}` | CONFLICT emitted, `raw_value` `"[5]"` (right answer, wrong payload) |

So list handling is inconsistent: silently dropped for string-valued tags, accidentally
correct for `step_count`, and truthy-but-garbled for `ramp`. The garbled `raw_value` also
lands in the audit trail (`provenance.raw_value`).

Two further forms are dropped but **masked** by the `NEEDS_LIVE_EVIDENCE` placeholder fact,
so a naive "are there facts?" check cannot see the loss:

- `["wheelchair=yes", "ramp=yes"]` (a bare sequence of `k=v` strings)
- `{"tags": {"wheelchair": "yes"}}` (the key is not unwrapped)

Note the HTTP layer *does* unwrap these — `_parse_accessibility_place_tags()` in `main.py`
reads `metadata["accessibility"]`, `metadata["tags"]` and parses a `k=v` list from
`place.tags_json`. `evidence_from_osm_tags()` itself does not. See §4.

---

## 3. Live confirmation — the gate really does allow it

`evidence/eac_live.json`, EAC lab backend on a throwaway SQLite DB, in-process TestClient.
Every demo place tagged identically, then `POST /journeys/{id}/capabilities/confirm`
with `STEP_FREE_REQUIRED`/HARD, then `POST /journeys/{id}/plans/generate`.

| Case | Read endpoint | Gate (`accessibility_state`) | Gate outcome | Expected |
|---|---|---|---|---|
| `toilet_only` | ACCESSIBILITY_VERIFIED | **ACCESSIBILITY_VERIFIED** | **ALLOW** | BLOCK → **FAIL** |
| `entrance_only` | ACCESSIBILITY_VERIFIED | **ACCESSIBILITY_VERIFIED** | **ALLOW** | BLOCK → **FAIL** |
| `ramp_only` | ACCESSIBILITY_UNVERIFIED | ACCESSIBILITY_UNVERIFIED | BLOCK | BLOCK → PASS |
| `elevator_only` | ACCESSIBILITY_UNVERIFIED | ACCESSIBILITY_UNVERIFIED | BLOCK | BLOCK → PASS |
| `wheelchair_yes` | ACCESSIBILITY_VERIFIED | ACCESSIBILITY_VERIFIED | ALLOW | ALLOW → PASS |
| `wheelchair_yes_step_count_5` | ACCESSIBILITY_CONFLICT | ACCESSIBILITY_CONFLICT | BLOCK | BLOCK → PASS |
| `wheelchair_yes_steps` | ACCESSIBILITY_CONFLICT | ACCESSIBILITY_CONFLICT | BLOCK | BLOCK → PASS |
| `wheelchair_no` | ACCESSIBILITY_CONFLICT | ACCESSIBILITY_CONFLICT | BLOCK | BLOCK → PASS |
| `kerb_only` | ACCESSIBILITY_UNVERIFIED | ACCESSIBILITY_UNVERIFIED | BLOCK | BLOCK → PASS |
| `tactile_only` | ACCESSIBILITY_UNVERIFIED | ACCESSIBILITY_UNVERIFIED | BLOCK | BLOCK → PASS |
| `empty` | NEEDS_LIVE_EVIDENCE | NEEDS_LIVE_EVIDENCE | BLOCK | BLOCK → PASS |
| `toilet_plus_ramp_plus_wheelchair_yes` | ACCESSIBILITY_UNVERIFIED | ACCESSIBILITY_UNVERIFIED | BLOCK | ALLOW → **FAIL** |
| `list_value_wheelchair` | NEEDS_LIVE_EVIDENCE | ACCESSIBILITY_UNVERIFIED | BLOCK | BLOCK → PASS (evidence lost) |
| `tuple_value_ramp` | ACCESSIBILITY_UNVERIFIED | ACCESSIBILITY_UNVERIFIED | BLOCK | BLOCK → PASS |

The `gate_direct` step reaches the same verdicts by calling
`feasibility._accessibility_metadata()` / `_capability_failure_for_record()` directly, so
the result does not depend on the planner or the HTTP layer. **Two independent measurement
paths agree.**

> Harness note: an earlier run reported `HTTP 500` for *every* `generate` call. That was a
> defect in this probe (it replaced `place.metadata_json` wholesale, destroying the demo
> seed the planner needs), **not** an EAC defect. The probe now merges only the `tags`
> sub-key. The 500 was diagnosed before any conclusion was drawn from it.

---

## 4. `overall_state` cross-subject / cross-code propagation — the brief's suspicion is confirmed

The brief asked specifically whether "generic `overall_state` wrongly propagates evidence
across subject/code". It does, in both directions:

**Propagates too much (unsafe).** A `TOILET`- or `ENTRANCE`-scoped `VERIFIED` fact becomes
the place-level state and satisfies `STEP_FREE_REQUIRED` (§2.1, §3).

**Propagates too little (over-blocks).** Any `VERTICAL_ACCESS`/`KERB`/`ROUTE` partial fact
poisons a genuine `PLACE`-level verification (§2.2).

Additionally, the **two consumers of the same place disagree**. `evidence/eac_live.json`
→ `consumer_divergence`: 9 shapes, 6 divergent, **3 divergent in the dangerous direction**.

| Shape | Read endpoint (`/places/{id}/accessibility-evidence`) | Gate | Dangerous? |
|---|---|---|---|
| `demo_baseline` | NEEDS_LIVE_EVIDENCE | ACCESSIBILITY_UNVERIFIED | labels disagree |
| `frozen_evidence_status` = `{"accessibility":{"evidence_status":"ACCESSIBILITY_VERIFIED"}}` | **NEEDS_LIVE_EVIDENCE** | **ACCESSIBILITY_VERIFIED** | **YES** |
| `frozen_evidence_short` = `{"evidence_status":"VERIFIED"}` | **NEEDS_LIVE_EVIDENCE** | **ACCESSIBILITY_VERIFIED** | **YES** |
| `frozen_step_free_true` = `{"step_free":true}` | **NEEDS_LIVE_EVIDENCE** | **ACCESSIBILITY_VERIFIED** | **YES** |
| `metadata_tags_mapping` | ACCESSIBILITY_VERIFIED | ACCESSIBILITY_VERIFIED | agree |
| `metadata_tags_kv_list` | NEEDS_LIVE_EVIDENCE | NEEDS_LIVE_EVIDENCE | agree (both drop) |
| `tags_json_kv_list` = `place.tags_json=["wheelchair=yes"]` | **ACCESSIBILITY_VERIFIED** | **NEEDS_LIVE_EVIDENCE** | reverse |
| `tags_json_mapping` = `place.tags_json={"wheelchair":"yes"}` | **ACCESSIBILITY_VERIFIED** | **NEEDS_LIVE_EVIDENCE** | reverse |
| `both_toilet_and_frozen` | ACCESSIBILITY_VERIFIED | ACCESSIBILITY_VERIFIED | agree (leak) |

Three consequences:

1. **`{"accessibility": {"evidence_status": "ACCESSIBILITY_VERIFIED"}}` is the documented
   frozen-evidence shape** — it is in the gate's own key set (`evidence_status`, `status`,
   `step_free`, `wheelchair_access`, `stairs`, …). The read endpoint ignores it entirely, so
   the product shows "we don't know" while the gate plans as if step-free were confirmed.
2. **`place.tags_json` is a real column on `Place`** (models.py:468). The read endpoint
   parses it; `_accessibility_metadata()` never looks at it. So a place with
   `tags_json=["wheelchair=yes"]` is reported **ACCESSIBILITY_VERIFIED** to the user and
   simultaneously **blocked** by the gate. The user is told the place is accessible and then
   told no plan is possible.
3. The conservative route fact (`ROUTE_STEP_FREE`, `NEEDS_LIVE_EVIDENCE`) is appended by the
   **journey** endpoint only. `route_level` in `eac_live.json` shows the journey read
   endpoint correctly reports `NEEDS_LIVE_EVIDENCE` while `POST /plans/generate` returns
   **201** — the gate never consults it.

---

## 5. Route-level step-free — reported unknown, planned as known

| Surface | Route-level step-free |
|---|---|
| `GET /api/v1/journeys/{id}/accessibility-evidence` | `{state: NEEDS_LIVE_EVIDENCE, code: ROUTE_STEP_FREE, subject: ROUTE}`, `overall_state: NEEDS_LIVE_EVIDENCE`, `unknown_is_not_accessible: true` |
| `POST /api/v1/journeys/{id}/plans/generate` with HARD `STEP_FREE_REQUIRED`, every place `wheelchair=yes` | **201 / plans produced** — the route fact is not consulted |

So the brief's requirement — *route-level step-free with no real provider evidence must stay
unknown* — **holds in the reporting surface and fails in the planning surface.** The
contract-gap marker is decorative.

---

## 6. Verdict table

| # | Requirement from the brief | Result | Tag |
|---|---|---|---|
| 1 | `toilets:wheelchair=yes` must never satisfy `STEP_FREE_REQUIRED` | **VIOLATED** (read + gate) | `FINAL_V19`, `EAC_REFERENCE` |
| 2 | `ramp=yes` / `elevator=yes` must not prove step-free | holds | — |
| 3 | `wheelchair=yes + step_count=5` must conflict | holds | — |
| 4 | list/tuple tag forms must not be silently dropped | **VIOLATED** (2 shapes dropped, 2 garbled) | `EAC_REFERENCE`, `NEW` |
| 5 | route-level step-free must stay unknown | reporting yes, **planning no** | `EAC_REFERENCE`, `NEW` |
| 6 | generic `overall_state` must not propagate across subject/code | **VIOLATED** in both directions | `EAC_REFERENCE`, `NEW` |
| 7 | (not in brief, found) verified place blocked by unrelated partial tag | **VIOLATED** | `EAC_REFERENCE`, `NEW` |
| 8 | (not in brief, found) read endpoint and gate disagree about the same place | **VIOLATED**, 6/9 shapes | `EAC_REFERENCE`, `NEW` |

## 7. Recommended fix (not applied — main tree untouched)

Subject/code-scoped aggregation, then a step-free-specific projection:

```python
STEP_FREE_FACT_CODES = {"WHEELCHAIR_ACCESS", "ENTRANCE_STEP_FREE"}

def step_free_state(facts) -> str:
    relevant = [f for f in facts if f.code in STEP_FREE_FACT_CODES]
    if not relevant:
        return "NEEDS_LIVE_EVIDENCE"          # a toilet tag proves nothing about the route
    if any(f.state == "ACCESSIBILITY_CONFLICT" for f in relevant):
        return "ACCESSIBILITY_CONFLICT"
    if any(f.state != "ACCESSIBILITY_VERIFIED" for f in relevant):
        return "ACCESSIBILITY_UNVERIFIED"
    return "ACCESSIBILITY_VERIFIED"
```

Plus: normalize scalar-or-sequence tag values before matching; never let a
`VERTICAL_ACCESS`/`KERB`/`ROUTE` fact downgrade a `PLACE`-scoped verification; and make
`_accessibility_metadata()` read `place.tags_json` so both consumers see the same tags.

---

# ADDENDUM — `CODEX_V19_1_IF_AVAILABLE` (Snapshot C, taken 2026-09-15 13:47:07)

Codex V19.1 landed in the main tree after Snapshot B. This section re-runs the
same brief-mandated demands against **Snapshot C**, and — critically — against
Codex's *own* provider-evidence implementation rather than the EAC reference one.

The EAC-aware brief said to **validate the EAC patch, not trust the EAC report**.
The measurement below shows why: the EAC reference implementation **fails the
very demand the brief names**, while Codex V19.1's independent implementation
**passes it**. The report was describing a design that the code does not deliver.

## A1. The demand-by-demand verdict

| Brief demand | EAC reference | FINAL_V19 (B) | **Codex V19.1 (C)** |
|---|---|---|---|
| `toilets:wheelchair=yes` must NOT satisfy `STEP_FREE_REQUIRED` | **FAIL** — promoted to `ACCESSIBILITY_VERIFIED` (`subject: TOILET`, `code: ACCESSIBLE_TOILET`) | FAIL (no subject concept at all) | **PASS** — `ACCESSIBILITY_UNVERIFIED` |
| `ramp=yes` must NOT prove step-free | PASS (unverified) | FAIL | **PASS** |
| `elevator=yes` must NOT prove step-free | PASS (unverified) | FAIL | **PASS** |
| `wheelchair=yes + step_count=5` must be CONFLICT | PASS (`CONFLICTING_TAGS`) | FAIL | **FAIL** — `ACCESSIBILITY_UNVERIFIED` |
| list/tuple tag forms must not be silently dropped | **FAIL** (2 of 2 dropped) | FAIL | **FAIL** — 4 of 7 forms dropped |
| route-level step-free with no route evidence must stay unknown | PASS | FAIL | **PASS** — `NEEDS_LIVE_EVIDENCE` |
| generic `overall_state` must not propagate across subject/code | **FAIL** — leaks (see §4) | FAIL | **PASS** — no leak |

## A2. Why EAC fails the toilet demand

The EAC reference has **two** layers and only the inner one is scoped:

```python
# EAC lab/runtime/backend/app/integrations/accessibility/osm.py
def overall_accessibility_state(facts):
    # aggregates EVERY fact, ignoring subject and code
    ...

# EAC lab/runtime/backend/app/replanning/feasibility.py:268-280
evidence_status = overall_accessibility_state(facts)      # <-- the leak
state = accessibility_state({"evidence_status": evidence_status})
```

`toilets:wheelchair=yes` produces a fact whose `state` is `ACCESSIBILITY_VERIFIED`.
`overall_accessibility_state` folds it into `ACCESSIBILITY_VERIFIED` without
checking that the fact's `subject` is `TOILET` or its `code` is
`ACCESSIBLE_TOILET`, and `accessibility_state()` then reads only that aggregate
string. Measured:

```
[FAIL] toilet_only  overall=ACCESSIBILITY_VERIFIED subjects=['TOILET'] codes=['ACCESSIBLE_TOILET'] leak=True
```

So EAC's own report row — "`toilets:wheelchair=yes` → `ACCESSIBILITY_VERIFIED` /
`TOILET` — scoped to the facility, not the route" — is true of the *fact* and
false of the *decision*. The `subject` field is recorded but never consulted.
This is exactly the `generic overall_state` failure mode the brief told us to look
for, and it is present in the reference implementation.

## A3. Why Codex V19.1 passes it

Codex V19.1 replaced the generic call with a per-requirement evaluator:

```python
# snapshot_c/backend/app/replanning/feasibility.py:286
state = evaluate_accessibility_requirement(code, metadata or {})
```

```python
# snapshot_c/backend/app/capabilities.py:454
def evaluate_accessibility_requirement(code: str, facts: Any) -> str:
    """Evaluate only evidence that is about the requested requirement."""
```

The demand is now answered *per capability code*, so a `TOILET` fact cannot reach
`STEP_FREE_REQUIRED`. The old grep-based assertion
`test_v19_char_d6c_gate_consults_accessibility_evidence` fails only because it
pinned the literal spelling `accessibility_state(` — classified `STALE_TEST`, not a
regression.

## A4. Residual defects in Codex V19.1 (still to fix)

Full evidence: `evidence/codex_v19_1_evidence.json` (30-case matrix, 60 nested
variants, 88 gate projections, 4 route cases).

### A4.1 `step_count` / `steps` / `highway=steps` are invisible → no CONFLICT

`evaluate_accessibility_requirement` detects stairs only via
`truth("stairs", "has_stairs")`. It never reads `step_count`, `steps` or
`highway=steps`:

| tags | C: `STEP_FREE_REQUIRED` | expected |
|---|---|---|
| `{wheelchair: yes, step_count: 5}` | `ACCESSIBILITY_UNVERIFIED` | `ACCESSIBILITY_CONFLICT` |
| `{wheelchair: yes, steps: yes}` | `ACCESSIBILITY_UNVERIFIED` | `ACCESSIBILITY_CONFLICT` |
| `{wheelchair: yes, highway: steps}` | `ACCESSIBILITY_UNVERIFIED` | `ACCESSIBILITY_CONFLICT` |
| `{wheelchair: yes, stairs: yes}` | `ACCESSIBILITY_CONFLICT` ✅ | `ACCESSIBILITY_CONFLICT` |

Direction of harm: the journey is still blocked (because `UNVERIFIED` is a
blocker), so this is **not** a fail-open. But the block is reported for the wrong
reason, and a numeric contradiction in provider data — `wheelchair=yes` beside
`step_count=5` — is exactly the signal an operator most needs to see. `step_count`
must be read and any positive value must force `CONFLICT`.

### A4.2 list/tuple used as a mapping *value* is silently dropped

```python
# snapshot_c/backend/app/capabilities.py:439
if isinstance(value, Mapping):
    return {str(k).strip().lower(): str(v).strip().lower() for k, v in value.items()}
```

`str(v)` on a sequence produces junk:

| tags | resolved | verdict |
|---|---|---|
| `{wheelchair: ["yes"]}` | `{wheelchair: "['yes']"}` | **dropped** |
| `{ramp: ("yes",)}` | `{ramp: "('yes',)"}` | **dropped** |
| `{step_count: [5]}` | `{step_count: "[5]"}` | **dropped** |
| `{toilets:wheelchair: ["yes"]}` | `{toilets:wheelchair: "['yes']"}` | **dropped** |
| `["wheelchair=yes", "ramp=yes"]` | `{wheelchair: "yes", ramp: "yes"}` | ✅ |
| `{tags: {"wheelchair": "yes"}}` | `{wheelchair: "yes"}` | ✅ |
| `{tags: ["wheelchair=yes"]}` | `{wheelchair: "yes"}` | ✅ |

So the **sequence** and **nested** forms are handled; only the value position is
lossy. The brief's demand is half met. Fix: in the `Mapping` branch, unwrap a
list/tuple value (take the first scalar, or join with `;`) before `str()`.

### A4.3 `step_free_verified` at metadata top level is dropped

`_accessibility_metadata` (feasibility.py:262–277) whitelists
`evidence_status, status, step_free, wheelchair_access, stairs, stroller_accessible,
luggage_accessible` and then reads `osm_tags` / `tags`. `step_free_verified` is one
key short:

| metadata shape | C: `STEP_FREE_REQUIRED` |
|---|---|
| `{step_free_verified: yes}` (top level) | `ACCESSIBILITY_UNVERIFIED` ❌ (projection is `None`, gate blocks) |
| `{step_free_verified: yes}` under `osm_tags` | `ACCESSIBILITY_VERIFIED` ✅ |
| `{step_free_verified: yes}` under `tags` | `ACCESSIBILITY_VERIFIED` ✅ |
| `{step_free: yes}` (top level) | `ACCESSIBILITY_VERIFIED` ✅ |

Same assertion, different nesting, opposite answer.

### A4.4 The EAC reference drops list values too

For completeness, the reference implementation has the same gap — so a fix here
should not be described as "restore EAC behaviour":

```
[FAIL] list_value_wheelchair  overall=NEEDS_LIVE_EVIDENCE subjects=[] codes=[] dropped=True
[FAIL] list_value_toilets     overall=NEEDS_LIVE_EVIDENCE subjects=[] codes=[] dropped=True
```

## A5. Route-level: EAC vs Codex

| case | EAC | Codex V19.1 |
|---|---|---|
| route, no evidence | `NEEDS_LIVE_EVIDENCE` ✅ | `NEEDS_LIVE_EVIDENCE` ✅ |
| route + place `wheelchair=yes` | promoted (leak) ❌ | `NEEDS_LIVE_EVIDENCE` ✅ |
| route + place `step_free=yes` | promoted ❌ | `NEEDS_LIVE_EVIDENCE` ✅ |
| route + explicit `route_step_free=yes` | `ACCESSIBILITY_VERIFIED` ✅ | `ACCESSIBILITY_VERIFIED` ✅ |

Codex V19.1 is the only one of the three that keeps a route-level step-free
requirement unknown without route evidence **and** honours an explicit route
assertion.

## A6. Sentence replay — all four trees

Evidence: `evidence/accessibility_evidence_scope.json`, field `sentences`.

| sentence | EAC | FINAL_V19 (B) | Codex V19.1 (C) |
|---|---|---|---|
| `轮椅必须全程无障碍，没有例外` | `STEP_FREE_REQUIRED` ✅ | `[]` ❌ | `STEP_FREE_REQUIRED` ✅ |
| `我以前不用轮椅，但现在必须无障碍` | `STEP_FREE_REQUIRED` ✅ | `[]` ❌ | `STEP_FREE_REQUIRED` ✅ |
| `我没有过敏，但我用轮椅，必须全程无障碍` | `STEP_FREE_REQUIRED` ✅ | `[]` ❌ | `STEP_FREE_REQUIRED` ✅ |
| `过去我坐轮椅，现在必须全程无障碍` | `STEP_FREE_REQUIRED` ✅ | `[]` ❌ | `STEP_FREE_REQUIRED` ✅ |
| `不是地铁，我需要出租车因为行李很多` | `LARGE_LUGGAGE` ✅ | `[]` ❌ | `[]` ❌ |
| `不需要人扶，但我坐轮椅，必须全程无障碍` | `STEP_FREE_REQUIRED` ✅ | `[]` ❌ | `STEP_FREE_REQUIRED` ✅ |
| **`I don't need a wheelchair, I can walk`** | **`STEP_FREE_REQUIRED` ❌** | **`STEP_FREE_REQUIRED` ❌** | **`[]` ✅** |
| **`朋友说我可能需要轮椅，但我不这么认为`** | **`STEP_FREE_REQUIRED` ❌** | **`STEP_FREE_REQUIRED` ❌** | **`[]` ✅** |

The two mandated sentences are fixed **only** in Codex V19.1. One regression
remains: `不是地铁，我需要出租车因为行李很多` now loses `LARGE_LUGGAGE` on C
(see `CODEX_V19_1_DELTA_RESULTS.md` §2).
