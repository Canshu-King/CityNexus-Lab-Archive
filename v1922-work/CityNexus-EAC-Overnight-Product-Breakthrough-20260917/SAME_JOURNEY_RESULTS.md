# SAME_JOURNEY_RESULTS.md

## Status

**The full visible same-Xiamen chain was NOT completed as one browser session.**

Critical traveller actions may not be substituted by API calls, so this file
records exactly what was driven through the visible browser and what was not.
`VISIBLE_UI_TRACE.json` is deliberately **absent**: there is no truthful
full-chain trace to publish.

## Driven in the visible browser this round

One Xiamen journey (`b20dd368-e961-48b2-92ec-27f84b024625`), 390x844 and
430x932, Chinese locale:

| Step | Result |
| --- | --- |
| Open `/v8/trips` | renders |
| Itinerary tab | real stops rendered |
| Tap a stop -> Activity Detail | opens, real fields shown |
| Back to itinerary | works |
| 预订 tab -> 手动填写 | manual booking form opens |
| Submit manual booking | draft preview appears |
| `/v8/hub`, `/v8/map`, `/v8/agent`, `/v8/me`, `/v8/live` | render, no leaks |
| Horizontal overflow | none |
| Real page errors | **0** |

## Not driven

1. create a fresh Xiamen trip through the 3-step wizard in the browser;
2. AI planning request and honest planning stages;
3. candidate comparison and in-UI plan selection;
4. hotel compare and in-UI selection;
5. proof that itinerary days and durations survive hotel selection in the UI;
6. booking import confirm and the booking appearing in Trips;
7. `鼓浪屿好玩吗？` answered usefully;
8. start/live and the governed replan accepted through the UI;
9. 中文 -> EN -> 中文 switch and hard-refresh continuity.

## Evidence that exists

* `evidence/fe_final.json` - tab sweep, leak scan, activity detail, 0 errors.
* `evidence/fe_booking.json` - manual booking import interaction trace.
* `screenshots/after/` - Today, Trips, Map, Copilot, Me, Live, Activity Detail,
  manual booking form and booking preview.

## Why this is not a pass

The mission states: *READY is allowed only if the visible same-Xiamen flow
actually completes.* It did not.
