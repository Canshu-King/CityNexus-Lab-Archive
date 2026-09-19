# UI_IMPLEMENTATION_MAP.md

The ten images are direction references; `DESIGN_CORRECTIONS_REQUIRED.md`
overrides any contradictory demo text in them. DONE = implemented **and**
personally observed in a real browser with evidence in this package.

| Ref | Screen | Status | Notes |
| --- | --- | --- | --- |
| — | Primary navigation | **DONE** | 今天 / 行程 / 地图 / Copilot / 我的; Wallet demoted (corrections §1) |
| — | Default entry `/` | **DONE** | Modern product; legacy behind `/legacy` |
| 01 | Today dashboard | **PARTIAL** | Renders with a working plan chooser and AI CTA; hero copy still partly generic |
| 02 | Trip detail (multi-day) | **PARTIAL** | New itinerary with day detail and a **week strip for >7 days**; not the full reference layout |
| 03 | Create trip step 1 | **DONE** | Destination + arrival/departure + dates; inferred region; 高级设置 holds country/timezone/currency (corrections §5) |
| 04 | Create trip step 2 | **DONE** | Travellers/rooms/budget/stay budget/pace/interests/special requirements |
| — | Create trip **step 3** | **DONE** | Review + 返回 + 确认创建 (corrections §4) |
| 05 | AI trip intent | **DONE** | Natural-language sheet, examples, no internal vocabulary |
| 06 | AI generation progress | **DONE** | Real 4-stage stepper; **no fabricated percentage** (corrections §6) |
| 07 | Plan comparison | **DONE** | Cost, stops, walking (only when real), highlights, real budget band, choose |
| 08 | Activity detail | **PARTIAL** | Per-stop time/duration/type/protected inside the itinerary; no separate screen |
| 09 | Hotel comparison | **NOT DONE** | Stay Explorer exists but was not reworked or driven |
| 10 | Live journey / replan | **NOT DONE** | Live opens; disruption→replan surfacing not built |
| — | Order import | **NOT DONE** | Existing inbox accepts pasted reservation JSON only |
| — | Error boundary | **DONE** | Bilingual, retry / back to Today / reload |
| — | Empty / failure states | **PARTIAL** | Itinerary-empty, map-no-location, backend-unreachable, AI-unavailable done; the rest of the matrix is open |

## Deliberately NOT implemented from the images

The reference images contain inconsistent demo numbers (¥8000 on one screen,
¥3000 on another). Per corrections §2 the target is one coherent set — 厦门, 2
travellers, CNY 3000 total / CNY 1000 stay — and the create-trip flow now uses
those defaults. The conflicting numbers were **not** reproduced.
