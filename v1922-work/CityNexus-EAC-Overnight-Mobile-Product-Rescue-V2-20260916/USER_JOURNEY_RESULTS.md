# USER_JOURNEY_RESULTS.md — first-time traveller walkthrough

Method: real Chrome, fresh browser context, cleared localStorage, 390x844
(isMobile + hasTouch) and 430x932, Chinese browser locale. Driven through the
visible UI. Screenshots in `screenshots/after/`, raw JSON in `evidence/`.

## The chain I actually completed

```
open "/"                     -> 新建行程 three-step form
type 厦门                     -> 已自动设置：中国 · 人民币 · 中国标准时间
arrival/departure + dates    -> step 1
travellers/budget/pace/      -> step 2 (values survive Back)
interests/special needs
review                       -> step 3
确认创建                      -> lands on 今天, AI planner already open
type a natural-language trip -> AI 帮我规划 runs a real 4-stage stepper
                             -> honest "AI 暂时不可用" (no key), retry offered
[plan comparison on 今天]     -> 3 candidates, real budget bands, highlights
采用这个方案                  -> chooser closes
行程 tab                     -> real day-by-day itinerary, 6 stops
地图 tab                     -> honest empty state, never Tianjin
Copilot: 鼓浪屿好玩吗         -> answers; no raw enums
backend cut                  -> 连不上服务器 / 数据没有丢失 / 重试, then recovers
语言切换                      -> 菜单 -> Menu -> 菜单, flow intact
```

## Step-by-step

| # | Traveller intent | Result |
| --- | --- | --- |
| 1 | Open the app | **PASS** — modern product, three-step form |
| 2 | Pick a destination | **PASS** — region/currency/timezone inferred; technical fields under 高级设置 |
| 3 | Say who is going and the budget | **PASS** — travellers, rooms, total + stay budget, pace, interests, special requirements |
| 4 | Review before creating | **PASS** — step 3 lists everything and 返回 preserves values |
| 5 | Create the trip | **PASS** — lands on 今天 with the planner open |
| 6 | Tell AI what I want | **PASS** — natural-language sheet with a real stepper, no fake % |
| 7 | See honest progress | **PASS** — stages, then an honest failure branch when AI is unavailable |
| 8 | Compare candidate plans | **PASS** — 3 cards, real cost, real budget band, highlights |
| 9 | Adopt a plan | **PASS** — chooses, chooser hides |
| 10 | See the day-by-day itinerary | **PASS** — 6 stops with times and durations |
| 11 | See activity detail | **PARTIAL** — time, duration, type and protected marker per stop; no separate detail screen with transit/why-this recommendation |
| 12 | Compare / choose hotels | **NOT DONE** — the entry is reachable; comparison and selection were not completed |
| 13 | Map shows the right city | **PASS** — explicit 尚未获取地图位置 instead of another city |
| 14 | Ask Copilot about 鼓浪屿 | **PASS** — answers in traveller language |
| 15 | No internal enum on screen | **PASS** — none of the prohibited tokens |
| 16 | Bookings / wallet does not white-screen | **PASS** |
| 17 | Survive a backend outage | **PASS** — honest panel, then recovery |
| 18 | Plan with GPS denied | **PASS** |
| 19 | Live disruption → replan | **NOT DONE** — Live opens; no disruption was driven to a replan |
| 20 | CN → EN → CN | **PASS** — flow intact after both toggles |

## Why this is not READY

The morning gate requires the READY narrative to end with "并在旅途中看到了可理解
的动态重规划". I did not drive a live disruption through to a governed replan, and
hotel comparison/selection is unfinished. Two core P1s are open, so the honest
verdict is `BLOCKED_FOR_REAL_USER_TRIAL`.
