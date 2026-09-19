# WorkBuddy final targeted delta

Read-only.

Freeze Snapshot I:
CityNexus-EAC-RealCity-Product-Closure-20260916.zip

Do not modify main.

Validate only:

1. STAY PRESERVATION
   - real Xiamen selected plan POIs before stay
   - select stay
   - same POIs remain after reload
   - stay nodes added
   - no silent itinerary replacement

2. REPLAN MATERIALITY
   - unresolved CLOSURE must not yield F0_STABLE_COPY success
   - protected closure must not fake a repair
   - mutable Xiamen POI closure must yield material diff or NO_ALTERNATIVE
   - accepted proposal must materially differ from base when presented as a repair

3. VISIBLE UI TRACE
   - verify visible browser actions, not backend-only claims
   - same journey id throughout
   - no demo reset

4. COPILOT
   - no authority/semantic envelope/raw statuses in default traveler view
   - `鼓浪屿好玩吗` receives useful answer or useful search action

5. ORDER IMPORT
   - consumer text/manual -> preview -> confirm
   - raw JSON advanced only

6. ACTIVITY DETAIL
   - real screen exists and works

7. VISUAL
   - inspect screenshots, do not award pass for mere render
   - Today/Trips/Copilot/Hotels/Live materially improved
   - Chinese-first

Final:
BLOCKED
or
SNAPSHOT_ACCEPTED_FOR_XIAOMI_13_ULTRA_TRIAL
