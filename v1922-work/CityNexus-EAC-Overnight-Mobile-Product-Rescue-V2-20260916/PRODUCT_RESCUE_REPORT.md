# PRODUCT_RESCUE_REPORT.md — CityNexus Overnight Mobile Product Rescue V2

## Verdict

**BLOCKED_FOR_REAL_USER_TRIAL**

Honest reason: the **primary traveller chain now works end to end in a real
browser** (create → AI entry → compare → adopt → itinerary → map → Copilot →
failure recovery → language), and the 20-item morning gate scored 20/20 on the
things I could actually drive. But two core P1s are **not** genuinely closed:

* hotel **comparison and selection** (gate #11) — only the entry is reachable;
* **live disruption → governed replan** (gate #19) — Live opens, but I did not
  drive a disruption and see an understandable replan.

The gate also requires the READY narrative to end with "...并在旅途中看到了可
理解的动态重规划". I cannot truthfully write that sentence. So READY is not
claimed.

## Phase 0 — V19.2.5 backend truth (DONE)

The C4 interior-boundary hotfix is in the live tree and independently verified:

```
MID_TRIP before ARRIVAL        -> rejected (C4_ACTIVITY_BEFORE_ARRIVAL)
MID_TRIP after DEPARTURE       -> rejected (C4_ACTIVITY_AFTER_DEPARTURE)
role-less lock before ARRIVAL  -> rejected
valid controls                 -> accepted
```

`v1925_c4_interior_probe.py` → **5/5 PASS**, exit 0. Backend suites → **93/93**.
Backend was then frozen; nothing else touched it.

## The information architecture is now correct

| Requirement | Result |
| --- | --- |
| `/` enters the modern product | **DONE** — was `LegacyApp`; legacy now at `/legacy` |
| Bottom nav = 今天 / 行程 / 地图 / Copilot / 我的 | **DONE** — browser-read labels match exactly |
| Wallet out of primary navigation | **DONE** — moved under 行程 and 我的 |

## The traveller chain that now works

Verified in real Chrome at 390x844 and 430x932, fresh context, cleared state:

1. Open `/` → three-step create-trip flow.
2. Step 1 infers 中国 · 人民币 · 中国标准时间 from "厦门"; technical fields behind
   **高级设置**.
3. Step 2 captures travellers, rooms, budget, stay budget, pace, interests and
   special requirements; values survive going **Back**.
4. Step 3 reviews everything, then creates the Journey and lands on **今天**
   with the AI planner already open.
5. **AI 帮我规划**: natural language in, a real 4-stage stepper out, no
   fabricated percentage. With no DeepSeek key configured it says **"AI
   temporarily unavailable — your trip is unchanged"** with a retry, and never
   leaks an internal enum.
6. Today shows a **plan comparison**: per-plan total cost, stops, walking (only
   when real), highlights, and a real budget band (预算内 / 接近预算上限 / 超预算
   +amount with a reason).
7. Choosing a plan hides the chooser and the **行程** tab shows a real
   day-by-day itinerary with times, durations and protected markers.
8. **地图** never silently renders Tianjin: with no trustworthy coordinates it
   shows an explicit "尚未获取地图位置" empty state.
9. **Copilot** answers, and its vocabulary is now traveller language
   ("I need one more detail", "Answered offline", "What I understood") instead
   of raw enums.
10. Backend offline → **"连不上服务器 / 你的行程数据没有丢失 / 重试"**, and it
    recovers. No white screen.
11. Language follows `navigator.language` and toggles 中文 → English → 中文
    without breaking the flow.
12. Any runtime error is caught by a bilingual **error boundary** with
    retry / back-to-Today / reload.

## Morning gate scorecard (real browser)

```
01 / 进入新产品                 PASS
02 自动推断国家/货币/时区        PASS  已自动设置：中国 · 人民币 · 中国标准时间
03 三步创建流程                  PASS
04 AI 规划面板打开               PASS
05 诚实规划进度/结果             PASS  AI 暂时不可用
06 比较候选方案                  PASS  cards=3
07 采用方案                      PASS
08 逐日行程详情                  PASS  stops=6
09 活动详情(时间+时长)           PASS
10 住宿入口可见                  PASS  (entry only — see gap #11)
11 地图正确/诚实空态             PASS  empty-state
12 Copilot 回答问题              PASS
13 无原始枚举泄露                PASS
14 预订/钱包不白屏               PASS
15 语言切换不破坏流程            PASS  菜单 -> Menu
16 后端断开可恢复                PASS
17 GPS 拒绝仍可用                PASS
18 Live 可进入                   PASS  (not driven through a disruption)
19 430x932 无横向溢出            PASS  sw=430 cw=430
20 主导航 = 今天/行程/地图/Copilot/我的  PASS
```

0 page errors except the deliberate `net::ERR_FAILED` from the offline test.

## What did NOT get done

See `REMAINING_PRODUCT_GAPS.md`. The largest items:

* hotel comparison / selection to the reference IA;
* live disruption surfacing and governed replan acceptance;
* order import (upload / paste / manual) with an explicit confirm step;
* the full empty/failure matrix beyond the error boundary and backend-offline;
* AI planning cannot complete without a DeepSeek credential, so the
  AI-generated-plan path was only exercised through its honest failure branch.

## Explicit non-claims

* No real payment was executed.
* **No physical-device testing.** All evidence is emulated viewports in headless
  Chrome on the build host.
* No live DeepSeek call: the backend ran with `CITYNEXUS_AI_ENABLED=false`.
* No live mobility/weather provider verification.
