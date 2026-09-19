# FINAL TRACE MAPPING

Every comparison below states the entity set, the filter, and the expected
cardinality. No claim of "consistent" is made without a defined mapping.

| # | Compared | Entity set / filter | Expected | Observed |
|---|---|---|---|---|
| 1 | journey | `journeys` row created by the wizard | exactly 1 | `d3f0cf26-7e62-47a7-8c39-111c61adeb95` |
| 2 | AI run | plans created by THIS run = ids not present before the run | >= 2 attributable new candidates | baseline=0, new=3, reported=3, id sets equal |
| 3 | plan selection | `journey.active_plan_version_id` after a visible "采用这个方案" | one of the new candidate ids | `53d340c6-9a03-5b18-86f2-53f0ef8609b3` |
| 4 | itinerary | Trips stop cards summed over every day button vs `active_plan.activities` | equal, because the itinerary lists every activity including structural rows | ui=14, backend=14 ([7,5,2]) |
| 5 | stay | `stay-options` where `status == SELECTED`, joined to `offers` by `external_offer_id` | property name + check-in + check-out all present | name=如家酒店 in=2026-11-06T06:00:00+00:00 out=2026-11-08T04:00:00+00:00 |
| 6 | booking | `wallet.reservations` | >= 1 confirmed row with reference, amount, origin | ref=E2E-XIAOMI-FINAL-1 amount=18000 origin=厦门北站 |
| 7 | Copilot | the assistant bubble after asking 鼓浪屿好玩吗？ in the visible dock | a useful Chinese answer OR an honest cannot-verify reply, with no raw enum/model vocabulary | answered=True, about the place=True, honest=True, raw leak=False |
| 8 | disruption + replan | `replans` proposal for a CLOSURE on the first mutable stop | material diff and locked commitments preserved | status=PRESENTED preserved=True -1/+1 |
| 9 | replan accept | `journey.active_plan_version_id` after a visible "接受新方案" | changed from the pre-disruption plan | before=1f0469d5-e40f-45d4-af6e-320190c2651e after=994ac179-64ae-4240-97fb-bddcab6ffa02 changed=True |
| 10 | locked truth | count of `activities.locked` before vs after the accepted replan | unchanged | before=6 after=6 preserved=True |
