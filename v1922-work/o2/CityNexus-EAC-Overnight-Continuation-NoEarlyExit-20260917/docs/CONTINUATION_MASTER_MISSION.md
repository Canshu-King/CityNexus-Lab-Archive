# CONTINUATION MASTER MISSION

Checkpoint O1 is a PARTIAL checkpoint, not the overnight result.

Resume from the current authoritative repository state.

Do not throw away completed work.
Do not restart Snapshot M from scratch.
Do not merely repackage the existing checkpoint.

==================================================
1. FIRST PRIORITY — COMPLETE THE SAME-XIAMEN UI FLOW
==================================================

The previous package explicitly says this was NOT completed.

Complete one fresh visible browser session:

1. open `/`
2. create a fresh Xiamen trip
3. finish Step 1 / 2 / 3
4. confirm
5. tap AI planning
6. enter natural-language request
7. observe honest planning stages
8. see >=2 genuinely distinct Xiamen candidate plans
9. compare
10. choose one through the UI
11. Trips shows a real multi-day Xiamen itinerary
12. open Activity Detail
13. open hotel compare
14. choose a hotel through the UI
15. prove POIs, day assignment, durations and locked truth remain intact
16. open booking import
17. paste confirmation text or use manual form
18. preview
19. confirm through the UI
20. prove booking appears in Trips
21. ask Copilot `鼓浪屿好玩吗？`
22. get a useful Chinese traveler answer or useful grounded search action
23. open map and verify Xiamen truth
24. enter Live
25. inject one explicitly targeted mutable-POI disruption fixture
26. see a material replan
27. accept through the UI
28. verify final Trips / Live / backend truth agree
29. switch 中文 -> EN -> 中文
30. hard refresh
31. browser back/forward
32. confirm same journey context survives

Produce:

`VISIBLE_UI_TRACE.json`

This is the top acceptance gate.

==================================================
2. TODAY / HOME
==================================================

The previous package still admits Today is generic.

Rebuild it around the active trip.

First viewport must show:
- Xiamen trip name;
- date span;
- current day / next action;
- today's plan summary;
- hotel / booking summary;
- disruptions or risks;
- AI planning / Copilot action.

Remove generic marketing filler.

==================================================
3. COPILOT
==================================================

The previous package admits `鼓浪屿好玩吗？` is still not useful.

Fix it.

Expected:
- useful Chinese answer;
- current-trip context;
- grounded place evidence when available;
- human actions:
  - 加入行程
  - 安排到第2天
  - 地图查看
  - 搜索更多

If verification is unavailable:
- say that plainly;
- offer a useful next action.

Default traveler UI must not show:
- semantic envelope;
- What-if Studio;
- policy jargon;
- raw internal enums.

==================================================
4. ME
==================================================

The previous package admits Me still shows:
- 权限边界
- ADVISORY
- RECORD_ONLY

Move these behind Advanced/Developer.

Normal Me:
- profile;
- preferences;
- documents;
- wallet/bookings;
- language;
- settings;
- Advanced entry.

==================================================
5. HOTEL PRODUCT QUALITY
==================================================

The previous package admits cards are not meaningfully differentiated.

Improve:
- real name;
- area/address;
- real itinerary relationship;
- arrival/departure fit;
- price when known;
- cancellation/breakfast when known;
- reason recommended.

Unknown remains unknown.

Do not fabricate differentiation.

Browser proof:
compare -> choose -> return to itinerary -> day structure preserved.

==================================================
6. LIVE TRAVELER-FIRST VIEW
==================================================

The previous package admits Live was not reworked.

First viewport must focus on:
- now;
- next stop;
- route summary;
- disruption;
- affected items;
- unchanged protected commitments;
- proposed adjustment;
- actions.

Move:
- transport-mode diagnostics;
- raw evidence;
- guardian internals;
- debugging state

behind Advanced.

==================================================
7. BUDGET SANITY
==================================================

Implement the missing advisory.

For extreme combinations such as:

39 days / 2 people / CNY 3000

show:
- approximate daily budget;
- warning;
- edit budget;
- continue intentionally.

Do not invent exact spend forecasts.

==================================================
8. BOOKING FLOW COMPLETION
==================================================

Checkpoint O1 only proved preview.

Complete:
preview -> confirm through browser -> booking appears in Trips / Today.

Test duplicate / incomplete input.

Never silently create an uncertain commitment.

==================================================
9. VISUAL IMPLEMENTATION
==================================================

Materially move the product toward the supplied 10-screen UI reference.

Do not settle for:
- browser-default controls;
- engineering-console layout;
- excessive empty space;
- giant diagnostic scrolls.

Prioritize:
- Today
- Trips
- Hotels
- Copilot
- Live
- Me
- Booking import

Capture before/after.

==================================================
10. FAILURE / HOSTILE FLOWS
==================================================

Checkpoint O1 admits these were not run.

Run:
- disconnect/reconnect backend during flow;
- refresh during AI loading;
- double-tap primary CTA;
- provider unavailable;
- stale/recovery state;
- GPS denied;
- AI disabled;
- empty trip;
- long trip;
- low budget;
- duplicate booking;
- incomplete booking;
- all primary tabs;
- repeated Copilot open/close.

Fix every P0/P1 found and rerun.

==================================================
11. DO NOT STOP AFTER FIRST PASS
==================================================

After the canonical flow passes, continue with the autonomous lab cycles.

No early packaging.
