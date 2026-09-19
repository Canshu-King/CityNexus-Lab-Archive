# TEST_RESULTS.md — CityNexus Overnight Mobile Product Rescue V2

All numbers are from real runs during this session.

## Environment

| Item | Value |
| --- | --- |
| Backend | uvicorn 127.0.0.1:8000, throwaway SQLite |
| Frontend | Vite dev server 127.0.0.1:5173 |
| Browser | real Chrome via Playwright, 390x844 (isMobile/hasTouch) and 430x932 |
| AI | `CITYNEXUS_AI_ENABLED=false` — local fallback, not live DeepSeek |

## 1. Backend truth (Phase 0) — PASS

| Check | Result |
| --- | --- |
| V19.2.5 C4 interior probe | **5/5 PASS**, exit 0 |
| Gate suites (V19.2 + V19.2.3 + V19.2.4 + V19.2.5) | **93 passed** |

The backend was frozen after this and not modified again this session.

## 2. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 3. Real-browser morning gate — 20/20 PASS

```
01 / 进入新产品                         PASS
02 自动推断国家/货币/时区                PASS
03 三步创建流程                          PASS
04 AI 规划面板打开                       PASS
05 诚实规划进度/结果                     PASS
06 比较候选方案                          PASS  cards=3
07 采用方案                              PASS
08 逐日行程详情                          PASS  stops=6
09 活动详情(时间+时长)                   PASS
10 住宿入口可见                          PASS  (entry only)
11 地图正确/诚实空态                     PASS  empty-state
12 Copilot 回答问题                      PASS
13 无原始枚举泄露                        PASS
14 预订/钱包不白屏                       PASS
15 语言切换不破坏流程                    PASS  菜单 -> Menu
16 后端断开可恢复                        PASS
17 GPS 拒绝仍可用                        PASS
18 Live 可进入                           PASS  (not driven through a disruption)
19 430x932 无横向溢出                    PASS  sw=430 cw=430
20 主导航 = 今天/行程/地图/Copilot/我的   PASS
```

Page/console errors: **0** apart from the deliberate `net::ERR_FAILED` produced
by the backend-offline test itself.

Evidence: `evidence/gate.json`, plus the per-scenario JSON in `evidence/`.

## 4. Screenshots

* `screenshots/before/` — the user's real Xiaomi 13 Ultra photographs, unmodified.
* `screenshots/after/` — real browser captures at 390x844 for the create flow,
  plan sheet, plan comparison, itinerary, map empty state, Copilot, offline
  state and language switch.

## 5. Not run

| Item | Why |
| --- | --- |
| Hotel comparison / selection | not built (gap #1) |
| Live disruption → replan | not built (gap #2) |
| AI success branch | no DeepSeek credential in this environment |
| Live mobility / weather providers | `CITYNEXUS_AI_ENABLED=false`, no provider keys |
| Xiaomi-13-Ultra-like physical viewport | deferred; 390x844 and 430x932 were swept |
| OpenAPI parity | no API contract changed this session |

## 6. Honest statement

`READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL` is **not** claimed: two core P1s (hotel
comparison, live disruption → replan) remain open, so the required READY
narrative cannot be written truthfully. See `USER_JOURNEY_RESULTS.md`.
