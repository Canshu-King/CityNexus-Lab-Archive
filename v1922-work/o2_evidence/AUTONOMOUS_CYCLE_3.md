# AUTONOMOUS CYCLE 3 — Input robustness

## Hypothesis
Repeated or hostile input cannot corrupt the product: double-tapping the primary
CTA, submitting the booking form twice, refreshing mid-AI-planning, very long or
emoji input, and repeatedly opening/closing Copilot all leave the state correct
and never duplicate a plan, a stay choice or a booking.

## Method
Driver: `cycle3_rerun.cjs` (Playwright + Chrome, mobile 390x844, `locale: zh-CN`).
All interactions through the visible UI. A first attempt (`cycle3.cjs`) ran while
another process reset the database mid-run, so this cycle was re-run on a stable
database and the re-run is the one reported here.

Steps driven:
1. 3-step wizard (厦门, 2026-11-06 10:00 → 2026-11-08 20:00, budget 3000 /
   stay 1000) → click **创建行程** twice as fast as the browser accepts.
2. Open AI sheet → **开始规划** twice (second click 300 ms after the first).
3. Open AI sheet → submit → **hard reload 2.5 s into planning**.
4. AI sheet with 660 characters (60× repeated Chinese + 30× emoji).
5. Copilot with 260 characters of emoji + Chinese.
6. Copilot edge toggled open/closed 8 times rapidly.
7. First hotel's **选择这家住宿** tapped twice.
8. Manual booking form (RAIL, C3-DOUBLE-0002) submitted twice.
9. Today's **AI 帮我规划** primary CTA tapped 5 times in a row.
10. Backend audit of plans / stay options / wallet / missions / audit log.

## Evidence

### No duplication anywhere (PASS)
```
1-create-double-tap   disabledAfterFirst=true  second=accepted  jid=46812fb0-…
2-places-available    n=8
2-ai-double-submit    busyDisabled=true  second=blocked(timeout: button disabled)
                      planCount=3  plans 0->3  uniqueIds=true
3-refresh-mid-ai      sheetBefore=1  afterReload={"sheet":0,"heading":"厦门之旅","stuckBusy":0}
                      plansNow=3  uniqueIds=true
4-long-emoji-ai       chars=660  planCount=3
5-copilot-long-emoji  chars=260  bubbles=2
6-copilot-toggle-x8   before=1  after=1  heading="厦门之旅"
7-hotel-double-tap    cards=10  second=accepted  chosenBadges=1  error=""
7-hotel-truth         SELECTED rows=1  names=Millenium Harbour View
8-booking-double-submit second=accepted  drafts=1  refVisible=1
9-cta-taps-x5         sheets=1
10-backend-audit      plans=7 uniqueIds=true versionNos=1..7 |
                      stayOptions=10 SELECTED=1 | reservations=0 commitments=0
page-errors           0 []
```
Backend confirmation for the same journey:
```
plan_versions  v1..v6 CANDIDATE INITIAL, v7 ACTIVE MANUAL   (no duplicate version_no)
journey_missions  ('COMPLETED', 3)      -> exactly one mission per AI submit (3 submits)
agent_runs        COMPLETED x3          -> no orphaned/duplicated runs
stay_journey_options  SELECTED = 1      -> double-tap did not select twice
external_reservation_drafts (1, READY_FOR_CONFIRMATION) -> one draft, not two
audit_logs  journey.created = 1         -> the double-tapped create button made ONE journey
```
The create button is disabled after the first tap (`disabledAfterFirst=true`) and
the AI submit button is disabled while busy (the second click timed out waiting
for an enabled button). Repeated primary-CTA taps produced exactly one sheet.

### Language of the AI summary
Two fresh submissions produced Chinese summaries:
```
首次到厦门，核心需求为看海、逛老街、看日落，并偏好轻松不赶的节奏；未提供预算或硬性时间约束。
已识别为厦门三天长辈同行行程，核心约束是少走路和每日下午休息；下午休息设为受保护安排，景点、餐饮和交通方式可调整。
```
An earlier run showed an English summary (`User wants a first-time Xiamen trip
f…`, `Compiled a 3-day Xiamen trip with parents…`) for a Chinese request. That is
model output variance from the upstream planner, not a deterministic UI defect;
it is recorded below as a risk rather than a defect.

### Environment note (not a product verdict)
The first `cycle3.cjs` run returned `planCount=0` with the honest copy
`没有生成可行方案 …你的行程没有被改动，可以调整预算或换个说法再试。` while
`GET /api/v1/places?city_code=CN-XIAMEN` returned `[]`. A separate process reset
the shared SQLite database mid-run (journey count dropped from 6 to 1 and back).
With places present the same flow returns `planCount=3`. The 0-plan path was
itself honest — it did not fabricate plans or claim success.

Screenshots: `shots/lab_3_01_create.png`, `lab_3_02_ai_double.png`,
`lab_3_03_refresh_mid_ai.png`, `lab_3_04_long_emoji.png`,
`lab_3_05_copilot_long_emoji.png`, `lab_3_06_copilot_toggle.png`,
`lab_3_07_hotel_double.png`, `lab_3_08_booking_double.png`,
`lab_3_ai_lang_1.png`, `lab_3_ai_lang_2.png`.

## Verdict: NOT_REPRODUCIBLE
No input-robustness defect reproduced. Every double-tap / double-submit /
mid-flight reload / extreme-input / repeated-toggle case left the state
consistent, and the product's guards (disabled buttons, single mission per
submit, one SELECTED stay) held.

## Fix
No code change in this cycle. (Cycle 1 and Cycle 2 changes were already in the
tree and were exercised by this run; `npx vite build` is clean.)

## Residual risk / what a real user trial should watch
* **Double-tap did create the journey once, but the button is only disabled
  client-side.** The create endpoint has no `Idempotency-Key` in the wizard path,
  so a genuinely flaky network (first request succeeds but the response is lost,
  user retries) could still create a second journey. The trial should try this on
  a real phone with airplane-mode toggling.
* The AI summary can come back in English for a Chinese request. On a Chinese
  screen that is a comprehension break for the traveller; a trial should sample
  many submissions and measure the rate.
* `POST /real-city/discover` returns
  `{"detail":"There was an error parsing the body"}` when the JSON body is sent
  with `curl -d` on Windows (body quoting), which made a first probe look like a
  400. It works with `--data-binary @file`. Worth checking how the phone client
  sends it.
* Refreshing mid-planning silently abandons the request with no "your request was
  interrupted" notice; the traveller has to notice the sheet is gone. A trial
  should watch whether people re-submit or assume it finished.
