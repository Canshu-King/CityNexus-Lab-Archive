# MIDTRIP_RECOVERY_RESULTS.md

**Scope:** what happens when a capability changes **during** a journey — the brief's
"mid-trip capability" focus item.
**Scenarios:** traveller gets hurt mid-trip and needs step-free access; elderly companion
suddenly needs less walking; wheelchair requirement appears mid-trip.
**Evidence:** `evidence/lifecycle_a.json`, `evidence/lifecycle_b.json`,
`evidence/commitment_conflict_{a,b}.json`
**Probes:** `tools/v191_probe_lifecycle.py` (`midtrip` step), `tools/v191_probe_commitment_conflict.py`

---

## 1. Sequence measured

The mid-trip scenario was moved **before** plan generation so the selected plan genuinely
violates the new need:

| Step | Result |
|---|---|
| Journey in progress with a selected plan | `ACTIVE` |
| `PUT /journeys/{id}/capabilities` with a HARD need | **409** `"hard capability needs require /confirm"` |
| `POST /journeys/{id}/capabilities/confirm` with the HARD need | **200** |
| Audit row written | `traveler.capability.created` |
| `plans_mutated_silently` | **`false`** |
| `replan_proposals` | **`0`** |
| Journey status afterwards | **`ACTIVE`** |

## 2. What works

**The journey is not stranded.** The journey remains `ACTIVE` throughout; declaring a new HARD
mid-trip need does not put it into an unrecoverable state.

**The selected plan is not silently mutated.** `plans_mutated_silently: false` — the
already-selected plan's activities are unchanged by the capability update. This is the correct
behaviour: silently rewriting a plan a traveller is currently executing would be worse than
doing nothing.

**The two-step guard works.** A HARD need cannot be introduced by a plain `PUT` — `409` forces
the explicit `/confirm` endpoint, and the capability is only persisted after confirmation.
This is the right shape and it is consistent between the JOURNEY and TRAVELER scopes.

**The change is audited.** `traveler.capability.created` is written with the journey id, so a
mid-trip capability change is traceable.

## 3. What does not work

**No recovery is proposed.** `replan_proposals: 0`. A traveller who has just been injured
mid-trip and declared a HARD step-free need receives no replan proposal, no alert, no
notification — nothing. The product records the fact and takes no action. Given that the same
capability would **block a fresh journey** with `422`, the asymmetry is stark: the need blocks
*new* planning but has no effect on the *running* journey.

**The already-selected plan is not re-evaluated.** Because
`generate_plans()`/`select_plan()` ignore the constraint set that
`_assert_selected_plan_feasible()` uses (see
`CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md` §3), the running plan continues to contain
activities that violate the new need, and no surface reports the violation.

**The experience surface is where the failure was visible.** At **Snapshot A**,
`GET /journeys/{id}/experience` returned **500** for a journey with a capability set:

```
NameError: name 'traveler_twin' is not defined   app/stay_mobility.py:923
```

At **Snapshot B** it returns **200** with `traveler_twin` present and
`experience_mentions_capability: true`. So the mid-trip recovery surface was completely broken
28 minutes before the end of this round and was fixed by Codex during it. Tag:
`NEW`, `FIXED_IN_CURRENT`.

Note the remaining gap: even at Snapshot B, `experience_mentions_review: false` — the
experience payload mentions the capability but not any review or conflict state.

## 4. Verdict table

| # | Finding | Result | Tag |
|---|---|---|---|
| 1 | Mid-trip HARD need requires explicit confirmation | **holds** (409 on `PUT`, 200 on `/confirm`) | — |
| 2 | Journey is not stranded by a mid-trip capability change | **holds** (stays `ACTIVE`) | — |
| 3 | Selected plan is not silently mutated | **holds** (`plans_mutated_silently: false`) | — |
| 4 | Mid-trip change is audited | **holds** (`traveler.capability.created`) | — |
| 5 | A replan is proposed when the running plan violates the new need | **VIOLATED** — `replan_proposals: 0` | `FINAL_V19` |
| 6 | The running plan is re-evaluated against the new need | **VIOLATED** — no surface reports the violation | `FINAL_V19` |
| 7 | The experience surface renders a capability-bearing journey | **VIOLATED at Snapshot A (500)** → **FIXED_IN_CURRENT at Snapshot B (200)** | `NEW`, `FIXED_IN_CURRENT` |
| 8 | The experience surface reports review / conflict state | **VIOLATED** — `experience_mentions_review: false` | `FINAL_V19` |

## 5. Recommendation (not applied)

1. After a mid-trip capability change on an `ACTIVE` journey, run the feasibility gate against
   the **running** plan and, on failure, raise a replan proposal through the existing Guardian
   path (which already exists — `POST /guardian/scan`, `/guardian/autopilot/*` — and is not
   wired to capability changes).
2. Surface the violation in `/experience` and `/twin` so the traveller is told, rather than
   silently continuing.
3. Add a regression test asserting that a mid-trip HARD capability change produces either a
   replan proposal or an explicit "no alternative" record — never silence.
