# AUTONOMOUS CYCLE 1 — State integrity across reload / navigation

## Hypothesis
The traveller's chosen plan and chosen hotel survive a hard refresh, browser
back/forward, and re-entering each tab, and no two surfaces (Today / Trips /
Live / backend) show contradictory readings of the same trip.

## Method
Driver: `D:\moodle\_v1922_work\cycle1.cjs` then `cycle1_reverify.cjs`
(Playwright + Chrome, viewport 390x844, `locale: zh-CN`, mobile/touch).
All state changes went through the visible UI. Journey created with the real
3-step wizard (厦门, 2026-11-06 10:00 → 2026-11-08 20:00, budget 3000 / stay 1000);
plans produced by the real AI sheet; the plan chosen with "采用这个方案"; the
hotel chosen from the live OSM stay list.

Steps driven:
1. wizard → AI plan → compare → choose plan → choose hotel (live OSM).
2. Read Today, Trips, Trips·Stay, Map, then Today again (no reload).
3. Hard-refresh (`page.reload`) on `/v8/trips`, `/v8/hub`, `/v8/live`.
4. Build a 3-deep history, `goBack()` ×3 then `goForward()` ×3.
5. Re-read the backend `/experience` and `/stay-options` and compare plan id,
   full activity-id list and SELECTED stay id with the baseline taken before.

Timezone probe (`cycle1b_tz.cjs` / `verify_tz.cjs`): the same journey opened in
browser contexts with `timezoneId` Asia/Shanghai, UTC and America/New_York, and
Today vs Trips vs Live compared for the *same* stop.

## Evidence

### What held (PASS)
* Plan id, all 14 activity ids and the SELECTED stay id were byte-identical
  before and after the whole navigation/refresh sequence:
  `integrity => planSame=true stopsSame=true staySame=true`
* Hard refresh was stable on all three surfaces:
  `refresh-trips => before={"tripsStops":7,"firstStopClock":"10:00",...} after={"tripsStops":7,"firstStopClock":"10:00",...}`
  `refresh-hub => before/after todayStay="厦门磐基酒店"`
  `refresh-live => before/after liveCurrent="厦门高崎国际机场"`
* Back/forward walked the real history, no blank screen:
  `back-forward => /v8/hub -> /v8/trips -> /v8/hub -> /v8/trips -> /v8/hub -> /v8/live`
* Map re-entry rendered a panel: `map => panels=1`; `0 page errors`.

### DEFECT found — the same stop read 02:00 on Today and 10:00 on Trips
Baseline run (`cycle1.cjs`, journey `dd2d8d72-…`), before any fix:

```
hub-read  => {"today_stay":"汉庭酒店",
              "today_next":"下一步 | 02:00 厦门高崎国际机场 | 今天没有安排 …"}
trips-read=> {"trips_stops":7}
trips first stop (TripItinerary):  10:00 | 10:20 | 厦门高崎国际机场
```

Backend truth for that stop (verbatim `/experience` excerpt):

```json
{"start_at":"2026-11-06T02:00:00+00:00","end_at":"2026-11-06T02:20:00+00:00",
 "title":"厦门高崎国际机场","locked":true}
```
journey `timezone = "Asia/Shanghai"`.

Timezone probe, before the fix (`cycle1_tz_result.json`):

```
Asia/Shanghai       today.when = "11月6日 10:00 — 11月8日 20:00" ; today.next = "02:00 厦门高崎国际机场" ; trips.firstStop = "10:00 …"
UTC                 today.when = "11月6日 02:00 — 11月8日 12:00" ; today.next = "02:00 …"                     ; trips.firstStop = "10:00 …"
America/New_York    today.when = "11月5日 21:00 — 11月8日 07:00" ; today.next = "02:00 …"                     ; trips.firstStop = "10:00 …"
```

Root cause (frontend): `Hub` sliced the raw ISO string instead of formatting
the instant in the journey's time zone —
`nextStop.start_at.slice(11, 16)` → `"02:00"`, and
`new Date().toISOString().slice(0,10)` / `start_at.slice(0,10)` for "today" —
while `TripItinerary`/`ActivityDetail` correctly used
`Intl.DateTimeFormat(..., { timeZone })` → `"10:00"`. Two surfaces therefore
disagreed about the same locked stop, and the trip's own start/end and anchors
were rendered in the *device's* zone, so a traveller abroad saw a different
day and hour for their trip than the itinerary showed.

Screenshots (pre-fix): `shots/lab_1_01_today_after_choose.png`,
`shots/lab_1_tz_Asia-Shanghai_hub.png`, `shots/lab_1_tz_UTC_hub.png`.

## Verdict: CONFIRMED_DEFECT

## Fix
File: `frontend/src/app/V8Experience.tsx` (function `Hub`, plus two new
module-level helpers). One file, no backend change.

* Added `clockInZone(value, timeZone)` and `dateKeyInZone(value, timeZone)`
  (Intl-based, with a raw-slice fallback only inside `catch`) and
  `dateInZone(value, locale, timeZone)`.
* `Hub`: `todayKey` is now the journey-local date, `todayStops` compares
  journey-local dates, and `nextClock` uses `clockInZone(..., journeyTz)`.
* `Hub` trip range and both anchors now use `dateInZone(..., journeyTz)`
  (`data.journey.timezone || "UTC"`).
* `Live` "now" clock, "leave by / arrive by" and ETA now use the journey zone
  as well, so Live can never disagree with Trips.

Diff: 69 added / 10 removed lines in `V8Experience.tsx`.

### Re-verification (after fix, same journey id, fresh run `cycle1_reverify.cjs`)
```
hub   => {"todayWhen":"11月6日 10:00 — 11月8日 20:00 · 2 位旅行者 · 3 天",
          "todayNext":"下一步 | 10:00 厦门高崎国际机场 | 今天没有安排 …",
          "todayStay":"厦门磐基酒店"}
trips => {"tripsStops":7,"firstStopClock":"10:00"}
live  => {"liveCurrent":"厦门高崎国际机场","liveClock":"10:00"}
integrity => planSame=true stopsSame=true staySame=true
```
Timezone matrix after fix (`cycle1_fix_verify.json`) — Today, Trips and Live
now agree in every device zone, and the trip reads in the city's clock:
```
Asia/Shanghai     Today 11月6日 10:00–11月8日 20:00 | next 10:00 | trips 10:00 | live 10:00
UTC               Today 11月6日 10:00–11月8日 20:00 | next 10:00 | trips 10:00 | live 10:00
America/New_York  Today 11月6日 10:00–11月8日 20:00 | next 10:00 | trips 10:00 | live 10:00
```
Screenshots after fix: `shots/lab_1_reverify_01_hub.png`,
`shots/lab_1_reverify_02_trips.png`, `shots/lab_1_fixed_UTC_live.png`.
`0 page errors` in both runs.

## Residual risk / what a real user trial should watch
* `formatMinorMoney` / money helpers were not re-audited for zone issues; only
  instants were.
* `OfflineJourneyView` (the read-only saved snapshot shown when the backend is
  unreachable) still formats `next_24h` timestamps with the device-zone `date()`
  helper. It has no journey timezone in its payload, so it can disagree with
  Today while offline. Worth watching in the offline trial.
* Wallet booking rows also use device-zone `date()`; they were outside this
  cycle's hypothesis but are the same class of bug.
* A real user trial should watch: does a traveller who crosses a timezone
  mid-trip still see their own trip days, and do notifications (which carry
  absolute instants) land on the same wall-clock the app shows?
