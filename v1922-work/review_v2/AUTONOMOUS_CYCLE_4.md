# AUTONOMOUS CYCLE 4 — Cross-surface agreement after disruption + replan + accept

## Hypothesis
After a disruption, a governed replan and an accepted replan, Trips, Live, the
map and the backend all agree on the same stops and times, and no pinned/locked
commitment is ever silently moved or dropped.

## Method
Driver: `cycle4_clean.cjs` (final, clean run) plus `cycle4b.cjs`,
`probe_post_accept_agreement.cjs`, `probe_refusal_ux.cjs`,
`probe_after_accept.cjs`, `probe_replan_diag.cjs` (Playwright + Chrome, mobile
390x844, `locale: zh-CN`).

Flow driven through the visible UI: 3-step wizard (厦门, 2026-11-06 10:00 →
2026-11-08 20:00, budget 3000 / stay 1000) → AI planning → choose a plan →
choose a live OSM hotel → raise a CLOSURE on one stop (the traveller cannot type
an event into a phone, so this is the one out-of-band step) → governed replan →
traveller sees the proposal on Live → taps 接受新方案 → read Trips / Live / map /
Today / backend.

Comparison was done at the **instant** level (`Date.parse`), not by comparing
ISO strings: the same instant is written as `+00:00` before a replan and `+08:00`
after it, so a naive string diff reports every commitment as "moved".

## Evidence

### No locked commitment moved or dropped (PASS)
```
5-before          plan=ccab62c0-… n=14 locked=6
7-proposal        preserved=true removed=1 added=0 moved=6
10-backend        plan=3c6ed5a2-… changed=true n=13 acceptedStatus=ACCEPTED
                  lockedBefore=6 lockedAfter=6
11-locked-check   lockedSame=true missingLocked=[]
```
All six locked commitments are byte-identical at the instant level, before and
after the accept:
```
before: 厦门高崎国际机场@2026-11-06T02:00:00+00:00   after: @2026-11-06T10:00:00+08:00   (same instant)
        Check in · 7天酒店@…06:00:00+00:00          after: @…14:00:00+08:00
        Overnight · 7天酒店@…14:30:00+00:00 (x2)   after: @…22:30:00+08:00
        Check out · 7天酒店@…04:00:00+00:00        after: @…12:00:00+08:00
        厦门北站@2026-11-08T11:50:00+00:00          after: @2026-11-08T19:50:00+08:00
```
`locked_commitments_preserved=true` from the backend, and Live told the traveller
the same thing: `已确认的预订和到达/离开时间保持不变。`

### Trips and the backend agree (PASS)
The earlier apparent mismatch (`tripsStops=7 backendStops=14`) was my harness
counting only the visible day. Walking every day chip gives an exact match:
```
perDay [6,5,2]  totalStops=13  backendStops=13   (and [7,5,2]=14 in another run)
```
`missingOnTrips=[]`. The map still renders a real canvas after the replan
(`panel=1 canvas=1`), and a hard refresh on Live does not re-offer the accepted
proposal (`proposals=0`).

### DEFECT — a handled disruption kept being counted as "needs attention"
After accepting the replan the backend event becomes `ACKNOWLEDGED` and no
proposal is pending, yet Today and the notification badge kept escalating it:

```
backend : active_plan.disruptions = 1 (CLOSURE, status ACKNOWLEDGED)
          events = [CLOSURE:ACKNOWLEDGED]
          replans = [ACCEPTED, INVALIDATED, INVALIDATED]

BEFORE FIX, stable across 3 rounds:
Today : attention "1 项变化"   alerts "通知 · 1 条活跃"
        next "… 需要关注 1 项变化 打开「实时行程」查看"
Live  : banner "发生了什么 有一处地点临时关闭"
        "当前没有需要你决定的调整。"      <- nothing to decide
```
Two surfaces contradicted each other on the same data: Today said the trip
needed attention, Live said there was nothing to decide. With several
disruptions raised it became `8 项变化` / `通知 · 8 条活跃` while every one of
those events had either an accepted or an invalidated proposal behind it.

Root cause: `LiveRecovery` only shows the "handled" notice when
`disruptions.length === 0`, but `_active_plan_payload` returns events in
`("DETECTED", "ACKNOWLEDGED")` and this product deliberately treats
acknowledgement as **not** resolution (`backend/app/planning/hard_recovery.py`
invariant 1). An accepted replan therefore leaves its trigger event
`ACKNOWLEDGED` in the payload forever, so the condition could never become true,
and `Hub`/the alert badge counted every event in that list as open.

Screenshots (pre-fix): `shots/lab_4d_round1_hub.png`,
`shots/lab_4d_round1_live.png`, `shots/lab_4e_hub.png`, `shots/lab_4e_live.png`.

## Verdict: CONFIRMED_DEFECT

## Fix
1. **`backend/app/stay_mobility.py`** (`_active_plan_payload`) — each entry in
   `disruptions` now carries `status` and `resolved_at` alongside the existing
   fields. The plan payload still lists the event (acknowledgement is not
   resolution); it just no longer hides whether the traveller already acted on
   it.
2. **`frontend/src/app/v8Types.ts`** — `active_plan.disruptions[]` gained
   optional `status` and `resolved_at`.
3. **`frontend/src/app/V8Experience.tsx`** — one shared
   `isHandledDisruption(item)` predicate (an event is handled when its status is
   `ACKNOWLEDGED`/`RESOLVED`/`IGNORED`, it has a `resolved_at`, or it is the
   trigger of an **ACCEPTED** replan read from `/replans`). The shell splits
   `allDisruptions` into `disruptions` (open) and `handledDisruptions`; the
   notification badge, the alert popover and Live's guardian line use the open
   list; `Hub` uses the same predicate and now answers 已处理 / "The earlier
   change has been handled" instead of 一切正常, so a handled event is
   acknowledged without being escalated.
4. **`frontend/src/features/execution/LiveRecovery.tsx`** — `Disruption` gained
   `status`/`resolved_at`; the "what happened" banner shows only still-open
   events; the handled notice appears when there is an accepted proposal **or**
   an already-handled event and nothing is open. It also cross-references
   accepted proposals' `trigger_event_id`, so it is correct even against a
   backend that has not yet been restarted.

`npx vite build` clean.

### Re-verification
Same journey (`e6978c52-…`), three consecutive rounds, after restarting the
backend to load the new projection:
```
backend : active_plan.disruptions = 1 (CLOSURE:ACKNOWLEDGED)
round 1/2/3 Today : attention "已处理"  alerts "通知 · 无活跃"
                  next "… 需要关注 已处理 刚才的变化已经处理好"
round 1/2/3 Live  : banner 0  "当前没有需要你决定的调整。"
                  handled 1  "刚才的行程变化已经处理好，已确认的预订保持不变。"
```
Fresh end-to-end run (`cycle4_clean.cjs`, journey `df741842-…`):
```
9-accept         accepted=true  "已按新安排更新你的行程。"
11-locked-check  lockedSame=true missingLocked=[]
13-agreement     perDay [6,5,2] totalStops=13 backendStops=13
16-hub-after     attention "已处理"
17-live-refresh  proposals=0 disruption=0 handled=1
page-errors      0 []
```
Screenshots after fix: `shots/lab_4b_01_live_proposal.png`,
`shots/lab_4b_02_live_accepted.png`, `shots/lab_4b_03_trips_after.png`,
`shots/lab_4b_06_hub_after.png`, `shots/lab_4b_07_live_refresh.png`,
`shots/lab_4c_02_after_accept_live.png`, `shots/lab_4c_03_after_accept_hub.png`.

## Residual risk / what a real user trial should watch
* **A disruption with no feasible replan is a dead end in the UI.** Raising a
  CLOSURE on 7 of 8 mutable stops returned
  `422 no feasible replan proposal: ACTIVITY_OVERLAP, INSUFFICIENT_TRAVEL_GAP…`
  and Live then showed the event banner plus "当前没有需要你决定的调整。" with
  no action. The product is honest (it does not fabricate a proposal) but the
  traveller is left with an open problem and no path. This is the most important
  thing a real trial should watch; it needs a "we cannot fix this automatically"
  state with a manual next step.
* `ACTIVITY_OVERLAP` and `INSUFFICIENT_TRAVEL_GAP` appear together in most
  refusals; the engine can build a plan it then refuses to re-time. Worth
  tracing whether the accepted plan and the replan gate disagree about the same
  itinerary.
* One run produced 8 DETECTED events from 8 attempts. A real phone cannot raise
  those, but the guardian can: a trial should check that repeated provider
  signals for the *same* closure do not multiply into 8 separate "changes".
* Live shows 3 near-identical proposals as "方案 A/B/C" when several
  disruptions exist; the dedupe only merges identical diffs. Worth watching
  whether a traveller understands they are alternatives.
* `Live`'s 仅调整今天 is a local no-op (`setMessage` only): it records nothing
  and does not reach the server. A trial should check whether travellers expect
  it to persist.
