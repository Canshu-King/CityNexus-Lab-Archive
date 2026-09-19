# STALE_CANDIDATE_RESULTS.md — Stale candidate lifecycle (P1-1, S01/S02)

## Defect

V19.2.2 correctly refused a stale select/start, but an expired candidate
remained an ordinary `CANDIDATE` row. The red-team evidence itself recorded
`candidate_still_listed = true`, so the API and UI could not distinguish a
current recommendation from an expired one.

## Fix

`PlanVersion` now projects the staleness of its frozen evidence:

```
stale: bool
selectable: bool
stale_reason: str | None
```

Computed by `_plan_staleness()` from the persisted `mobility_evidence_json`:

* no `snapshot_id` -> `STALE_RECOMPOSE_REQUIRED: no frozen provider evidence`
* unreadable JSON -> `STALE_RECOMPOSE_REQUIRED: mobility evidence is not readable`
* `expires_at` in the past -> `STALE_RECOMPOSE_REQUIRED: frozen provider evidence expired`
* invalid timestamp -> `STALE_RECOMPOSE_REQUIRED: evidence timestamp invalid`

This is a **projection only**. Selection revalidation and `/start` remain the
authoritative guards; the flag exists so a stale plan cannot *look* current.

## Verified behaviour (S01/S02)

| Check | Fresh plan | Expired plan |
| --- | --- | --- |
| `stale` | false | **true** |
| `selectable` | true | **false** |
| `stale_reason` | null | `STALE_RECOMPOSE_REQUIRED: frozen provider evidence expired` |
| `/start` | — | **409** `STALE_RECOMPOSE_REQUIRED` |
| journey status after refusal | — | `PLANNED` (never ACTIVE) |
| `experience_flags.staleness` | false | **true** |
| `experience_flags.needs_review` | false | **true** |
| UI warning panel | not rendered | **rendered**, "Trip evidence needs re-syncing" |

Both mandated viewports (390x844, 430x932) behave identically.

## Evidence

* `evidence/mobile_v1923_d.json` — `STALE_CANDIDATE_WARNING` for both viewports:
  `candidate_flagged_stale = true`, `candidate_selectable = false`,
  `start_status = 409`, `panel_visible = true`.
* `tests/test_v1923_final_code_gate.py` — S01 and S02 regression tests.
* `evidence/v1923_gate_run.txt` — 74 passed.

## Not claimed

The stale UI was exercised on emulated mobile viewports only. No physical
device was used.
