# Product finish gate

After M1–M4 are closed, stop backend archaeology.

The next meaningful work is consumer product completion.

## Consumer booking import

Normal UI:
- paste booking/confirmation text;
- manual form;
- screenshot/upload only if actually supported;
- parsed preview;
- editable extracted fields;
- explicit confirm;
- booking/commitment created only after confirmation.

Raw Reservation JSON:
Advanced/Developer only.

## Today

Replace generic marketing copy with actual current-trip state:
- Xiamen journey;
- date/day;
- next action;
- booking/risk summary;
- AI planning/replan entry.

## Trips

Show a real multi-day itinerary.
Do not accept a synthetic one-day "厦门景点0/1/2/3" fixture as product proof.

## Copilot

For `鼓浪屿好玩吗？`:
- useful Chinese answer from live provider/AI when available;
- current-trip context;
- human action buttons;
- no What-if Studio / semantic/policy jargon as primary UI.

## Me

Move:
- 权限边界
- ADVISORY
- RECORD_ONLY
- engineering delegation state

behind Advanced/Developer settings.

Normal Me:
- profile
- travel preferences
- documents
- wallet/bookings
- settings.

## Live

First viewport:
- where I am / current stop;
- next stop;
- actual route summary;
- disruption;
- proposed change;
- accept/adjust/remind.

Move mode diagnostics, evidence and guardian details behind Advanced.

## Budget sanity

Very low daily budget for a long trip should produce an advisory warning.

## Full visible same-Xiamen acceptance

One fresh journey, UI only for critical actions:

create
-> natural-language AI planning
-> real Xiamen candidate plans
-> choose
-> multi-day Trips
-> Activity Detail with real coords
-> hotel compare/select
-> same itinerary survives
-> consumer booking import
-> useful Copilot answer
-> Xiamen map
-> Live
-> explicit mutable POI disruption
-> material replan
-> accept in UI
-> final truth consistent.

Produce:
`VISIBLE_UI_TRACE.json`

No `/demo/reset`.
No API substitution for user actions.
