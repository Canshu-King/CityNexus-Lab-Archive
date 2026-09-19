# Real-user product gate

After the narrow backend truth fixes, stop doing backend archaeology.

The next acceptance is a consumer-product acceptance.

## Must exist

- 3-step create trip
- AI planning input/progress
- real Xiamen plan comparison
- multi-day Trips UI
- activity detail
- hotel comparison + select
- hotel selection preserves itinerary
- consumer booking import
- useful Copilot
- Xiamen map
- Live disruption
- material replan
- accept through UI
- error/offline recovery

## Must be performed through visible UI

Critical user actions may not be replaced by direct API calls:
- create
- select plan
- select hotel
- import booking
- accept replan

## Chinese-first

Canonical acceptance screenshots should not expose:
- PlanVersion
- C4
- semantic envelope
- authority boundary
- NONESEARCH / UNKNOWN / UNVERIFIED
- raw JSON

These belong behind Advanced/Developer surfaces.

## Physical-device threshold

Only after the browser-visible chain passes may the user repeat it on the
Xiaomi 13 Ultra.

A route existing is not a feature completion.
