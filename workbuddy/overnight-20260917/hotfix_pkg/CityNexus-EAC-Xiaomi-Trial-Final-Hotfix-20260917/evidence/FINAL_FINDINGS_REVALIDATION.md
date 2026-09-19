# FINAL FINDINGS REVALIDATION — B1..B6 against CURRENT code

Method: each blocker was reproduced against the current worktree (not the exported
package). Evidence is a source location plus a live probe, both run AFTER the
corresponding fix where one was needed.

| # | Blocker | Verdict | Evidence |
|---|---|---|---|
| B1 | Final Copilot evidence stale | **FIXED** | `VISIBLE_UI_TRACE_FINAL.json` was generated after the last source edit; the Copilot step is captured live in it (`assertions.copilot`). No stale trace is used as proof. The ledger now carries the shutdown interruption and closes with FINAL. |
| B2 | Me exposes ADVISORY / 权限边界 | **FIXED** | Me rebuilt (`frontend/src/app/V8Experience.tsx`, `function Me`). Live probe of the default surface: `leaks ADVISORY: false / 权限边界: false / CN-XIAMEN: false`. Policy mode, version, city code and raw policy JSON now live under `data-testid="me-advanced"`. |
| B3 | known-free / partial-price / low-budget truth | **FIXED** | `ActivitySchema.cost_status` added and derived in `app/services.py::_activity_cost_status`; ActivityDetail renders 已知免费→`免费`, 已知付费→金额, 未知→`暂无价格` (`data-cost-status`). PlanComparison now requires ALL stops priced before any budget verdict, and says `部分价格未知 (n/N)` / `至少 …` otherwise. Budget advisory added at `data-testid="budget-advisory"`. 8/8 unit cases + 9 regression tests pass. |
| B4 | Wallet route developer-shaped | **FIXED** | Raw JSON moved under `data-testid="bookings-advanced"` with a guarded parse; invalid input shows a localised `data-testid="bookings-parse-error"` instead of throwing. `UNKNOWN_REALTIME` → 暂无实时状态, `受保护 C4` → 已确认 · 受保护, `Journey Memory` → 已保存的行程事实. `/v8/bookings` deep link now routes to Trips. |
| B5 | /v8/today and /v8/copilot blank | **FIXED** | `routeFromPath` now maps aliases (today→hub, copilot→agent, bookings/wallet/stay→trips) and falls back to Today for any unknown key. Live probe: `/v8/today` 622 chars, `/v8/copilot` 353 chars, `/v8/bookings` 438 chars, `/v8/unknownroute` 622 chars — none blank. |
| B6 | AI success satisfied by OLD plans | **FIXED** | `PlanWithAiSheet.tsx` snapshots existing plan ids before the run and counts only artifacts this run created (`data-new-plan-ids`). Verified: `baseline_count=0, reported_new_count=3, backend_new_ids` match exactly. |
| — | Copilot engineering vocabulary | **FIXED** | `humanIntent`/`humanVerification`/`humanAction` map enums; runtime/provider detail sits under Advanced; `What-if Studio`/`JourneyTwin`/`deterministic`/`DeepSeek` replaced in EN+ZH copy. `assertions.copilot.raw_vocabulary_leak = false`. |
| — | Evidence assertion cleanup | **FIXED** | `stay-truth` now reads the real nested payload and joins the offer by `external_offer_id`: `name=喜来登酒店 in=2026-11-06T06:00:00+00:00 out=2026-11-08T04:00:00+00:00`. `undefined` can no longer be a PASS value because the trace throws when a field is missing. `trips-vs-backend` states its entity set and proves UI total (14) equals backend activities (14). |

## Additional real defects found while revalidating

* **Stay calendar vs gate used two different generators.** `_travel_minutes` reserved
  the *slowest* mode (up to 134 min) while the plan's selected leg fact was the
  *fastest* (~4–25 min), so every hotel was rejected with a false
  `STAY_ITINERARY_CONFLICT:NO_SAME_DAY_SLOT`. Both now reserve the same leg.
* **Materialiser trusted stale adjacency facts.** After the calendar re-ordered
  stops, `_selected_facts` matched previously captured `MobilityFact` rows for a
  different adjacency, producing `INSUFFICIENT_TRAVEL_GAP` / `LEG_ARRIVES_LATE`
  on a feasible plan. It now re-derives each leg from the calendar's own
  generator and persists that as the frozen fact (with a unique-index guard).
