# Mid-trip HARD recovery and stale-candidate lifecycle

Evidence: `evidence/lifecycle_a.json` (groups `midtrip`, `conflict`, `projection`),
`evidence/stale_candidates_a.json`, `evidence/stale_candidates_b.json`,
`evidence/feasibility_truth_a.json`.

---

## 1. Mid-trip HARD capability — the plan is safe, the trip is not

Sequence driven through the real HTTP surface on a live journey:

```
generate → 201 / 3 plans
select   → 200
start    → 200 / journey ACTIVE
PUT  /journeys/{id}/capabilities      → 409 "hard capability needs require /confirm"   ✅
POST /journeys/{id}/capabilities/confirm → 200 (STEP_FREE_REQUIRED, HARD, confirmed)   ✅
```

| Check | Result | Verdict |
|---|---|---|
| HARD capability requires explicit confirmation | 409 on PUT, 200 on confirm | ✅ |
| Capability mutation is audited | `audit_capability: ["traveler.capability.created"]` | ✅ |
| The active plan is not silently rewritten | `plans_mutated_silently: false`; plan signatures byte-identical before/after | ✅ |
| Journey stays consistent | `journey_status_after_capability: "ACTIVE"` | ✅ |
| **A governed consequence is produced** | **`replan_proposals: 0`** | ❌ |
| **The traveller is told the trip needs review** | **`experience_mentions_review: false`** | ❌ |
| The experience surface knows about the capability | `experience_mentions_capability: true`, `experience_status: 200` | ✅ |

**A HARD accessibility need declared mid-trip has no effect on the trip.** The journey keeps
running on the old plan, no `ReplanProposal` is created, and `/experience` never signals that
review is needed. This is the V19.1 round's P0-6, unchanged. Label: **STILL_REPRODUCIBLE**.

The "don't silently rewrite" guard is correct and should stay. What is missing is the *positive*
half: the system should surface the conflict and offer a governed replan, not stay quiet.

## 2. Capability ↔ C4 conflict

`evidence/lifecycle_a.json` → `conflict`:

| Check | Result |
|---|---|
| C4 commitment seeded | `C4_Anchored / ACTIVE`, `semantic_key: ea06631e-…` |
| Commitment survives the failed generation | `commitment_survived: true` ✅ |
| Conflict surfaces mention the capability | `mentions_step_free: false`, `mentions_accessibility: false` ❌ |
| Conflict surfaces mention the commitment | `mentions_commitment: false` ❌ |
| `generate` body names the cause | `names_capability: false`, `names_commitment: false`, `failures: []` ❌ |

Two independent HARD requirements — a confirmed anchor and a confirmed accessibility need — can
both block planning, and the client is told neither.

## 3. Stale candidate lifecycle

`evidence/stale_candidates_a.json`. Technique: generate plans, then rewrite a plan's frozen
`mobility_evidence_json` directly in the lab's own throwaway database, in four shapes.

### Candidate path — **PASS**

| Staleness shape | `POST /plans/{id}/select` | Message |
|---|---|---|
| evidence expired | **409** | `STALE_RECOMPOSE_REQUIRED: PlanVersion evidence expired` |
| `snapshot_id` removed | **409** | `STALE_RECOMPOSE_REQUIRED: PlanVersion has no frozen provider evidence` |
| `snapshot_id` inconsistent with the column | **409** | `STALE_RECOMPOSE_REQUIRED: PlanVersion evidence reference is inconsistent` |
| `expires_at` not a timestamp | **409** | `STALE_RECOMPOSE_REQUIRED: PlanVersion evidence timestamp invalid` |

`all_shapes_refused: true` ✅ — and each shape gets a *distinct, accurate* message rather than a
generic failure. `stale_candidate_refused: true` ✅.

### Selected / started path — **FAIL**

| Check | Result |
|---|---|
| Select a fresh plan | 200 ✅ |
| Expire that plan's evidence | mutated |
| Booking-path revalidation (`validate_selected_plan_feasibility`) | **raises** `ValueError: STALE_RECOMPOSE_REQUIRED: PlanVersion frozen mobility evidence expired` ✅ |
| `POST /journeys/{id}/start` | **200** ❌ |
| `journey_status` | **ACTIVE** ❌ |
| `/experience` flags the staleness | **false** ❌ |
| `journey_still_running_on_expired_evidence` | **true** ❌ |

So the system correctly refuses to *offer* a stale candidate, and the booking path correctly
refuses to *sell* against one — but a journey can be **started and kept running** on a plan whose
provider evidence has already expired, with nothing in the UI saying so.

For a shadow trial this is a direct safety problem: the traveller walks a real city using
mobility facts the system itself considers expired. Label: **STILL_REPRODUCIBLE** (the V19.1
round reported the same lifecycle gap).

Identical on Snapshot B (`evidence/stale_candidates_b.json`).

## 4. Exact reproduction

```
cd D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915
python tools/sync_tests.py A
python tools/v191_probe_lifecycle.py A        # midtrip / conflict / projection groups
python tools/v192_probe_stale_candidates.py A
```

## 5. What Codex should do

1. **Mid-trip HARD → governed consequence.** On confirming a HARD capability for an ACTIVE
   journey, re-evaluate the active plan and either emit a `ReplanProposal` or an explicit
   no-alternative / conflict state, and expose it on `/experience` and `/twin`.
2. **Name the blocker in the `generate` 422.** Carry the concrete failure codes
   (`LOCKED_COMMITMENT_LOST:<key>`, `ACCESSIBILITY_UNVERIFIED:<location>`, …) into the body.
3. **Refuse `/start` on expired evidence.** `start_journey` should apply the same
   `STALE_RECOMPOSE_REQUIRED` gate that `select` already applies, or mark the journey as degraded
   and say so.
4. **Surface staleness in `/experience`** so the phone can tell the traveller to re-sync.
