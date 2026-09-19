# Patch Port Matrix

All patches are starting points, not authority.

| Patch | Apply-check against supplied Codex V19.1 | Scope | Recommendation |
|---|---:|---|---|
| `V19_1_LOW_CONFLICT_FIXES.patch` | PASS | `(scope, code)` dedup, mapping-sequence normalization, stair evidence | Safe reference; port or apply after inspecting live tree |
| `V19_1_TESTS_ONLY.patch` | PASS | WorkBuddy contract/red-team tests | Apply only to a branch/snapshot first; reconcile one conflicting `0 m` expectation |
| `V19_2_VERIFIED_STARTER.patch` | PASS | Includes the low-conflict fixes plus conservative fallback guards, scope language, stricter merge, evidence normalization, km/negative/time-window safety | Prefer semantic port; it is broader and supersedes the production parts of the first patch |

## `V19_2_VERIFIED_STARTER.patch` verification

The starter patch was generated as a production-only diff against the supplied Codex V19.1 baseline. It touches only:

```text
backend/app/capabilities.py
backend/app/replanning/feasibility.py
```

Targeted checks on the patched scratch tree:

```text
false-HARD / evidence / merge selection: 32 passed
scope-language selection:               8 passed
numeric/window safety selection:        8 passed
```

A full run of the two WorkBuddy V19.1 contract modules produced:

```text
144 passed
1 failed
13 skipped
```

The single failure is an internally conflicting WorkBuddy test that requires `走路不能超过 0 米` to persist `max_m=0`, while another WorkBuddy safety test requires a non-positive walking limit not to persist. This road-prep intentionally chooses the safer trial policy: local fallback should request clarification rather than turn `0 m` into a clean authoritative numeric limit.

## What the starter patch does NOT fix

It does not solve the two largest product P0s:

- C4 feasibility split-brain;
- ARRIVAL C4 `/start` 500.

It also does not implement mid-trip replan orchestration or stale-plan lifecycle. Codex must implement those in the main tree.
