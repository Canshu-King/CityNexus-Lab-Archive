# CODEX_V19_1_DELTA_RESULTS.md — targeted read-only delta check

**Tag: `CODEX_V19_1_IF_AVAILABLE`**

The brief authorises **one** targeted read-only delta check if Codex V19.1 lands
in the back half of the round, and explicitly forbids a full re-run. This is that
single check, and nothing more.

| Item | Value |
|---|---|
| Trigger | Codex wrote `backend/app/capabilities.py`, `backend/app/replanning/feasibility.py` and `backend/app/main.py` in the main tree after Snapshot B was taken |
| Live-tree mtimes | `capabilities.py` 13:3x, `feasibility.py` 13:3x, `main.py` 13:3x (all after Snapshot B at 13:05:57) |
| Snapshot C taken | `2026-09-15 13:47:07`, 341 files, 10.6 s |
| `import app.main` | **OK** (`missing_symbols: {}`) |
| `app/capabilities.py` | 15,283 B → **19,890 B**, sha16 `7e3ff4cb3a85b7b6` → **`b342df348c0d62a7`** |
| Main tree modified by me | **No** (verified: only Codex's own edits; my probe DBs live under `evidence/_db/`) |

Snapshot C is a **read-only copy**. Every measurement below was taken against the
copy, with `PYTHONDONTWRITEBYTECODE=1`, so the main tree was never imported from
directly and never written to.

---

## 1. Focused contract suite: A → B → C

The **same four test files** (byte-identical sha256 in all three snapshots —
verified) were run against each snapshot.

| Snapshot | Tree | Passed | Failed | Skipped | Collected |
|---|---|---:|---:|---:|---:|
| A | FINAL_V19 @ 12:38 | 37 | 106 | 45 | 188 |
| B | FINAL_V19 @ 13:06 | 37 | 106 | 45 | 188 |
| **C** | **Codex V19.1 @ 13:47** | **119** | **54** | **15** | **188** |

**Codex V19.1 fixed 52 of the 106 failing assertions. Zero guards broke.**

> **Harness defect found and fixed during this check.** The first pass of this
> suite reported 108 assertions. The EAC test file used a *module-level*
> `pytest.importorskip("app.integrations.accessibility.osm")`; because that
> package does not exist on any tree, collection raised `Skipped` and pytest
> silently dropped **every** test in the file — including the two mandated-sentence
> tests. It has been replaced with a `try/except ImportError` binding plus a
> `@requires_osm` marker, so the module now collects 81 tests instead of 0.
> Any earlier "108 assertions" figure from this round is superseded by 188.

### Per delta target

| Target | A → B (FINAL_V19 drift) | **B → C (Codex V19.1)** |
|---|---|---|
| D1 hard-downgrade guard | 2 fixed / 19 still | **21 fixed / 0 still** |
| D2 clause-local negation & history | 2 fixed / 18 still | **18 fixed / 2 still** |
| D3 duplicate capability codes | 0 fixed / 8 still | **8 fixed / 0 still** |
| D4 walking / rest numerics | 6 fixed / 19 still | 6 fixed / **19 still** |
| D5 rest & nap windows | 2 fixed / 6 still | 2 fixed / **6 still** |
| D6 gate interprets capability | 2 fixed / 1 still | 1 fixed / 1 still / 1 **stale test** |
| D7 TRAVELER scope reachable | 2 fixed / 7 still | 2 fixed / **7 still** |
| EAC / provider-evidence scope | 4 fixed / 26 still / 20 not covered | **22 fixed / 9 still / 8 new defects / 22 new guards hold** |
| guards (must not regress) | 13 GUARD_HOLDS | **13 GUARD_HOLDS** |

### Verdict per original finding

| # | Finding | Verdict |
|---|---|---|
| D0 | `capability_payload` import blocker | `FIXED_IN_CURRENT` (already at 12:37, before Snapshot A) |
| D1 | HARD accessibility severity is downgradable | **`FIXED_IN_CURRENT`** — all 21 cells now force HARD |
| D2 | negation / history is text-global | **`FIXED_IN_CURRENT`** for 18 of 20; 2 residual (see §2) |
| D3 | no capability-code dedup | **`FIXED_IN_CURRENT`** — 8/8 |
| D4 | walking numerics | `STILL_REPRODUCIBLE` — 19 residual |
| D5 | rest / nap windows | `STILL_REPRODUCIBLE` — 6 residual |
| D6 | gate interprets capability | `FIXED_IN_CURRENT` (the `UNSUPPORTED_HARD_CONSTRAINT` fail-closed branch is gone) |
| D7 | TRAVELER scope unreachable | `STILL_REPRODUCIBLE` — 7 residual |
| — | P0 ARRIVAL-anchored C4 strands the journey (`/start` → 500) | **`STILL_REPRODUCIBLE`** |
| — | P0 generate/select ignore C4 while booking enforces it | **`STILL_REPRODUCIBLE`** |
| — | provider-evidence scope: `wheelchair=yes + step_count=5` must be CONFLICT | **`STILL_REPRODUCIBLE`** (new, measured on C) |
| — | provider-evidence scope: list/tuple tag forms silently dropped | **`STILL_REPRODUCIBLE`** (new, measured on C) |
| — | generic `overall_state` cross-subject leak | **`FIXED_IN_CURRENT`** — Codex replaced the generic call with a per-requirement evaluator |
| — | third-party / facility-description / speculation false HARD | **`STILL_REPRODUCIBLE`** — 9 cases (see §2b) |
| — | cross-scope dedup collapse (`TRAVELER` + `JOURNEY`) | **`REGRESSED`** (see §6) |

---

## 2. The two mandated false-HARD sentences are **fixed** by Codex V19.1

The EAC-aware brief states that an independent review confirmed the **EAC capability
patch** still produces a wrong HARD need for these two sentences, and asks for them
to be re-tested and added to the tests-only patch.

| Sentence | EAC reference | FINAL_V19 (B) | **Codex V19.1 (C)** |
|---|---|---|---|
| `I don't need a wheelchair, I can walk` | HARD `STEP_FREE_REQUIRED` ❌ | HARD `STEP_FREE_REQUIRED` ❌ | **`[]`** ✅ |
| `朋友说我可能需要轮椅，但我不这么认为` | HARD `STEP_FREE_REQUIRED` ❌ | HARD `STEP_FREE_REQUIRED` ❌ | **`[]`** ✅ |

**The EAC claim is falsified for EAC and confirmed-fixed for Codex V19.1.**
Both sentences are now encoded as regression tests in
`patches/V19_1_TESTS_ONLY.patch`.

Across the full 182-case discriminating corpus:

| Metric | Value |
|---|---|
| corpus size | 182 |
| cases whose extracted code set changed B → C | 22 |
| false-HARD removed (`hard_fixed`) | **12** |
| correct HARD newly produced (`new_hard`) | **7** |
| cases where B had a code and C lost it | 14 (all 12 false-HARD removals + 2 stale expectations) |
| HARD-producing cases, B → C | 64 → **59** |

Per bucket (`hard_fixed` = a wrong HARD removed, `new_hard` = a correct HARD added):

| bucket | n | changed | hard_fixed | new_hard |
|---|---:|---:|---:|---:|
| clause_negation | 25 | 6 | 0 | **5** |
| denial_vs_need | 28 | 5 | **4** | 0 |
| hearsay | 6 | 2 | **2** | 0 |
| hypothetical | 3 | 3 | **3** | 0 |
| mandated | 2 | 2 | **2** | 0 |
| mixed_language | 9 | 1 | 1 | 0 |
| scope_permanence | 15 | 1 | 0 | 1 |
| hard_vs_soft | 25 | 1 | 0 | 1 |
| duplicate_multi | 12 | 1 | 0 | 0 |
| provider_evidence / rest_nap_window / stroller_luggage / walking_numeric | 5/15/10/27 | 0 | 0 | 0 |

Examples of false HARD removed (`B → C`):

| text | B | C |
|---|---|---|
| `I don't need a wheelchair, I can walk fine` | `STEP_FREE_REQUIRED` | `[]` |
| `I don't use a wheelchair` | `STEP_FREE_REQUIRED` | `[]` |
| `no stairs problem for me, I'm fine` | `AVOID_STAIRS` | `[]` |
| `my colleague said I might need a wheelchair` | `STEP_FREE_REQUIRED` | `[]` |
| `同事说我也许需要轮椅` | `STEP_FREE_REQUIRED` | `[]` |
| `if I get tired I might need a wheelchair` | `STEP_FREE_REQUIRED` | `[]` |
| `如果累了可能需要轮椅` | `STEP_FREE_REQUIRED` | `[]` |
| `maybe I should avoid stairs` | `AVOID_STAIRS` | `[]` |
| `no stroller this time, ignore that` | `STROLLER` | `[]` |

Examples of a correct HARD now produced (`B → C`):

| text | B | C |
|---|---|---|
| `轮椅必须全程无障碍，没有例外` | `[]` | `STEP_FREE_REQUIRED` |
| `我以前不用轮椅，但现在必须无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `过去我坐轮椅，现在必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `我没有过敏，但我用轮椅，必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `不需要人扶，但我坐轮椅，必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `我一直坐轮椅，不是这次才需要` | `[]` | `STEP_FREE_REQUIRED` |
| `必须全程无障碍，没有例外` | `[]` | `STEP_FREE_REQUIRED` |

**Net effect: 19 wrong answers corrected, 0 new false-HARD introduced in the corpus.**

### The 2 residual D2 cases

| text | Codex V19.1 |
|---|---|
| `说不定到时候我需要轮椅` | still produces HARD `STEP_FREE_REQUIRED` |
| `if I end up in a wheelchair I'll tell you` | still produces HARD `STEP_FREE_REQUIRED` |

These are *speculative* statements (`说不定…`, `if I end up…`). The 3-case
`hypothetical` bucket was fully fixed, so this is a residual marker gap rather than
a systematic failure. Both are now in the tests-only patch.

### 2b. Residual false-HARD class — third-party, facility description, speculation

Nine further sentences still manufacture a HARD `STEP_FREE_REQUIRED` on Codex
V19.1. All nine were verified live against Snapshot C's extractor (not merely
reported by the test suite), and all nine are unchanged from FINAL_V19:

| text | B | C | why it is wrong |
|---|---|---|---|
| `my friend needs a wheelchair, not me` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | the need belongs to someone else; `not me` is explicit |
| `my mother uses a wheelchair` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | companion's need, not the traveller's |
| `我朋友需要轮椅` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | third party |
| `我妈妈坐轮椅` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | third party |
| `I am not a wheelchair user` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | explicit self-denial |
| `the station has an accessible toilet` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | a facility description, not a requirement |
| `车站有无障碍厕所` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | facility description |
| `说不定到时候我需要轮椅` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | speculation |
| `if I end up in a wheelchair I'll tell you` | `STEP_FREE_REQUIRED` | `STEP_FREE_REQUIRED` | conditional, explicitly deferred |

The 182-case corpus **did** cover the same *classes* and Codex fixed most of them
(`my colleague said I might need a wheelchair` ✅, `同事说我也许需要轮椅` ✅,
`if I get tired I might need a wheelchair` ✅, `no stairs problem for me, I'm fine` ✅).
So this is **not** a blanket failure — it is a **marker-coverage gap**: the
extractor recognises `said`, `might`, `maybe`, `no ... problem` but not
`my friend` / `my mother` / `我妈妈` / `我朋友` / `not me` / `说不定` / `if I end up`.
The pattern is that a *relational subject* (someone other than the speaker) and a
*possibility marker without a modal verb* both defeat it.

**Recommendation (Codex handoff):** extend the negation/subject guards with a
third-party subject list (`my friend`, `my mother`, `my father`, `my colleague`,
`我朋友`, `我妈妈`, `我父亲`, `我同事`, …) and a first-person denial form
(`I am not a X user`, `not me`), and treat `说不定` like `也许`/`可能`.

All nine are encoded as regression tests in `patches/V19_1_TESTS_ONLY.patch`.

---

## 3. Provider-evidence scope on Codex V19.1

Codex V19.1 replaced the generic `accessibility_state(metadata)` call with a
**per-requirement** evaluator:

```python
# snapshot_c/backend/app/replanning/feasibility.py:286
state = evaluate_accessibility_requirement(code, metadata or {})
```

```python
# snapshot_c/backend/app/capabilities.py:454
def evaluate_accessibility_requirement(code: str, facts: Any) -> str:
    """Evaluate only evidence that is about the requested requirement."""
```

This is the correct structural answer to the cross-subject-leak problem. Measured
on the 30-case tag matrix (evidence: `evidence/codex_v19_1_evidence.json`):

**23 / 30 pass.**

| Brief demand | Result |
|---|---|
| `toilets:wheelchair=yes` MUST NOT satisfy `STEP_FREE_REQUIRED` | **PASS** → `ACCESSIBILITY_UNVERIFIED` |
| `ramp=yes` / `elevator=yes` / `ramp:wheelchair=yes` / `highway:elevator=yes` MUST NOT prove step-free | **PASS** — none verify |
| `kerb=lowered` / `tactile_paving=yes` MUST NOT prove step-free | **PASS** |
| route-level step-free with no real route evidence MUST stay unknown | **PASS** → `NEEDS_LIVE_EVIDENCE` |
| generic `overall_state` MUST NOT propagate across subject/code | **PASS** — route + place `wheelchair=yes` still yields `NEEDS_LIVE_EVIDENCE` |
| `wheelchair=yes + step_count=5` MUST be CONFLICT | **FAIL** → `ACCESSIBILITY_UNVERIFIED` |
| list/tuple tag forms MUST NOT be silently dropped | **FAIL** — 4 of 7 forms lost |

### Residual defect 1 — `step_count` / `steps` / `highway=steps` are invisible

`evaluate_accessibility_requirement` only recognises stairs via `truth("stairs", "has_stairs")`.
It never reads `step_count`, `steps` or `highway=steps`. Therefore a place that
advertises `wheelchair=yes` **and** `step_count=5` is reported as merely
unverified, not as the contradiction it is:

| tags | Codex V19.1 `STEP_FREE_REQUIRED` | expected |
|---|---|---|
| `{wheelchair: yes, step_count: 5}` | `ACCESSIBILITY_UNVERIFIED` | `ACCESSIBILITY_CONFLICT` |
| `{wheelchair: yes, steps: yes}` | `ACCESSIBILITY_UNVERIFIED` | `ACCESSIBILITY_CONFLICT` |
| `{wheelchair: yes, highway: steps}` | `ACCESSIBILITY_UNVERIFIED` | `ACCESSIBILITY_CONFLICT` |
| `{wheelchair: yes, stairs: yes}` | `ACCESSIBILITY_CONFLICT` ✅ | `ACCESSIBILITY_CONFLICT` |

The consequence is a **fail-open** in the wrong direction: because the gate treats
`UNVERIFIED` as a blocker (`ACCESSIBILITY_UNVERIFIED` + `NEEDS_LIVE_EVIDENCE`), the
journey is still blocked — but for the wrong reason, and the operator never learns
that the provider data contradicts itself. `step_count=5` is a hard numeric
contradiction and must surface as `CONFLICT`.

### Residual defect 2 — list/tuple tag values are silently dropped

`normalize_osm_tags` stringifies any mapping value:

```python
# snapshot_c/backend/app/capabilities.py:439
if isinstance(value, Mapping):
    return {str(k).strip().lower(): str(v).strip().lower() for k, v in value.items()}
```

so a provider that emits a list value loses it:

| tags | resolved by `normalize_osm_tags` | verdict |
|---|---|---|
| `{wheelchair: ["yes"]}` | `{wheelchair: "['yes']"}` | **dropped** |
| `{ramp: ("yes",)}` | `{ramp: "('yes',)"}` | **dropped** |
| `{step_count: [5]}` | `{step_count: "[5]"}` | **dropped** |
| `{toilets:wheelchair: ["yes"]}` | `{toilets:wheelchair: "['yes']"}` | **dropped** |
| `["wheelchair=yes", "ramp=yes"]` (sequence) | `{wheelchair: "yes", ramp: "yes"}` | ✅ handled |
| `{tags: {"wheelchair": "yes"}}` (nested) | `{wheelchair: "yes"}` | ✅ handled |
| `{tags: ["wheelchair=yes"]}` (nested) | `{wheelchair: "yes"}` | ✅ handled |

So the *sequence* and *nested* forms are handled correctly; only a list/tuple used
as a **mapping value** is lost. The brief's "list/tuple tag forms must not be
silently dropped" is therefore **half met**: dropped in the value position, safe in
the sequence/nested positions.

### Residual defect 3 — `step_free_verified` is dropped at the metadata top level

`_accessibility_metadata` (feasibility.py:262–277) whitelists only
`evidence_status, status, step_free, wheelchair_access, stairs, stroller_accessible,
luggage_accessible` when reading top-level metadata keys, and then reads
`osm_tags`/`tags`. A provider assertion of `step_free_verified=yes` placed directly
on the place metadata is therefore invisible:

| metadata shape | `STEP_FREE_REQUIRED` |
|---|---|
| `{step_free_verified: yes}` (top level) | `ACCESSIBILITY_UNVERIFIED` ❌ |
| `{step_free_verified: yes}` under `osm_tags` | `ACCESSIBILITY_VERIFIED` ✅ |
| `{step_free_verified: yes}` under `tags` | `ACCESSIBILITY_VERIFIED` ✅ |
| `{step_free: yes}` (top level) | `ACCESSIBILITY_VERIFIED` ✅ |

Same value, different nesting, different answer. The whitelist is one key short.

---

## 4. The one regression: cross-scope dedup collapse

`test_v191_eac_defect_merge_respects_scope` is the **only** assertion in the 188
that went from PASSED to FAILED across B → C.

Codex V19.1 added duplicate-code merging (good — D3 is fixed 8/8), but the dedup
key is the **code alone**:

```python
# snapshot_c/backend/app/capabilities.py:329, 365
seen: dict[str, dict[str, Any]] = {}
...
previous = seen.get(code)          # <-- scope is NOT part of the key
```

Measured directly against both snapshots:

```
B: canonicalize_capabilities([
       AVOID_STAIRS HARD scope=TRAVELER params={note: traveler},
       AVOID_STAIRS HARD scope=JOURNEY  params={note: journey}])
   -> 2 rows  (scope=TRAVELER, scope=JOURNEY)

C: -> 1 row   {code: AVOID_STAIRS, severity: HARD, scope: TRAVELER, params: {note: traveler}}
```

The JOURNEY-scoped row and its params are **silently discarded**. This is the same
defect the EAC patch introduced, reproduced independently in the live tree.

**Impact.** A traveller with a permanent need *and* a trip-specific need of the
same code keeps only the permanent one. The collapse is latent today because D7 is
still open (every natural-language form currently resolves to `JOURNEY`, so there
is usually only one row to collapse) — but it becomes a live data-loss bug the
moment D7 is fixed. Fix: key `seen` on `(scope, code)`.

Note the merge rule is otherwise *better* than FINAL_V19's: two unscoped
`MAX_WALKING_PER_LEG_M` limits now merge to the stricter value (400 wins over 800),
which B did not do at all.

## 5. What is *not* claimed

- **No full re-run was performed.** Only the focused suite (188 assertions), the
  182-case corpus extractor comparison, the two C4 probes and the tag matrix were
  executed against Snapshot C. The 494-case / 168-flow sweep was deliberately not
  repeated.
- **The EAC lab was not stood up as a product.** Only its
  `app/capabilities.py` and `app/integrations/accessibility/osm.py` were loaded by
  file path, for the reference column.
- **Snapshot C is a copy, not the live tree.** If Codex edits further, the C
  measurements stay bound to 13:47:07 — per the V19 lesson, conclusions must carry
  their baseline timestamp.

## 6. Artefacts

| File | Contents |
|---|---|
| `evidence/snapshot_c.json` | Snapshot C manifest, hashes, import status, symbol check |
| `evidence/_junit_{a,b,c}.xml` | JUnit XML for the three suite runs |
| `evidence/postfix_classification.json` | Per-assertion A→B and B→C verdicts, 108 rows |
| `evidence/codex_v19_1_corpus_delta.json` | 182-case B vs C extractor comparison |
| `evidence/codex_v19_1_evidence.json` | 30-case tag matrix + route + gate projection + sentences |
| `evidence/c4_gate_c.json`, `evidence/c4_start_c.json` | The two P0 probes on Snapshot C |
| `evidence/accessibility_evidence_scope.json` | EAC / A / B / C sentence replay |
