# Capability Semantics — V19.2

Evidence: `evidence/capability_semantics_a.json`, `evidence/p0_numeric_a.json`,
`evidence/corpus_delta_c_to_a.json`, `evidence/lifecycle_a.json`.

`capabilities.py` is byte-identical in Snapshot A and B (`23668 B`, sha16 `9b68b17997f4cf4e`),
so every row below holds for both snapshots.

---

## 1. Residual false-HARD — **FIXED (9/9)**

The nine sentences V19.1 still turned into a HARD `STEP_FREE_REQUIRED` are all clean now:

| Sentence | V19.1 (C) | V19.2 (A) |
|---|---|---|
| `my friend needs a wheelchair, not me` | HARD | ✅ nothing |
| `my mother uses a wheelchair` | HARD | ✅ nothing |
| `我朋友需要轮椅` | HARD | ✅ nothing |
| `我妈妈坐轮椅` | HARD | ✅ nothing |
| `I am not a wheelchair user` | HARD | ✅ nothing |
| `the station has an accessible toilet` | HARD | ✅ nothing |
| `车站有无障碍厕所` | HARD | ✅ nothing |
| `说不定到时候我需要轮椅` | HARD | ✅ nothing |
| `if I end up in a wheelchair I'll tell you` | HARD | ✅ nothing |

The two mandated sentences still produce a real hard need (`G1_mandated_guard 2/2`), so the fix
did not simply disable extraction.

Corpus confirmation (`evidence/corpus_delta_c_to_a.json`, 120 cases): `A_REMOVES_HARD ×2`,
`denial_vs_need` bucket clean, and the V19.1 `我朋友需要轮椅，不是我` false-HARD is gone.

## 2. Over-filtering — **NEW REGRESSION (3 cases), plus 4 inherited**

The fix overshot. `_SPECULATIVE_MARKERS` contains `如果`, `if `, `maybe`, `might`, and
`_THIRD_PARTY_MARKERS` contains `我妈妈` / `我父亲`; a clause containing any of them is dropped
**whole**. Measured (`evidence/p0_numeric_a.json` → `n4_filtering`), 7 of 8 probe sentences now
produce **nothing at all**:

| Sentence | FINAL_V19 (B) | V19.1 (C) | V19.2 (A) | Label |
|---|---|---|---|---|
| `if possible I need step-free access` | HARD | HARD | **nothing** | **REGRESSED** |
| `我妈妈要午休` | STRONG | STRONG | **nothing** | **REGRESSED** |
| `如果能推婴儿车就方便多了` | STRONG | STRONG | **nothing** | **REGRESSED** |
| `如果可能的话我需要无障碍通道` | HARD | nothing | nothing | STILL_REPRODUCIBLE |
| `我可能需要轮椅` | HARD | nothing | nothing | STILL_REPRODUCIBLE |
| `maybe I need a wheelchair` | HARD | nothing | nothing | STILL_REPRODUCIBLE |
| `我父亲走不了远路` | nothing | nothing | nothing | STILL_REPRODUCIBLE |
| `我朋友需要轮椅，不是我` | nothing | HARD | nothing | **FIXED** |

Corpus confirmation: `hard_vs_soft-0052` `如果能推婴儿车就方便多了` → V19.1 `STROLLER STRONG`,
V19.2 **empty**. `duplicate_multi-0107` `我父亲走不了远路，我妈妈要午休，宝宝要睡午觉` →
V19.1 `MIDDAY_REST_WINDOW`, V19.2 **empty** (the corpus expects three distinct codes).

### Why this matters more than the false positives

A false HARD blocks a trip that could have run. A **dropped need** lets the planner route a
traveller who cannot use stairs up a staircase, and the UI shows nothing wrong. On a real phone
in a real city that is the dangerous direction. `if possible I need step-free access` and
`我可能需要轮椅` are exactly what a real traveller types.

### Root causes, precisely

- `_SPECULATIVE_MARKERS` treats `如果` / `if ` / `maybe` as a reason to discard the **whole
  clause**, even when the clause states a first-person requirement. A hedged need should become
  `STRONG` + `needs_confirmation`, not disappear.
- `_THIRD_PARTY_MARKERS` cannot distinguish *"a third party who is not travelling"*
  (`我朋友需要轮椅，不是我` — correctly empty) from *"a companion who is travelling"*
  (`我妈妈要午休` — a real journey constraint that is now lost).
- `_NEGATED_MARKERS` contains `可能` / `也许`, so `我可能需要轮椅` is treated as a denial.

## 3. Scope-aware canonicalization — **FIXED**

The V19.1 regression (dedup keyed on `code` alone) is closed. `canonicalize_capabilities` now
uses `merge_key = (payload.get("scope"), code)` (line 390).

| Check | Result |
|---|---|
| TRAVELER + JOURNEY, same code, both survive | ✅ 2 rows, each with its own params |
| Journey params not silently dropped | ✅ |
| Same-scope duplicates merge to the stricter bound | ✅ 400 beats 800 |
| Permanent language → TRAVELER | ✅ `我终身需要无障碍设施，一直如此` → TRAVELER |
| This-trip language → JOURNEY | ✅ `这次旅行我需要无障碍通道` → JOURNEY |

Corpus: `scope_permanence-0091` `我终身不能走楼梯，这是永久性的` → V19.1 `JOURNEY`,
V19.2 **`TRAVELER`** ✅.

## 4. Provider evidence scope

### Facility tags — **PASS (12/12)**

None of `toilets:wheelchair=yes`, `ramp=yes`, `elevator=yes`, `ramp:wheelchair=yes`,
`highway=elevator`, `kerb=lowered`, `tactile_paving=yes`, `entrance=yes`, `wheelchair=yes`,
`wheelchair=designated`, `wheelchair=limited`, `wheelchair=no` satisfies
`STEP_FREE_REQUIRED`. The V19.1 leak (aggregate state across subjects) is closed.

### Route-level — **PASS (2/2)**

`{"subject": "route"}` and `{"subject": "route", "osm_tags": {"wheelchair": "yes"}}` both →
`NEEDS_LIVE_EVIDENCE`. No leakage from place evidence into route evidence.

### Positive assertions — **PASS (4/4)**

`step_free: yes`, `step_free_verified: yes` (flat), `{"osm_tags": {"step_free_verified": "yes"}}`,
`route_step_free_verified` → all `ACCESSIBILITY_VERIFIED`.

### Tag container shapes — **PASS (5/5)**

`{"wheelchair": ["yes"]}` → `{"wheelchair": "yes"}`; `{"ramp": ("yes",)}` → `{"ramp": "yes"}`;
`["wheelchair=yes", "ramp=yes"]` → both keys. The V19.1 `str(["yes"])` loss is closed.

### Contradictions — **FAIL (5/7)**

| Facts | Expected | Actual |
|---|---|---|
| `{"wheelchair": "yes", "stairs": "yes"}` | CONFLICT | ✅ CONFLICT |
| `{"wheelchair": "yes", "has_stairs": "yes"}` | CONFLICT | ✅ CONFLICT |
| `{"wheelchair": "yes", "step_count": "5"}` (flat) | CONFLICT | ✅ CONFLICT |
| `{"wheelchair": "yes", "highway": "steps"}` (flat) | CONFLICT | ✅ CONFLICT |
| `{"osm_tags": {"wheelchair": "yes", "highway": "steps"}}` | CONFLICT | ✅ CONFLICT |
| `{"osm_tags": {"wheelchair": "yes", "step_count": "5"}}` | CONFLICT | ❌ **UNVERIFIED** |
| `{"wheelchair": "yes", "steps": "yes"}` | CONFLICT | ❌ **UNVERIFIED** |

`evaluate_accessibility_requirement` reads the stair count from the **top-level** facts only:

```python
step_count = facts.get("step_count", facts.get("steps"))
```

When the tags arrive nested under `osm_tags` (the normal provider shape) `facts.get(...)` is
`None`, so `many_steps` is `False` and the contradiction is folded into the generic UNVERIFIED
bucket. `steps: "yes"` fails for a different reason — `int("yes")` raises and is swallowed.

### The `evidence_status` signal is ignored — **FAIL**

`{"evidence_status": "VERIFIED"}` → **`ACCESSIBILITY_UNVERIFIED`**, so `generate` returns
**422 / 0 plans** (`evidence/lifecycle_a.json` → `capability_evidence_verified_string`), while
`{"step_free": true}` → 201 / 3 plans.

`_accessibility_metadata` *does* whitelist `evidence_status`, so the value reaches
`evaluate_accessibility_requirement` — which never looks at it. Only the older
`accessibility_state()` reads that key. The canonical provider signal for "this place is
verified accessible" is therefore discarded, and fail-closed policy blocks the trip.

This is **not** a V19.2 regression: snapshot C fails identically. Label: **STILL_REPRODUCIBLE**.

### Top-level `step_free_verified` is dropped — **FAIL**

`_accessibility_metadata`'s whitelist is `{evidence_status, status, step_free, wheelchair_access,
stairs, stroller_accessible, luggage_accessible}`. A place whose metadata carries a flat
`step_free_verified: yes` loses it, while the same value nested under `osm_tags` survives.
focused suite: `test_v191_eac_defect_top_level_step_free_verified_is_seen` **FAILS**.
This is precisely the half of `V19_2_VERIFIED_STARTER.patch` that Codex did **not** merge.

## 5. Hermes / agent capability context

`evidence/lifecycle_a.json` → `hermes`: `any_capability_tool: false`,
`hermes_capabilities_endpoint: 200`. No capability **write** tool is exposed to the agent; the
read-only capability context the V19.1 round established is preserved. ✅

## 6. Projection transparency — **gap**

`evidence/lifecycle_a.json` → `projection`: a confirmed HARD `STEP_FREE_REQUIRED` appears in
`traveler_capabilities` rows but **not** in `capability_in_constraint_api` or
`capability_in_constraint_table` (both `[]`), and `journey_constraints_before == after == 3`.
The gate does act on it (generate fails closed), but nothing in the constraint surface shows the
traveller which requirement is blocking them.

---

## Exact reproduction

```
cd D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915
python tools/v192_probe_capability_semantics.py a
python tools/v192_probe_p0_numeric.py a
python tools/v192_corpus_delta.py
```

## Recommended order for Codex

1. **Stop dropping first-person hedged needs.** Split `_SPECULATIVE_MARKERS` into "the statement
   is about a possible future" (keep as STRONG + `needs_confirmation`) and "the statement is not
   about the traveller" (discard). At minimum, if the clause contains a first-person marker and a
   capability token, keep it.
2. **Distinguish companion from non-travelling third party.** A companion need is a JOURNEY
   constraint; only a denial (`不是我`, `not me`) should discard.
3. **Read stair evidence from `tags`, not `facts`** — use `tags.get("step_count")` as a fallback,
   and treat `steps in {"yes","true","1"}` as a stair signal.
4. **Honour `evidence_status` in `evaluate_accessibility_requirement`** — map `VERIFIED` →
   `ACCESSIBILITY_VERIFIED`, `CONFLICT`/`INACCESSIBLE` → `ACCESSIBILITY_CONFLICT`.
5. **Add the `feasibility.py` whitelist keys** (`step_free_verified`, `route_step_free`,
   `route_step_free_verified`, `has_stairs`, `step_count`, `steps`, `highway`).
6. **Project HARD capabilities into the constraint surface** so the traveller can see what is
   blocking them.
