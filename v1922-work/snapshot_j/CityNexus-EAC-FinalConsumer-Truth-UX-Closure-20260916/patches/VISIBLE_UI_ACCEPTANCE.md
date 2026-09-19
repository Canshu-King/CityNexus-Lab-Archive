# Visible UI acceptance

The final READY claim must be completed through the UI.

## Canonical flow

Fresh browser + fresh acceptance journey:

1. `/`
2. create Xiamen trip in Chinese
3. review Step 3 and confirm
4. tap "AI 帮我规划"
5. enter:
   `两个人去厦门，想去鼓浪屿、环岛路和中山路，不要太赶，想吃本地美食。`
6. see honest generation stages
7. see >= 2 genuinely different Xiamen candidates
8. select one through UI
9. Trips shows Xiamen POIs
10. open an activity detail
11. open hotel compare
12. choose a hotel
13. return to itinerary and prove Xiamen POIs were NOT erased
14. import a reservation through consumer UI
15. ask Copilot `鼓浪屿好玩吗？`
16. receive a useful human answer or a clear search action
17. map shows Xiamen
18. start/live the journey
19. inject a mutable-POI closure as the test fixture
20. Live shows a material replan
21. accept through UI
22. final Trips/Live state agrees with backend truth

## Evidence trace

Create `VISIBLE_UI_TRACE.json`.

Every entry:
- timestamp
- journey_id
- route
- user action
- visible text/result
- backend request status
- plan id when applicable

Backend setup calls are marked separately as fixture preparation and do not count as task completion.

## Forbidden acceptance shortcuts

- select plan directly through API and then claim UI selection passed;
- select hotel through API and then claim hotel UI passed;
- accept replan directly through API and then claim Live UI passed;
- use a different journey for any stage;
- use demo reset.
