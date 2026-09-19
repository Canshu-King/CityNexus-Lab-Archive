# Starter Patch Validation — independent re-measurement

The road-prep's `PATCH_PORT_MATRIX.md` reports all three patches as `git apply --check` **PASS**.
That was measured against the V19.1 baseline. It is **no longer true** on the current tree.
Nothing here trusts the road-prep's verification: every claim was re-measured in this lab
against `snapshot_a` (2026-09-15 17:29:11) and `snapshot_b` (17:50:44), which are byte-identical
for `capabilities.py` and `feasibility.py`.

Reproduction (per patch, in a throwaway copy — the main tree is never touched):

```
cp -r snapshot_a _scratch/<name>
cd _scratch/<name> && git init -q .
git apply --check -v ../../_brief/patches/<patch>
```

## Apply results

| Patch | Road-prep says | Re-measured on V19.2 | First failing hunk |
|---|---|---|---|
| `V19_1_LOW_CONFLICT_FIXES.patch` (5,715 B) | PASS | **FAIL — does not apply** | `capabilities.py:326` — the canonicalizer body was rewritten |
| `V19_1_TESTS_ONLY.patch` (65,189 B) | PASS | **PASS** | n/a — all four files are `new file mode`, so there is nothing to conflict with |
| `V19_2_VERIFIED_STARTER.patch` (15,848 B) | PASS | **FAIL on `capabilities.py`** | `capabilities.py:110` — the marker block already exists in a slightly different form |

`V19_1_LOW_CONFLICT_FIXES.patch` fails with:

```
error: while searching for:
    """Validate model/API candidates and enforce hard-severity invariants."""

    result: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
error: patch failed: backend/app/capabilities.py:326
error: backend/app/capabilities.py: patch does not apply
```

`V19_2_VERIFIED_STARTER.patch` fails with:

```
error: while searching for:
    "allegedly",
)


@dataclass(frozen=True)
class CapabilityItem:
error: patch failed: backend/app/capabilities.py:110
error: backend/app/capabilities.py: patch does not apply
Checking patch backend/app/replanning/feasibility.py...   (no error reported)
```

## Why they no longer apply — and why that is the good news

**Codex V19.2 has already merged the substance of `V19_2_VERIFIED_STARTER.patch` into
`capabilities.py`.** The file grew `19,890 B → 23,668 B` and now contains all six new marker
constants plus the scope and numeric-merge logic the patch introduced:

| STARTER patch content | Present in V19.2 `capabilities.py`? | Where |
|---|---|---|
| `_SPECULATIVE_MARKERS` | ✅ | line 112 |
| `_THIRD_PARTY_MARKERS` | ✅ | line 113 |
| `_FACILITY_SUBJECT_MARKERS` | ✅ | line 114 |
| `_FIRST_PERSON_MARKERS` | ✅ | line 115 |
| `_PERMANENCE_MARKERS` | ✅ | line 116 |
| `_THIS_TRIP_MARKERS` | ✅ | line 117 |
| `effective_scope` (permanence → TRAVELER) | ✅ | lines 234–236 |
| clause filter: speculative / third-party / facility | ✅ | lines 246–251 |
| `merge_key = (payload.get("scope"), code)` | ✅ | line 390 |
| numeric upper-bound min-merge | ✅ | lines 402–405 |
| `_time_window` rejects reversed windows | ✅ | lines 198–199 |
| `_number_before` km→m, negatives, decimals | ✅ | lines 203–210 |
| `normalize_osm_tags` unwraps list/tuple values | ✅ | lines 472–474 |
| `step_count` / `highway=steps` → CONFLICT | ⚠️ **partial** | lines 502–507 |
| **`feasibility.py` `_accessibility_metadata` whitelist additions** | ❌ **absent** | `feasibility.py` unchanged since 13:16:26 |

So the patch is *stale*, not *unapplied* — with **one important exception**: the patch's second
half (the `feasibility.py` whitelist) was **not** merged. `feasibility.py` still has
`8a0de9106818725d`, identical to Snapshot C, and its whitelist still omits `step_free_verified`,
`route_step_free`, `route_step_free_verified`, `has_stairs`, `step_count`, `steps`, `highway`.

That asymmetry is directly measurable:

- `evidence/capability_semantics_a.json` → `G3_contradiction` — `{"wheelchair": "yes", "step_count": "5"}` (flat) → `ACCESSIBILITY_CONFLICT` ✅, but the **nested** form `{"osm_tags": {"wheelchair": "yes", "step_count": "5"}}` → `ACCESSIBILITY_UNVERIFIED` ❌.
- `evidence/lifecycle_a.json` → `capability_evidence_verified_string` → **422 / 0 plans**, because `_accessibility_metadata` forwards `evidence_status` but `evaluate_accessibility_requirement` never reads it.
- focused suite → `test_v191_eac_defect_top_level_step_free_verified_is_seen` **FAILS**.

## Independent measurement of what the patches claim

The road-prep's `VERIFICATION.md` claims, after applying the starter, "false-HARD / evidence /
merge selection: 32 passed" and "144 passed / 1 failed / 13 skipped" with the single failure
being an internal contradiction about `走路不能超过 0 米`. Measured here on the **unpatched**
V19.2 tree, with this round's own probe suite:

| Property the patch claims to guarantee | V19.2 baseline (measured) |
|---|---|
| nine residual false-HARD sentences are clean | ✅ 9/9 (`capability_semantics_a.json`, G1) |
| the two mandated sentences still produce HARD | ✅ 2/2 (G1 `mandated_guard`) |
| `(scope, code)` dedup | ✅ 2/2 (G2) |
| facility tags never verify step-free | ✅ 12/12 (G3) |
| `wheelchair=yes + step_count=5` → CONFLICT | ⚠️ flat form only (G3, 5/7) |
| list/tuple tag values are not dropped | ✅ 5/5 (G3) |
| reversed time window rejected | ✅ (`cross_snapshot_numeric.json`) |
| km → m | ✅ |
| **`0 m` is not persisted as a clean cap** | ❌ `{'max_m': 0, 'needs_clarification': False}` HARD |
| **a minutes value does not become a metres cap** | ❌ `连续走不能超过 20 分钟` → `max_m: 20` HARD |

The road-prep describes the `0 m` behaviour as "an internal contradiction between
`走路不能超过 0 米` and another safety test, where road-prep deliberately chose the safer trial
policy". The measurement does not support that framing: the tree currently persists `0 m` as a
**clean, authoritative, HARD** cap with `needs_clarification: false`. That is the exact opposite
of the road-prep's own stated policy in `DEFECT_MATRIX.md` P0-7 ("local fallback must not persist
`0 m` as a clean authoritative numeric cap"). **The policy is stated but not implemented.**

## Verdict

| Question | Answer |
|---|---|
| Do the supplied patches apply to the current tree? | **No — 2 of 3 fail** |
| Is the failure a defect in the patches? | No — they are stale; Codex already merged most of the starter |
| Is the starter's substance present in the tree? | **Mostly yes, with a measurable gap in `feasibility.py`** |
| Should Codex apply them? | **No.** Applying `V19_1_TESTS_ONLY.patch` is safe and useful. Re-deriving the `feasibility.py` whitelist change against the current file is needed; the other two patches should be withdrawn |

---

# This round's own deliverable — `patches/V19_2_TESTS_ONLY.patch`

Produced by `tools/v192_make_tests_patch.py`. Two new files, both `new file mode 100644`,
818 added lines, no production module touched.

| File | Purpose |
|---|---|
| `backend/tests/v192_harness.py` | self-locating harness: throwaway SQLite in `%TEMP%`, `PYTHONDONTWRITEBYTECODE=1`, in-process `TestClient`, plus direct readers for plans, commitments and place evidence |
| `backend/tests/test_v192_shadow_trial_gate.py` | 61 contract assertions: 37 `test_v192_guard_*` (must pass) + 24 `test_v192_defect_*` (locked defects) |

Apply check, run in a throwaway git repository (never the main tree):

```
mkdir -p _scratch/patchcheck/backend/tests
cd _scratch/patchcheck && git init -q .
git apply --check ../../patches/V19_2_TESTS_ONLY.patch   -> PASS
git apply         ../../patches/V19_2_TESTS_ONLY.patch   -> OK
```

Byte identity of the applied files against the lab sources:

| File | sha256 (first 16) | Applied == source |
|---|---|---|
| `v192_harness.py` | `341cf4247831330b` | ✅ MATCH |
| `test_v192_shadow_trial_gate.py` | `98c3917e680c1db0` | ✅ MATCH |

> **Windows note.** A first apply in a scratch repo with `core.autocrlf=true` wrote CRLF and
> changed the hashes. The **main tree has `core.autocrlf=false`** (verified read-only), so the
> patch lands byte-identical there. Do not "fix" the patch for CRLF; fix the local git config if
> a scratch checkout disagrees.

## Measured behaviour of the patch on the V19.2 baseline

```
cd backend && python -m pytest tests/test_v192_shadow_trial_gate.py -q
-> 24 failed, 37 passed
```

Every failure is a `test_v192_defect_*`; **every `test_v192_guard_*` passes**. That is the intended
fail→pass flip: when Codex fixes a defect, its test goes green and can be renamed to a guard.

Adding the file to the round's focused suite (no interference — the existing profile is unchanged
apart from the addition):

| Suite | Result |
|---|---|
| V19.1 four files only | 14 failed, 161 passed, 13 skipped |
| V19.1 four files + this file | **38 failed, 198 passed, 13 skipped** |

Delta = exactly +24 failures / +37 passes, i.e. the new file neither masks nor perturbs any
existing assertion. `13 skipped` is unchanged.
