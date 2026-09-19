# REMAINING_PRODUCT_GAPS.md

Ordered by how much each blocks a real traveller.

## Blocking a READY verdict

1. **Hotel comparison and selection.** The 住宿 entry is reachable but there is
   no comparison of price / area / distance-from-itinerary / reason, and no
   selection that feeds the itinerary. Gate #11.
2. **Live disruption → governed replan.** Live opens, but nothing drives an
   Event (weather / closure / delay) into the traveller-language surface
   (发生了什么 / 哪些受影响 / 哪些不变 / 接受 / 仅调整今天 / 稍后提醒) and no
   replan is accepted end to end. Gate #19.
3. **AI planning needs a credential.** With `CITYNEXUS_AI_ENABLED=false` the
   planner returns `SKIPPED_EXTERNAL_DEPENDENCY` ("DeepSeek API key is not
   configured"). The honest failure branch is implemented and verified, but the
   success branch — AI producing real candidate plans — was **not** exercised.
   A run with a live key is required before the AI path can be called verified.

## Important but not blocking

4. **Activity detail screen** (reference 08): per-stop time/duration exist, but
   no dedicated screen with transit, cost breakdown and "why we recommend this".
5. **Order import**: upload a screenshot / paste reservation text / manual entry,
   then parse → review → user confirms → create the commitment. Today the inbox
   accepts pasted structured JSON. No commitment is created from uncertain OCR,
   which is correct, but the product shell is missing.
6. **Empty / failure matrix**: itinerary-empty, map-no-location,
   backend-unreachable and AI-unavailable are done. Still missing: DeepSeek
   unavailable inside Discovery, provider unavailable, no bookings, no plan on
   Today beyond the chooser, and per-route runtime errors.
7. **Today hero copy** is still partly generic ("Your next city, already
   considered", "STILL UP") and should answer 现在该做什么 / 下一步 / 有没有风险.
8. **Multi-day realism**: the itinerary groups by date and has a week strip, but
   no journey in this environment has more than one day, so the >7-day path was
   **not** exercised with real data.
9. **Remaining technical prose** in secondary screens ("provider evidence" and
   similar). The prohibited enums are gone; this is polish debt.

## Environment facts that shaped the run

* Backend ran against a throwaway SQLite database; the demo Journey was seeded
  via `/api/v1/demo/reset`.
* No DeepSeek key was configured for the browser session, so both the AI planner
  and Copilot ran on the conservative local fallback.
* Xiamen has no sealed provider fixture, so a newly created Xiamen Journey
  cannot produce plans in this environment; the reachable planning chain was
  exercised on the sealed Tianjin demo Journey.

## Explicitly out of scope this session

Frontend visual re-skinning beyond the corrections, OpenAPI changes (no API
contract changed), and any backend architecture work beyond the V19.2.5 hotfix.
