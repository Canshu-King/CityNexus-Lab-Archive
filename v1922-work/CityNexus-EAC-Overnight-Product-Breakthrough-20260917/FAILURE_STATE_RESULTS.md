# FAILURE_STATE_RESULTS.md

## Verified states

| State | Behaviour | Evidence |
| --- | --- | --- |
| Backend offline | explicit `连不上服务器 / 你的行程数据没有丢失 / 重试` panel, no white screen; recovers after the backend returns | earlier round, retained |
| No map coordinates | explicit `尚未获取地图位置` empty state; never renders another city | `fe_final.json` (Xiamen fixture has coordinates, empty state covered earlier) |
| AI unavailable | honest `AI 暂时不可用` with retry; never fabricates a plan | earlier round, retained |
| No plan yet | itinerary-empty state with a `AI 帮我规划` call to action | earlier round, retained |
| GPS denied | app remains usable; planning is not blocked | earlier round, retained |
| Runtime component error | bilingual error boundary with retry / back to Today / reload | earlier round, retained |
| Booking extraction unavailable | deterministic text/manual paths remain; no fabricated extraction | this round |

## Not exercised tonight

* disconnect/reconnect during an active flow;
* refresh during loading;
* double-tap on primary CTAs;
* provider-unavailable during the canonical chain;
* stale/recovery state surfacing.

These are listed in `REMAINING_PRODUCT_GAPS.md`.
