# USER_JOURNEY_RESULTS.md — same-journey Xiamen walkthrough

Method: real Chrome via Playwright, fresh context per viewport, cleared
localStorage, Chinese locale, 390x844 and 430x932. Backend ran with **live
credentials** (`DEEPSEEK_API_KEY` from the user environment, injected into the
child process only; never printed or persisted) and live providers.

`/api/v1/demo/reset` was **never called** for this run.

## The chain that was completed

```
create 厦门征程 (visible UI)        -> journey 89695905…  city CN-XIAMEN
live discovery (Overpass/Nominatim) -> 6 real Xiamen POIs
generate candidates                 -> 3 plans, 6 / 5 / 4 stops
compare + select                    -> 89a623c2…
start                               -> ACTIVE
stay offers + generate              -> 4 real Xiamen hotels
select stay                         -> authoritative selection updated
itinerary                           -> day-grouped stops
map                                 -> real coordinates / honest empty state
Copilot 鼓浪屿好玩吗                 -> answered, no enum
disruption (CLOSURE)                -> event raised on a real stop
governed replan                     -> PRESENTED, C4 preserved
accept                              -> ACCEPTED
final state                         -> plan 8c4c6f6f…, 6 stops, recovery consistent
```

## Step results

| # | Intent | Result |
| --- | --- | --- |
| 1 | Open the product | **PASS** — modern product at `/`, not LegacyApp |
| 2 | Create a Xiamen trip | **PASS** — three steps, region inferred, sticky CTA, values preserved on Back |
| 3 | Ask AI to plan | **PASS** — natural language, real stepper, honest failure branch |
| 4 | Real Xiamen candidates | **PASS** — 3 plans built only from discovered Xiamen POIs |
| 5 | Compare candidates | **PASS** — real cost / stops / walking / budget band / highlights |
| 6 | Choose a plan | **PASS** |
| 7 | Itinerary | **PASS** — day-grouped stops with times and durations |
| 8 | Activity detail | **PARTIAL** — details inline per stop; no dedicated screen |
| 9 | Map | **PASS** — real coordinates; honest "尚未获取地图位置" when absent |
| 10 | Hotel compare / select | **PASS** — 4 provider-backed Xiamen stays, selection applied |
| 11 | Booking import | **PARTIAL** — works, but still a JSON box rather than a consumer flow |
| 12 | Live + disruption | **PASS** — 发生了什么 / 受影响 / 保持不变 / 推荐怎么改 |
| 13 | Governed replan accept | **PASS** — `ACCEPTED`, C4 preserved, consistent final state |
| 14 | No internal vocabulary | **PASS** — none of the forbidden tokens on any acceptance surface |
| 15 | Chinese-first | **PASS** — whole run in Chinese; 中文 → EN → 中文 preserves state |
| 16 | No map fallback city | **PASS** — Tianjin never rendered for Xiamen |
| 17 | 430x932 | **PASS** — all tabs render, no horizontal overflow |

## Why the verdict is still BLOCKED

Three items remain short of the mission's bar, and the mission is explicit that
"route opens" is not a pass:

1. **Order import** is still a raw JSON textbox; the consumer entry
   (paste text → parsed preview → confirm, plus a guided manual form) is not
   built. See `ORDER_IMPORT_RESULTS.md`.
2. **Activity detail** has no dedicated screen (reference 08).
3. **Visual parity** is partial: the product layer is real, but the visual
   system is still closer to the previous console than to the reference images.

Everything the mission listed as *blocking* — same-journey continuity, real
Xiamen planning, hotel compare/select, live disruption → governed replan — is
now done and evidenced. READY is withheld on the three items above rather than
over-claimed.
