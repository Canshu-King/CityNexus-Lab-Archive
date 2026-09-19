# VISIBLE UI ACCEPTANCE

The final run is accepted only if the user task completes through visible UI.

Canonical request:

`我和朋友两个人去厦门，想去鼓浪屿、环岛路和中山路，不要太赶，想吃本地美食，也想住交通方便、性价比高的酒店。`

Expected chain:

Create Xiamen
-> AI planning
-> compare Xiamen plans
-> select
-> multi-day itinerary
-> activity detail
-> hotel compare/select
-> itinerary remains intact
-> booking import
-> Copilot
-> map
-> live
-> targeted disruption
-> material replan
-> accept
-> final state consistent

The same `journey_id` must remain throughout.

Forbidden shortcuts:
- `/demo/reset`
- demo Tianjin journey
- direct API plan selection
- direct API hotel selection
- direct API booking confirmation
- direct API replan acceptance

APIs may:
- inject an explicit disruption test fixture;
- inspect final state;
- prepare controlled external failure conditions.

They may not substitute for the traveler action being tested.
