# CAPABILITY_CANONICALIZATION_RESULTS.md

**Subject:** `app/capabilities.py::canonicalize_capabilities()` and the merge performed by
`app/integrations/ai/semantic_compiler.py`
**Evidence:** `evidence/canonicalization_a.json`, `evidence/canonicalization_b.json`,
`evidence/hardpairs.jsonl`, `evidence/eac_differential.jsonl`, `evidence/eac_live.json`
**Probes:** `tools/v191_probe_canonicalization.py`, `tools/v191_run_semantic_live.py`,
`tools/v191_eac_differential.py`
**Labels:** `FINAL_V19` / `CODEX_V19_1_IF_AVAILABLE` are the same file
(`app/capabilities.py` sha16 `7e3ff4cb3a85b7b6`, byte-identical in Snapshots A and B);
`EAC_REFERENCE` is the EAC patch.

---

## 1. Signature and shape contract

```python
def canonicalize_capabilities(candidates, *, source="SEMANTIC",
                              provenance="USER_STATED", scope="JOURNEY",
                              explicit=None, confirmed=False) -> list[dict]
```

Returns a **`list`**, not a tuple (`EAC_REFERENCE` returns a `tuple`). A test written against
the wrong assumption fails spuriously; this round's own guard
(`test_v191_guard_unknown_capability_code_is_dropped`) had to be corrected from `== ()` to
`== []`. Worth pinning in the contract.

Unknown codes are **dropped silently** — `if code not in CAPABILITY_CODES: continue` — with no
counter, no warning and no audit row.

---

## 2. `FINAL_V19` — the two canonicalization defects

### 2.1 A HARD accessibility need can be downgraded through the public API

`D1` was the brief's first focus item. Measured at Snapshot A and unchanged at Snapshot B:

```
POST /api/v1/journeys/{id}/capabilities/confirm
     [{"code":"STEP_FREE_REQUIRED","severity":"STRONG"}]
  -> 200
     persisted: severity="STRONG", capability_class="HARD_ACCESSIBILITY_NEED"
POST /api/v1/journeys/{id}/plans/generate -> 201 / 3 plans
     audit: traveler.capability.created + traveler.capability.updated
```

The **class** stays `HARD_ACCESSIBILITY_NEED`, but the **gate keys on severity**, so a
`STRONG` step-free requirement no longer blocks. 18 of 24 probe cells accept a downgrade;
omitting `severity` entirely yields `STRONG` via
`default_severity(code, hard_asserted=False)`.

This is the guard the previous round described as "a tautology", and it is **still
reproducible**: `D1 → 19 STILL_REPRODUCIBLE / 2 FIXED_IN_CURRENT`.

### 2.2 No dedupe — the same code is stored twice

`D3 → 8 STILL_REPRODUCIBLE / 0 FIXED`. `canonicalize_capabilities` in `FINAL_V19` builds a
list with no keyed merge, so duplicates survive to persistence. Live measurements
(`evidence/hardpairs.jsonl`):

- **5 merged rows carry a duplicate code**
- **1 row carries the same code in two different severities**

Concrete case: `wheelchair, must be step-free` merges to **two identical
`STEP_FREE_REQUIRED` HARD rows**, because the model's item and the local backstop's item have
different `params` and nothing dedupes them.

---

## 3. The model/server vocabulary mismatch is the largest single loss

From the live 120-case run, comparing what the model emitted against what survived
canonicalization:

| Measure | Value |
|---|---|
| Rows where the model emitted at least one capability | ~103 |
| Rows where a **model** capability survived canonicalization | **5** |
| Model capabilities **silently dropped** | **98** |
| Distinct invented codes the server refused | **48** |

Most frequent refused codes:

| Code the model invented | Count |
|---|---|
| `MAX_WALKING_DISTANCE` | 15 |
| `MOBILITY_WHEELCHAIR` | 11 |
| `STEP_FREE_ACCESS` | 10 |
| `MOBILITY_LIMITED_WALKING` | 6 |
| `STEP_FREE` | 4 |
| `WHEELCHAIR_ACCESSIBLE` | 4 |
| `LUGGAGE_LARGE` | 4 |
| `NO_STAIRS` | 4 |
| … 40 more distinct | |

Meanwhile the deterministic server-side extractor
(`extract_capabilities_from_text`) supplied a capability on **63** rows the model had said
nothing about.

**Net:** 63 cases carry a capability, 36 of them HARD. So the merge is lossy in one direction
(98 model items discarded without a trace) and one-sided in the other (the server backstop
carries the load). `semantic_compiler.py:167-190` documents the intent *"a model omission
must not erase a user-stated hard need"* — the measured behaviour shows the converse is also
untrue: a model **assertion** is routinely erased, and nothing records it.

There is **no count check** in `SemanticEnvelope.from_mapping`, so the envelope validates
while 98 capabilities vanish.

---

## 4. `EAC_REFERENCE` — canonicalization improved, with two new defects

### 4.1 FIXED: HARD cannot be downgraded

```python
if code in HARD_ACCESSIBILITY_CODES:
    klass = capability_class_for(code)
    if bool(params.get("needs_confirmation")):
        severity = "STRONG"
    else:
        severity = "HARD"        # a model/client cannot downgrade it
```

Measured: `severity: "SOFT"` in → `severity: "HARD"` out. **`D1` FIXED in EAC.**

### 4.2 FIXED: duplicates merged

`merged: dict[str, CapabilityItem]` keyed by code, strongest severity wins.
`evidence/eac_differential_summary.json` → `canonical_duplicates = 0` across 182 cases.
**`D3` FIXED in EAC.**

### 4.3 NEW: the dedup key ignores `scope` — cross-scope collapse and param contamination

```python
canonicalize_capabilities([
  {"code":"AVOID_STAIRS","severity":"HARD","scope":"TRAVELER","params":{"note":"traveler"}},
  {"code":"AVOID_STAIRS","severity":"HARD","scope":"JOURNEY", "params":{"note":"journey"}},
])
# -> [{"code":"AVOID_STAIRS","severity":"HARD","scope":"TRAVELER",
#      "params":{"note":"journey"}}]          # ONE row, JOURNEY scope lost
```

A permanent traveller-level need and a this-trip need collapse into one row carrying the
wrong scope and the other row's parameters. The brief's item 3 (`Traveler + Journey same
code`) is **violated on the compiler path**.

The database layer is correct — `traveler_capabilities` is `UNIQUE(traveler_id, journey_id,
scope, code)` and the live test stores **2 rows** (`cross_scope_row_count: 2`, one
`TRAVELER`/`journey_id: null` with `params={"note":"traveler"}`, one `JOURNEY` with
`params={"note":"journey"}`). So the defect exists only where the model's output is
canonicalized — i.e. on the path a real sentence takes.

### 4.4 NEW: duplicate merge weakens numeric constraints

```python
canonicalize_capabilities([
  {"code":"MAX_WALKING_PER_LEG_M","severity":"HARD","params":{"max_m":400}},
  {"code":"MAX_WALKING_PER_LEG_M","severity":"HARD","params":{"max_m":800}},
])
# -> params={"max_m": 800}      # the LOOSER limit wins
```

`merged_params = {**existing.params, **item.params}` lets the **later** value win, so
restating a physical limit more loosely silently relaxes it and the stricter statement is
discarded. For a walking limit this is safety-relevant.

---

## 5. Side-by-side

| Property | `FINAL_V19` / `CODEX_V19_1` | `EAC_REFERENCE` |
|---|---|---|
| Return type | `list` | `tuple` |
| Unknown code | dropped silently | dropped silently |
| HARD code forced to HARD | **no** — `STRONG` accepted | **yes** |
| Dedupe | **none** | by `code` only |
| Dedupe respects `scope` | n/a | **no** — collapses scopes |
| Dedupe preserves strictest numeric limit | n/a | **no** — looser wins |
| Duplicates in 182-case corpus | 0 at extractor level | 0 |
| Duplicates on the live merge path | **4–5 rows** | not measured (EAC lab merge path differs) |
| `needs_confirmation` escape hatch | implicit via `severity` | explicit via `params` |

---

## 6. Verdict table

| # | Finding | `FINAL_V19` | `EAC_REFERENCE` | Tag |
|---|---|---|---|---|
| 1 | HARD accessibility need cannot be downgraded | **VIOLATED** | **FIXED** | `FINAL_V19`, `EAC_REFERENCE` |
| 2 | Duplicate codes are merged | **VIOLATED** (8/8) | **FIXED** | `FINAL_V19`, `EAC_REFERENCE` |
| 3 | Unknown codes are dropped silently (no counter) | VIOLATED | VIOLATED | `FINAL_V19`, `EAC_REFERENCE` |
| 4 | Model vocabulary survives canonicalization | **VIOLATED** (5/103) | not measured | `FINAL_V19` |
| 5 | Dedupe respects `scope` | n/a | **VIOLATED** | `NEW` |
| 6 | Dedupe preserves the strictest limit | n/a | **VIOLATED** | `NEW` |
| 7 | `canonicalize_capabilities` return type is stable | `list` | `tuple` | `NEW` |

## 7. Recommendation (not applied — main tree untouched)

1. Key the merge by `(scope, code)`, not `code`.
2. Merge numeric params with `min()` for upper bounds (and `max()` for lower bounds) instead
   of last-writer-wins.
3. Force `severity="HARD"` for `HARD_ACCESSIBILITY_CODES` in `FINAL_V19` as EAC does — this is
   a small, well-scoped change that closes `D1` outright.
4. Return a structured result `(items, dropped)` and record dropped codes in the audit log so
   the 98 silent losses become observable.
5. Pin the return type (`list`) in the contract test.
