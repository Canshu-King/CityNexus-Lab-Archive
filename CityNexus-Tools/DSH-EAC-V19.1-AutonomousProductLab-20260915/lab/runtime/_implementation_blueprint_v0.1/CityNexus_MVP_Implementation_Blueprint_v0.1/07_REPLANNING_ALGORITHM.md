# 07 - Core Replanning Algorithm Specification

## 1. Purpose

Replanning transforms the currently active PlanVersion into one or more feasible alternatives after a new Event or user change, while protecting commitments and keeping the decision explainable.

The algorithm follows the source-backed ordering:

```text
Reality / verified context
        -> deterministic feasibility
        -> commitment protection
        -> candidate scoring
        -> optional AI ranking/explanation
        -> user confirmation
```

AI must not be used to decide whether a hard constraint is satisfied.

## 2. Inputs

`ReplanContext`:

- Journey
- active PlanVersion
- current time
- current/completed Activity prefix
- active/future Activities
- active Constraints
- active Commitments
- triggering Event(s)
- verified Place/CityService availability snapshot
- Mobility estimates
- budget state / sunk and future cost
- Traveler Preferences
- planning_mode
- optional AI adapter status

## 3. Outputs

One `ReplanProposal` containing:

- base plan id
- proposed plan id
- triggering event id
- hard-gate booleans
- score breakdown
- total score
- structured plan diff
- deterministic reasons
- optional AI-polished explanation
- proposal status

If no candidate passes the hard gates, return a structured infeasibility result. Never fabricate a feasible proposal.

## 4. Non-negotiable invariants

A candidate is ineligible for scoring/selection if any of the following is false:

1. All HARD constraints pass.
2. All LOCKED commitments are preserved.
3. Activities do not overlap.
4. Travel time fits between activities.
5. Each scheduled activity is available/open for its interval.
6. The candidate stays inside the Journey start/end boundary.
7. A hard budget limit is respected when represented as a HARD constraint.
8. Completed activities and historical facts are not rewritten.
9. The proposed plan is derived from the current active plan version, not a stale superseded version.

## 5. Snapshot and partition

Before generating alternatives:

1. Read the current active PlanVersion.
2. Build a `RealitySnapshot` from verified/mock providers.
3. Partition activities into:
   - `historical_prefix`: COMPLETED or already elapsed/immutable;
   - `protected_future`: activities bound to LOCKED commitments;
   - `mutable_future`: remaining future activities.
4. Apply triggering event effects to availability and travel estimates.
5. Mark directly disrupted activities.

The historical prefix is copied exactly to all proposal plans.

## 6. Candidate-generation families

Generate a bounded, deterministic candidate set. For MVP, use these families in this order:

### F0 - Minimal shift
Keep the same activities; shift mutable times only if this restores feasibility.

### F1 - Local replacement
Replace each disrupted mutable activity with one compatible available Place/CityService matching preferences and duration window.

### F2 - Resequence mutable activities
Reorder nearby mutable activities while keeping protected commitments fixed.

### F3 - Drop optional activity
Remove the lowest-value non-committed activity if necessary to regain time feasibility.

### F4 - Conservative fallback
Keep only historical prefix + protected commitments + required transit/buffer, producing a sparse but feasible plan.

Do not use combinatorial brute force over every place. Cap alternatives per disrupted slot (suggested engineering default: 5) and retain a bounded number of candidates (suggested default: 20) before scoring.

The numerical caps above are engineering defaults, not source requirements.

## 7. Planning-mode effect

Do not silently alter the source-backed score weights. Planning mode influences candidate generation/pre-filtering:

- `balanced`: use all families normally.
- `budget`: prefer lower-cost replacements and drop expensive optional activities earlier.
- `explore`: generate more novel alternative Places while still passing all hard gates.
- `strict_schedule`: prefer minimal-shift/local-replacement families and reject high schedule drift earlier.

## 8. Deterministic feasibility evaluation

For each candidate:

```text
check journey boundary
check activity ordering / overlap
check provider availability
check travel feasibility
check HARD constraints
check budget hard constraint
check LOCKED commitment preservation
```

Return explicit failure codes, e.g.:

- `HARD_CONSTRAINT_VIOLATION`
- `LOCKED_COMMITMENT_LOST`
- `ACTIVITY_UNAVAILABLE`
- `TRAVEL_TIME_INFEASIBLE`
- `JOURNEY_WINDOW_EXCEEDED`
- `BUDGET_EXCEEDED`

Only candidates with zero hard failures reach scoring.

## 9. Contextual Journey Utility Score

Every component is normalised to `[0,1]`.

```text
score =
  0.24 * commitment_preservation
+ 0.18 * stability
+ 0.15 * time_reliability
+ 0.12 * preference_fit
+ 0.10 * mobility_fit
+ 0.08 * budget_fit
+ 0.07 * robustness
+ 0.06 * opportunity_value
```

### Component definitions for MVP

These definitions are implementation proposals that operationalise the source-backed component names and weights.

#### commitment_preservation

- 1.00 when all active commitments are preserved unchanged.
- LOCKED loss is a hard failure and never scored.
- For RESERVED/PAID non-locked commitments, deduct proportionally for cancellation, rescheduling or monetary loss.

Suggested formula:

```text
1 - weighted_commitment_change_cost / max(weighted_commitment_value, 1)
```

Clamp to `[0,1]`.

#### stability

Measure how much of the future base plan remains unchanged.

```text
1 - normalized(edit_count + schedule_shift_penalty)
```

Preserving activity identity/order/time produces a higher value.

#### time_reliability

Penalise plans with little buffer around transport and fixed commitments. A plan with adequate buffer and no lateness risk approaches 1.0.

#### preference_fit

Weighted average match between candidate activities and stored Traveler Preferences.

#### mobility_fit

Reward lower travel burden and compatibility with mobility preferences/constraints.

#### budget_fit

If under budget:

```text
1 - future_cost / max(budget_remaining, 1)
```

clamped and transformed so lower cost scores higher. If a HARD budget is exceeded the candidate is rejected before scoring.

#### robustness

Reward buffer, multiple nearby alternatives and lower dependency on fragile optional providers.

#### opportunity_value

Reward useful alternatives created by the changed context without violating stability/commitment rules.

## 10. Stable deterministic tie-breaking

If two candidates have equal score within `1e-9`, rank by:

1. fewer commitment changes;
2. fewer activity replacements/removals;
3. lower total schedule shift minutes;
4. lower future cost;
5. lower total travel minutes;
6. lexicographically smaller canonical candidate fingerprint.

This makes tests reproducible.

## 11. Explanation generation

Always construct a deterministic structured explanation first:

```json
{
  "summary": "One future activity was replaced because it became unavailable.",
  "reasons": [
    "Tech Art Center is closed during the planned visit.",
    "The locked river-cruise commitment remains at 15:30.",
    "The replacement remains within the journey budget and time window."
  ],
  "changes": [...],
  "preserved_commitments": [...]
}
```

If AI is available, it may rewrite this into friendlier language, but the structured reasons remain the verified source.

## 12. Proposal acceptance

Proposal generation does not change the active plan.

On user acceptance, in one transaction:

```text
assert proposal.status == PRESENTED
assert journey.active_plan_version_id == proposal.base_plan_version_id
re-run fast feasibility against latest snapshot
mark old plan SUPERSEDED
mark new plan ACTIVE
update journey.active_plan_version_id
mark proposal ACCEPTED
refresh JourneyTwin
write audit log
```

If the base plan changed, return `409 STALE_REPLAN_PROPOSAL` and invalidate the proposal.

## 13. Graceful degradation

- AI unavailable: use deterministic ranking and template explanation.
- Optional city recommendation provider unavailable: use cached/mock verified catalog if freshness policy permits; otherwise omit optional discovery choices.
- Payment/booking provider unavailable: do not invent confirmation. Preserve known commitments and report provider degradation.
- Mobility data unavailable: use deterministic mock/cached estimate only if the active environment explicitly allows it; mark JourneyTwin DEGRADED.

## 14. Canonical MVP acceptance scenario

The fixture in `mock/demo_journey.json` + `mock/events.json` must demonstrate:

- active plan contains Tech Art Center;
- 15:30 River Cruise has a LOCKED commitment;
- closure makes Tech Art Center infeasible;
- at least one candidate replaces/drops it;
- River Cruise remains unchanged;
- hard gates pass;
- all eight score components are present;
- user accepts proposal;
- new PlanVersion becomes active;
- same flow works with AI disabled.
