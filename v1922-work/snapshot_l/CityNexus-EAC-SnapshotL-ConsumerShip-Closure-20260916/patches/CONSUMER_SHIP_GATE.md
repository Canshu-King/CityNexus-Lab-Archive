# Consumer ship gate

After the scheduler/network fixes, backend archaeology stops.

## Required consumer features

### Booking import
Normal traveler UI:
- paste booking/confirmation text
- manual form
- screenshot/upload only if truthfully supported
- parsed preview
- editable fields
- explicit confirm

Raw Reservation JSON:
Advanced/Developer only.

### Activity detail
Keep the new screen, but:
- do not call arbitrary same-plan stops "nearby";
- show real coordinates/map when available;
- useful provider-backed details;
- replace/add/map/Copilot actions where implemented truthfully.

### Copilot
Default traveler view:
- useful Chinese response;
- current journey context;
- human actions;
- no What-if Studio / semantic envelope / policy jargon as primary content.

Advanced details may retain engineering information.

### Today
Replace generic:
`你的下一座城市，已被充分考虑`

with current-trip information:
- 厦门三天
- today's state
- next action
- alerts/bookings
- AI planning entry.

### Trips
Must show the real multi-day itinerary and selected stay without collapsing it
into a one-day placeholder.

### Live
Top half:
- now
- next stop
- route
- disruption
- recommended change
- user actions.

Mode/risk/evidence diagnostics go to Advanced.

### Me
Move `权限边界` and ADVISORY engineering concepts behind an advanced/settings
section.

## Full visible same-Xiamen acceptance

One fresh journey through visible browser UI:

create
-> AI planning request
-> real Xiamen candidates
-> select plan
-> multi-day itinerary
-> activity detail
-> hotel compare/select
-> itinerary still preserves day structure
-> booking import
-> Copilot place question
-> Xiamen map
-> start/live
-> explicit mutable POI disruption
-> material replan
-> accept through UI
-> final state consistent

Produce `VISIBLE_UI_TRACE.json`.

No `/demo/reset`.
No direct API substitution for user actions.
