# CityNexus Real-City Product Closure Road-Prep

## Frozen input

Freeze the submitted EAC overnight result as **Snapshot H**:

`CityNexus-EAC-Overnight-Mobile-Product-Rescue-V2-20260916.zip`

Its self-verdict is correctly conservative:

`BLOCKED_FOR_REAL_USER_TRIAL`

The package made meaningful structural progress, but it does **not** yet prove
the product works end-to-end for the actual newly-created Xiamen journey.

## Why another focused closure is needed

The next round is not another broad architecture sprint.

It must close exactly three kinds of gap:

1. **Same-journey real-city continuity**
   - Create Xiamen
   - Plan Xiamen
   - Compare Xiamen candidates
   - Adopt Xiamen plan
   - Show Xiamen itinerary/map/hotels
   - Live/replan the same Xiamen journey
   - Never switch to the sealed Tianjin demo for acceptance evidence

2. **Missing traveler features**
   - real hotel compare/select
   - live disruption -> governed replan
   - order import confirm flow
   - activity detail

3. **Actual product UI**
   - current implementation is functional but still visually/declaratively close
     to the old engineering console
   - implement the prior 10-screen UI reference direction instead of merely
     reorganising the existing CSS

Read:

- `docs/INDEPENDENT_AUDIT.md`
- `docs/SAME_JOURNEY_PROOF.md`
- `docs/UI_CLOSURE_SPEC.md`
- `docs/EAC_NEXT_MISSION.md`
- `docs/WORKBUDDY_DELTA_PROMPT.md`
