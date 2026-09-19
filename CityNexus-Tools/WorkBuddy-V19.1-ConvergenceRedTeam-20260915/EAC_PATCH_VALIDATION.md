# EAC_PATCH_VALIDATION.md

**Round:** CityNexus WorkBuddy V19.1 Convergence Red-Team — EAC-Aware Update
**Method:** the EAC reference implementation was **executed**, not read. Two probes:

- `tools/v191_probe_accessibility_evidence.py` — loads `lab/runtime/backend/app/capabilities.py`
  and `.../integrations/accessibility/osm.py` by file path and replays a corpus through both
  the EAC and the current-tree extractors (deterministic, offline).
- `tools/v191_probe_eac_live.py` — drives the EAC lab backend in-process (throwaway SQLite)
  over HTTP: confirm, generate, catalog, extract, audit, concurrency.
- `tools/v191_eac_differential.py` — **182 cases / 176 unique texts** through both extractors.

**Evidence:** `evidence/eac_differential.jsonl`, `evidence/eac_differential_summary.json`,
`evidence/accessibility_evidence_scope.json`, `evidence/eac_live.json`

**Labels:** `FINAL_V19` = current tree extractor; `CODEX_V19_1_IF_AVAILABLE` = same file
(`app/capabilities.py` is **byte-identical in Snapshot A and Snapshot B**, sha16
`7e3ff4cb3a85b7b6`, so the extractor surface answers both labels identically);
`EAC_REFERENCE` = the EAC patch.

---

## 1. Headline: the two mandated sentences are **not** fixed

The update brief states that independent review confirmed the EAC capability patch still
produces a wrong HARD need for these two sentences. **Reproduced, in both implementations:**

| Sentence | FINAL_V19 / CODEX_V19_1 | EAC_REFERENCE | Brief expectation |
|---|---|---|---|
| `I don't need a wheelchair, I can walk` | `['STEP_FREE_REQUIRED']` HARD | `['STEP_FREE_REQUIRED']` HARD | no HARD need |
| `朋友说我可能需要轮椅，但我不这么认为` | `['STEP_FREE_REQUIRED']` HARD | `['STEP_FREE_REQUIRED']` HARD | no HARD need |

Confirmed three ways: pure-function replay (`accessibility_evidence_scope.json` →
`mandated_false_hard`), the 182-case differential (`eac_differential_summary.json` →
`mandated`), and the live `/capabilities/extract` endpoint
(`eac_live.json` → `extract.false_hard_cases = ["mandated_en","mandated_zh"]`).

**EAC did not fix the false-positive direction of the negation problem.**

---

## 2. What EAC *did* fix (verified improvements)

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | A model/client cannot downgrade a HARD accessibility code | **FIXED** | `canonicalize_capabilities([{code:STEP_FREE_REQUIRED, severity:SOFT}])` → `severity: HARD`. EAC forces `severity="HARD"` for `HARD_ACCESSIBILITY_CODES` unless `params["needs_confirmation"]`. |
| 2 | Duplicate capability codes are merged | **FIXED** | `merged: dict[str, CapabilityItem]` keyed by code; `eac_differential_summary.canonical_duplicates = 0` across 182 cases (was 8 STILL_REPRODUCIBLE assertions in the previous round). |
| 3 | Clause-local negation / history | **FIXED (partly)** | EAC added `_split_clauses()` + `_extract_from_clause()`. 6 cases where FINAL_V19 erased a live need now survive — see §3. |
| 4 | Numeric walking limits are parsed | **FIXED** | 16 walking-numeric cases now produce a capability where FINAL_V19 produced none — see §4. |
| 5 | Rest / nap windows are parsed | **FIXED** | 4 cases now produce `MIDDAY_REST_WINDOW` where FINAL_V19 produced none. |
| 6 | `extract` is marked candidate-only | **FIXED** | live endpoint returns `source: "DETERMINISTIC_TEXT_FALLBACK"`, `authority: "UI_CANDIDATE_ONLY"` for all 7 cases; no persistence. |

**Net effect on the corpus:** `divergent = 32`, `eac_only = 32`, **`b_only = 0`** — EAC detects
strictly more than FINAL_V19 and never fewer. `eac_hard = 71` vs `b_hard = 64`.

---

## 3. EAC's clause-local negation fix is real — and one-sided

`_split_clauses()` recovers live needs that FINAL_V19 erased (all EAC-only, `b_only = 0`):

| Text | FINAL_V19 | EAC | Why it matters |
|---|---|---|---|
| `轮椅必须全程无障碍，没有例外` | `[]` | `STEP_FREE_REQUIRED` | a trailing `没有例外` erased the need |
| `我以前不用轮椅，但现在必须无障碍` | `[]` | `STEP_FREE_REQUIRED` | the historical clause erased the live clause |
| `过去我坐轮椅，现在必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` | same |
| `我没有过敏，但我用轮椅，必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` | an unrelated denial erased the need |
| `不需要人扶，但我坐轮椅，必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` | same |
| `不是地铁，我需要出租车因为行李很多` | `[]` | `LARGE_LUGGAGE` | scoped negation |
| `我一直坐轮椅，不是这次才需要` | `[]` | `STEP_FREE_REQUIRED` | permanence clause |

**But the opposite direction is untouched.** `_NEGATED_MARKERS` is **byte-identical** between
EAC and FINAL_V19 (verified: `eac_negated_markers == b_negated_markers`), and it contains
`没有`, `不需要`, `不用`, `无需`, `不是`, `以前`, `曾经`, `过去`, `历史` as **clause-global**
suppressors. Splitting clauses removed the *false erasure*; it did nothing about the
*false creation*. From `eac_differential.jsonl`, cases where **both** implementations emit a
HARD need:

| Bucket | Cases | Both emit HARD | Example |
|---|---|---|---|
| `denial_vs_need` | 28 | **11** | `I don't use a wheelchair`, `I am not a wheelchair user`, `no stairs problem for me, I'm fine` → `AVOID_STAIRS` |
| `hearsay` | 6 | **6** | `my friend needs a wheelchair, not me`, `我妈妈坐轮椅`, `同事说我也许需要轮椅` |
| `hypothetical` | 3 | **3** | `if I get tired I might need a wheelchair`, `maybe I should avoid stairs` |

So **~20 raw-language cases manufacture a HARD accessibility need from a denial, a third
party, or a hypothetical — identically in both implementations.** For an accessibility
product this is the more damaging failure mode: it misrepresents a person as disabled and
blocks a journey they did not ask to be blocked.

### 3.1 New: a statement about the world becomes a need of the traveller

| Text | Both implementations |
|---|---|
| `the station has an accessible toilet` | `['STEP_FREE_REQUIRED']` |
| `车站有无障碍厕所` | `['STEP_FREE_REQUIRED']` |
| `the venue has a ramp` | `[]` |
| `there is an elevator at the museum` | `[]` |
| `这里有坡道` | `[]` |

Describing a **facility** as accessible (`无障碍` / accessible) is read as the **traveller**
requiring step-free access. `无障碍` is a hard marker with no subject check. Tag: `NEW`,
present in both.

---

## 4. New: EAC's numeric parser accepts nonsense values

EAC's `_number_before()` fix works — but with **no bounds validation**:

| Text | FINAL_V19 | EAC |
|---|---|---|
| `走路不能超过 500 米` | `[]` | `MAX_WALKING_PER_LEG_M` |
| `走路不能超过 0 米` | `[]` | `MAX_WALKING_PER_LEG_M` ← **0 m** |
| `走路不能超过 1 米` | `[]` | `MAX_WALKING_PER_LEG_M` |
| `走路不能超过 499 米` | `[]` | `MAX_WALKING_PER_LEG_M` |
| `走路不能超过 -5 米` | `[]` | `MAX_WALKING_PER_LEG_M` ← **negative** |
| `走路不能超过 10000 米` | `[]` | `MAX_WALKING_PER_LEG_M` ← **10 km per leg** |
| `I cannot walk more than 500 metres per leg` | `[]` | `MAX_WALKING_PER_LEG_M` |
| `我每天走路不能超过 3000 米` | `MAX_DAILY_WALKING_M` | `MAX_DAILY_WALKING_M` **+** `MAX_WALKING_PER_LEG_M` |
| `连续走不超过 15 分钟` | `MAX_CONTINUOUS_WALKING_MIN` | `MAX_CONTINUOUS_WALKING_MIN` **+** `MAX_WALKING_PER_LEG_M` |

Two distinct defects:

1. **No range check.** `0`, `1` and `-5` metres become HARD `MAX_WALKING_PER_LEG_M`
   constraints. In FINAL_V19 these were silent no-ops; EAC converts a harmless gap into an
   **active wrong constraint** that makes the journey unplannable. `_bounded_number()`
   exists in the module but is not applied to the walking term.
2. **Over-extraction.** A daily limit and a continuous-walking limit each also emit
   `MAX_WALKING_PER_LEG_M`. FINAL_V19 emitted the correct single code.

Tag: `NEW`, `EAC_REFERENCE` only.

### 4.1 New: soft preferences become capabilities

| Text | FINAL_V19 | EAC |
|---|---|---|
| `中午能休息一下就更好了` ("it would be nice to rest at noon") | `[]` | `MIDDAY_REST_WINDOW` |
| `我最多走 500 米，尽量吧` ("at most 500 m, if possible") | `[]` | `MAX_WALKING_PER_LEG_M` |

A hedged wish now creates a `CARE_REQUIREMENT`. Severity is `STRONG` (not HARD), so it does
not hard-block, but it is persisted and reported as a care requirement. Tag: `NEW`,
`EAC_REFERENCE`.

---

## 5. `canonicalize_capabilities` — fixes plus two new defects

### 5.1 Fixed: HARD cannot be downgraded

```python
if code in HARD_ACCESSIBILITY_CODES:
    klass = capability_class_for(code)
    if bool(params.get("needs_confirmation")):
        severity = "STRONG"
    else:
        severity = "HARD"      # a model/client cannot downgrade it to SOFT
```

Measured: `severity: "SOFT"` in → `severity: "HARD"` out. This is the D1 delta target,
**FIXED in EAC**.

### 5.2 New: the dedup key ignores `scope` — cross-scope collapse and param contamination

`merged` is keyed by `code` only, and the merge is
`merged_params = {**existing.params, **item.params}`.

```python
canonicalize_capabilities([
  {"code":"AVOID_STAIRS","severity":"HARD","scope":"TRAVELER","params":{"note":"traveler"}},
  {"code":"AVOID_STAIRS","severity":"HARD","scope":"JOURNEY", "params":{"note":"journey"}},
])
# -> ONE row: scope="TRAVELER", params={"note":"journey"}
```

The JOURNEY-scoped row disappears and its params overwrite the TRAVELER row's. A permanent
traveller-level need and a this-trip need are **merged into one row with the wrong scope and
foreign parameters**.

The database itself is correct — `traveler_capabilities` has
`UNIQUE(traveler_id, journey_id, scope, code)` and the live cross-scope test stores
**2 rows** (`cross_scope_row_count: 2`, one `TRAVELER`/`journey_id: null`, one `JOURNEY`).
So the collapse happens **only on the semantic-compiler path**, where the model's items go
through `canonicalize_capabilities` — which is exactly the path a real user's sentence takes.

### 5.3 New: duplicate merge weakens numeric constraints

```python
canonicalize_capabilities([
  {"code":"MAX_WALKING_PER_LEG_M","severity":"HARD","params":{"max_m":400}},
  {"code":"MAX_WALKING_PER_LEG_M","severity":"HARD","params":{"max_m":800}},
])
# -> params={"max_m": 800}   # the LOOSER limit wins
```

Because `{**existing, **item}` lets the **later** value win, restating a limit more loosely
silently relaxes the constraint. A stricter limit stated earlier is discarded. For a
physical limit this is a safety-relevant merge. Tag: `NEW`, `EAC_REFERENCE`.

---

## 6. Confirm semantics — the brief's item 3 fails

### 6.1 `confirm A` → `confirm B` loses A

```
POST /journeys/{id}/capabilities/confirm  [{"code":"STEP_FREE_REQUIRED", severity HARD}] -> 200
POST /journeys/{id}/capabilities/confirm  [{"code":"AVOID_STAIRS",       severity HARD}] -> 200
GET  /journeys/{id}/capabilities -> ["AVOID_STAIRS"]      # STEP_FREE_REQUIRED is GONE
```

`a_survived: false`, `a_survived_after_reload: false`. **The brief's requirement — "confirm A
→ confirm B, A must not disappear" — is violated.** Cause: `_replace_capability_rows(...)`
replaces the whole JOURNEY-scope set rather than upserting, so a second confirm is a
destructive overwrite.

### 6.2 Concurrent confirm loses a capability (nondeterministically)

Three concurrent `confirm` calls (`STEP_FREE_REQUIRED`, `AVOID_STAIRS`, `LARGE_LUGGAGE`),
all returning **200**:

| Run | Surviving codes | Lost |
|---|---|---|
| 1 | `["AVOID_STAIRS","LARGE_LUGGAGE"]` | `STEP_FREE_REQUIRED` |
| 2 | `["LARGE_LUGGAGE","STEP_FREE_REQUIRED"]` | `AVOID_STAIRS` |

Every request reports success; one capability is silently dropped, and **which one is lost
varies between runs**. This is a lost-update race in `_replace_capability_rows` — read-modify-
write of the JOURNEY scope without isolation. Tag: `NEW`, `EAC_REFERENCE`.

### 6.3 Cross-scope duplicate — storage correct, compiler wrong

| Check | Result |
|---|---|
| TRAVELER `AVOID_STAIRS` + JOURNEY `AVOID_STAIRS` stored | **2 rows**, correct scopes and params |
| Same two items through `canonicalize_capabilities` | **1 row**, `scope="TRAVELER"`, `params` from the JOURNEY item |

---

## 7. EAC autonomous endpoints

### 7.1 `/api/v1/capabilities/catalog` — canonical defaults **do** drift from server rules

| Code | Catalog `default_severity` | Actually stored on confirm |
|---|---|---|
| `STEP_FREE_REQUIRED` | **`STRONG`** | **`HARD`** |
| `AVOID_STAIRS` | `STRONG` | `HARD` |

`catalog_vs_server_drift: true`. The catalog calls
`default_severity(code, hard_asserted=False)`, which returns `STRONG` for every hard code;
`canonicalize_capabilities` then forces `HARD`. A UI that renders the catalog's "default
severity" shows a hard accessibility need as a strong preference. The brief's requirement —
*canonical defaults must not drift from real server rules* — **fails**.

Mitigating detail: the catalog is self-consistent with the *input* contract (omitting
`severity` is what a client would do), and `needs_confirmation` does store `STRONG`
(measured: `needs_confirmation_stored: [{"code":"STEP_FREE_REQUIRED","severity":"STRONG"}]`).
The drift is between the advertised default and the effective stored severity.

### 7.2 `/api/v1/travelers/{id}/capabilities/extract` — correctly marked, still false-HARD

| Check | Result |
|---|---|
| `source` | `DETERMINISTIC_TEXT_FALLBACK` |
| `authority` | `UI_CANDIDATE_ONLY` — all 7 cases |
| Persistence | none (no `session.add`) |
| False-HARD for the two mandated sentences | **yes** |

The candidate-only marking satisfies the brief. But because the **same** extractor is merged
into `compile_semantic_envelope` on the server, the candidate-only guard does not protect the
live path: a false-HARD candidate confirmed by a user becomes a stored HARD fact.

If Codex later switches to DeepSeek-first, the boundary to verify is
`model → canonicalize → confirmation`: `canonicalize_capabilities` forces `HARD` for hard
codes, so **any** model-emitted `STEP_FREE_REQUIRED` becomes a durable HARD need — including
one derived from a denial or a third party. The `needs_confirmation` param is the only
escape hatch, and nothing in the extractor sets it for negated/hearsay clauses.

### 7.3 `/api/v1/travelers/{id}/capabilities/audit` — complete enough

| Check | Result |
|---|---|
| Journey-scope events visible | **yes** (`journey_id` populated) |
| Traveler-scope events visible | **yes** |
| Deactivation event present | **yes** (`traveler.capability.deactivated`) |
| `before`/`after` payloads present | **yes** |
| Actions observed | `traveler.capability.created`, `traveler.capability.updated`, `traveler.capability.deactivated` |

No completeness gap found. One observation: after a journey-scope confirm only **1** event is
written; after a clear, `deactivated` + 2 × `created` — consistent with the replace-all
semantics of §6.1, i.e. the audit faithfully records the destructive overwrite.

---

## 8. TRAVELER scope is still unreachable (EAC did not fix D7)

15 `scope_permanence` cases, **0 rows with `scope == "TRAVELER"` in either implementation**.

| Text | EAC | FINAL_V19 |
|---|---|---|
| `我终身不能走楼梯，这是永久性的` ("lifelong, permanent") | `JOURNEY` | `JOURNEY` |
| `我长期需要无障碍通道` ("long-term") | `JOURNEY` | `JOURNEY` |
| `I permanently need step-free access` | `JOURNEY` | `JOURNEY` |
| `我一直坐轮椅，不是这次才需要` ("not just this trip") | `JOURNEY` | `[]` |

`eac_traveler_scope_rows: 0`, `b_traveler_scope_rows: 0`. So a permanent need can never be
expressed as a traveller-level fact from text, and — per the previous round's live
measurement — a TRAVELER-scoped need blocks **every** future journey while contributing
nothing to the current journey's constraint list.

---

## 9. Verdict table

| # | EAC claim / brief item | Verdict | Tag |
|---|---|---|---|
| 1 | `I don't need a wheelchair, I can walk` no longer false-HARD | **NOT FIXED** | `EAC_REFERENCE` |
| 2 | `朋友说我可能需要轮椅，但我不这么认为` no longer false-HARD | **NOT FIXED** | `EAC_REFERENCE` |
| 3 | HARD accessibility cannot be downgraded | **FIXED** | `EAC_REFERENCE` |
| 4 | Duplicate capability codes merged | **FIXED** | `EAC_REFERENCE` |
| 5 | Clause-local negation / history | **FIXED (erasure direction only)** | `EAC_REFERENCE` |
| 6 | Numeric walking values parsed | **FIXED, but unvalidated + over-extracting** | `EAC_REFERENCE`, `NEW` |
| 7 | Rest / nap windows parsed | **FIXED** | `EAC_REFERENCE` |
| 8 | `extract` marked candidate-only | **FIXED** | `EAC_REFERENCE` |
| 9 | `confirm A → confirm B` keeps A | **VIOLATED** | `FINAL_V19`, `EAC_REFERENCE` |
| 10 | Concurrent confirm is safe | **VIOLATED** (silent loss, nondeterministic) | `NEW` |
| 11 | Cross-scope duplicate handled | storage OK, **compiler collapses scopes** | `NEW` |
| 12 | TRAVELER + JOURNEY same code | storage OK, **compiler merges** | `NEW` |
| 13 | Catalog defaults match server rules | **VIOLATED** (`STRONG` vs `HARD`) | `NEW` |
| 14 | Duplicate merge preserves the stricter numeric limit | **VIOLATED** (looser wins) | `NEW` |
| 15 | TRAVELER scope reachable from text | **NOT FIXED** | `FINAL_V19`, `EAC_REFERENCE` |
| 16 | Statement about a facility ≠ traveller's need | **VIOLATED** | `NEW` |

**Bottom line:** the EAC patch is a genuine, measurable improvement on the *detection* axis
(32 cases recovered, 0 regressions, 0 cases where FINAL_V19 was better) and on HARD
immutability and dedupe. It does **not** address the false-HARD direction that the brief
named, and its new dedupe introduces scope collapse, parameter contamination and constraint
weakening. Do not merge `canonicalize_capabilities` as-is.

---

# ADDENDUM — `CODEX_V19_1_IF_AVAILABLE` (Snapshot C, 2026-09-15 13:47:07)

Codex V19.1 landed in the main tree after Snapshot B. This addendum re-runs the
EAC-aware brief's validation targets against Snapshot C, and — the more useful
outcome — records which of EAC's defects Codex V19.1 independently solved, which
it left open, and which EAC defects never existed in the live tree at all.

Because Codex implemented the capability layer **independently** (its
`app/capabilities.py` is 19,890 B; EAC's is 19,910 B — different code), Snapshot C
is a genuine third opinion, not a copy of EAC.

## B1. The two mandated sentences — fixed by Codex, not by EAC

| Sentence | EAC | FINAL_V19 (B) | **Codex V19.1 (C)** |
|---|---|---|---|
| `I don't need a wheelchair, I can walk` | HARD ❌ | HARD ❌ | **`[]`** ✅ |
| `朋友说我可能需要轮椅，但我不这么认为` | HARD ❌ | HARD ❌ | **`[]`** ✅ |

Both now have regression tests in `patches/V19_1_TESTS_ONLY.patch`. This is the
single highest-value outcome of the whole round: the sentence pair the brief
singled out as "still broken" is broken in **EAC**, and **fixed in Codex V19.1**.

## B2. EAC defect → Codex V19.1 status

| # | EAC defect (from §5/§6 above) | Status on Codex V19.1 |
|---|---|---|
| 1 | HARD accessibility downgradable | **FIXED** — 21/21 cells force HARD |
| 2 | Duplicate capability codes not merged | **FIXED** — 8/8 |
| 3 | Cross-scope dedup collapse (`TRAVELER` + `JOURNEY`) | **NOT FIXED — REGRESSED** (see B3) |
| 4 | Duplicate merge weakens the numeric limit (looser wins) | **FIXED** — the stricter `max_m` now wins |
| 5 | Clause-local negation / history (erasure direction) | **FIXED** — 18/20, 2 residual |
| 6 | Clause-local negation (false-HARD direction) | **PARTIALLY FIXED** — 12 false HARD removed, 9 residual (B4) |
| 7 | Numeric walking values unvalidated / over-extracting | `STILL_REPRODUCIBLE` — 19 residual |
| 8 | Rest / nap windows | `STILL_REPRODUCIBLE` — 6 residual |
| 9 | TRAVELER scope unreachable from text | `STILL_REPRODUCIBLE` — 7 residual |
| 10 | `confirm A → confirm B` loses A | see `SCOPE_AUDIT_RESULTS.md` |
| 11 | Catalog defaults drift from server rules | see `SCOPE_AUDIT_RESULTS.md` |
| 12 | Facility-scoped tag satisfies step-free | **FIXED** — per-requirement evaluator |
| 13 | `overall_state` cross-subject leak | **FIXED** |

## B3. Codex V19.1's canonicalizer — one EAC defect fixed, one reproduced

The EAC merge problems split cleanly in two. One is fixed, one has **regressed**
from FINAL_V19 (which did not dedupe at all, so it could not collapse scopes).

### B3.1 FIXED — the stricter numeric limit now wins

```
B: canonicalize_capabilities([MAX_WALKING_PER_LEG_M max_m=400, MAX_WALKING_PER_LEG_M max_m=800])
   -> 2 rows, params [{'max_m': 400}, {'max_m': 800}]      # no dedupe at all
C: -> 1 row,  params [{'max_m': 400}]                      # the stricter limit wins  ✅
```

### B3.2 REGRESSED — the dedup key is `code` alone, so scopes collapse

```python
# snapshot_c/backend/app/capabilities.py:329, 365
seen: dict[str, dict[str, Any]] = {}
...
previous = seen.get(code)          # <-- scope is NOT part of the key
```

Measured directly against Snapshot B and Snapshot C:

```
B: canonicalize_capabilities([
       AVOID_STAIRS HARD scope=TRAVELER params={note: traveler},
       AVOID_STAIRS HARD scope=JOURNEY  params={note: journey}])
   -> 2 rows:
        {code: AVOID_STAIRS, severity: HARD, scope: TRAVELER, params: {note: traveler}}
        {code: AVOID_STAIRS, severity: HARD, scope: JOURNEY,  params: {note: journey}}

C: -> 1 row:
        {code: AVOID_STAIRS, severity: HARD, scope: TRAVELER, params: {note: traveler}}
```

The JOURNEY-scoped row is **silently discarded**, together with its params. This is
exactly the defect the EAC patch introduced (§5.2 above) — Codex V19.1 has
reproduced it independently. The test
`test_v191_eac_defect_merge_respects_scope` was `PASSED` on A and B and is
`FAILED` on C: a **REGRESSED** verdict, and the only regression in the whole
188-assertion suite.

**Practical impact.** A traveller who says *"I permanently use a wheelchair"* and
*"on this trip I also need step-free transfers"* should end up with a permanent
`TRAVELER` need **and** a `JOURNEY` need. Today only the first survives, so the
journey-scoped constraint is lost before it ever reaches the gate. Note that D7
(TRAVELER scope unreachable from text) is still open, so in practice both rows
currently arrive as `JOURNEY` — the collapse is latent rather than user-visible
today, but it becomes a live data-loss bug the moment D7 is fixed.

**Fix:** key `seen` on `(scope, code)` instead of `code`, and merge only within a
scope. Both halves are already encoded in `patches/V19_1_TESTS_ONLY.patch`.

### B3.3 What does hold

```
test_v191_eac_defect_merge_keeps_strictest_limit             PASSED on C (FAILED on A/B)
test_v191_eac_guard_duplicate_codes_are_merged               PASSED on C (FAILED on A/B)
test_v191_eac_guard_hard_code_cannot_be_downgraded           PASSED on C (FAILED on A/B)
test_v191_eac_defect_merge_respects_scope                    FAILED on C (PASSED on A/B)  <-- regression
```

**Consequence for the merge decision:** the advice in the closing paragraph above
("do not merge `canonicalize_capabilities` as-is") still stands, and now applies to
Codex's version too. Porting EAC's canonicalizer is pointless — Codex has the same
scope bug, the same fix location, and a better numeric-merge rule.

## B4. Residual false-HARD after the Codex V19.1 negation fix

Nine sentences still produce a HARD `STEP_FREE_REQUIRED`, verified live against
Snapshot C's extractor and unchanged from FINAL_V19:

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

The corpus shows Codex **did** fix the same classes elsewhere
(`my colleague said I might need a wheelchair` ✅, `同事说我也许需要轮椅` ✅,
`if I get tired I might need a wheelchair` ✅, `no stairs problem for me, I'm fine` ✅),
so this is a **marker-coverage gap**, not a design failure. The two shapes that
defeat it are a **relational subject** (`my friend` / `my mother` / `我妈妈` /
`我朋友` / `not me`) and a **possibility marker without a modal verb**
(`说不定`, `if I end up`).

Suggested guard additions (tests already written):
- third-party subject list: `my friend`, `my mother`, `my father`, `my colleague`,
  `我朋友`, `我妈妈`, `我父亲`, `我同事`
- first-person denial: `I am not a … user`, `not me`
- possibility markers: `说不定`, `搞不好`, `if I end up`, `I'll tell you`

## B5. EAC autonomous endpoints on Codex V19.1

Codex V19.1 does **not** ship EAC's autonomous `catalog` / `extract` / `audit`
trio under the same names; the live tree exposes the capability surface through
`/api/v1/travelers/{id}/capabilities` and `/api/v1/journeys/{id}/capabilities`
plus a new `/route-evidence` route. See `SCOPE_AUDIT_RESULTS.md` and
`OPENAPI_DRIFT_RESULTS.md` for the measured route inventory.
