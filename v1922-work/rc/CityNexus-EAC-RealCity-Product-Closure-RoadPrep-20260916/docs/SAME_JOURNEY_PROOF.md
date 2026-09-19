# SAME_JOURNEY_PROOF

The next READY claim must prove one continuous traveler journey.

## Canonical acceptance scenario

Create through visible UI:

- destination: 厦门
- city_code: must remain Xiamen-specific
- 2 travelers
- realistic 3–5 day acceptance dates preferred
- budget: choose a value compatible with a real test trip, or explicitly prove
  budget-overrun handling
- arrival: 厦门高崎国际机场
- departure: 厦门北站

Use a single `journey_id`.

Record the id once after creation.

Every subsequent browser/API artifact used for acceptance must reference that
same id.

## Required chain

1. create Xiamen Journey
2. natural-language request
3. DeepSeek/live semantic success if configured
4. real Xiamen provider/place results
5. generate >= 2 genuinely different Xiamen candidate plans
6. compare candidates
7. choose one
8. itinerary contains Xiamen places
9. map contains Xiamen coordinates, or a truthful missing-data state before
   coordinates arrive
10. compare/select an Xiamen stay
11. import or confirm one reservation through traveler UI
12. start/live the same Journey
13. inject or receive a disruption
14. create governed replan
15. traveler sees affected / unchanged / proposed changes
16. accept replan
17. selected/active plan and recovery state update consistently

## Forbidden acceptance shortcuts

- `/api/v1/demo/reset`
- sealed Tianjin plan after creating Xiamen
- switching journey ids without making that visible in the report
- manually injecting a PlanVersion from a different journey
- declaring Copilot success using only conservative fallback when the READY claim
  depends on live AI
- calling "hotel PASS" because the button exists
- calling "replan PASS" because Live route opens

## Evidence required

Create `SAME_JOURNEY_TRACE.json` containing at minimum:

- timestamp
- route/screen
- journey_id
- city_code
- active/selected plan id
- action
- backend response status
- visible user result

A reviewer must be able to prove the entire chain never switched journeys.
