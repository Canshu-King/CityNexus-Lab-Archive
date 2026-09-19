# TRACE_EVIDENCE_NOTE.md — how to read the two trace files

Journey: `4bf2b6c9-b177-4f4f-a3ed-33a5ef09f25f` (fresh Xiamen journey, live Overpass POIs)
Captured: 2026-09-18 05:24 local

## What the trace proves

`VISIBLE_UI_TRACE_XIAOMI_FINAL.json` — the full 18-step visible UI journey:

| step | result |
|---|---|
| create-xiamen-journey | 201 |
| ai-plan-run-specific | new-candidates (baseline=0 new=3 reported=3) |
| select-plan | selected |
| trips-multiday | 4 stops |
| activity-detail | opened |
| hotel-select | selected |
| booking-import-confirm | **confirmed** (ref=E2E-V2-BOOKING-1, amount=18000, origin=厦门北站) |
| commitments-before-closure | 1 commitment, activity_id_nulls=1 |
| copilot-place-question | answered honestly (refuses to invent a review) |
| xiamen-map | panel |
| live | has-next |
| replan-before | captured, with base_plan_id / affected_activity_id / affected semantic key |
| closure-event | 201 (CLOSURE -> named mutable POI) |
| closure-proposal | **422 — no feasible replan proposal** |
| replan-after | unchanged, active plan unchanged, locked 6->6 |
| trips-vs-backend | match (ui=14 backend=14) |

So the acceptance ordering IS satisfied: a CONFIRMED booking exists before the
closure/replan step, and the before/after snapshots carry ID-level identities.

## What the trace does NOT prove, and why

**No replan was accepted on this journey.** The closure replan returned 422, so
the active plan is unchanged and the closed venue legitimately remains. The
harness says so explicitly rather than hiding it:

```
closed_place_reappeared: true
applicable: false
applicability_reason: "no replan was accepted, so the active plan is unchanged
                       and the closed venue is expected to remain"
non_degenerate: true
discriminates: true
```

The assertion is no longer the old always-true `place_id` comparison. It now
compares `metadata.semantic_key` and carries a `self_test` block proving it can
return false:

```
closed venue still present -> expected True,  actual True   PASS
closed venue replaced      -> expected False, actual False  PASS
all identities UNKNOWN     -> expected False, actual False  PASS
empty activity set         -> expected False, actual False  PASS
target identity UNKNOWN    -> expected False, actual False  PASS
```

`REPLAN_IDENTITY_TRACE.json` contains the before/proposal/after identities and
that self-test in full.

## The blocker

The 422 is Finding 3 in `FINDINGS.md`: every new replan leg is priced at the
mock fixture's constant 20 minutes, so the re-timed proposal overlaps the pinned
check-in and the deterministic gate refuses it. The gate is correct. The travel
time is fabricated. See `MOCK_MOBILITY_LIMITATION.md`.

**This is why the package must not be presented as "replan verified end to
end".** The identity machinery is verified; the acceptance of a real closure
replan is blocked upstream.
