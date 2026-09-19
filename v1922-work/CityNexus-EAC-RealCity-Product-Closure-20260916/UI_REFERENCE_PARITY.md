# UI_REFERENCE_PARITY.md — reference screens vs implementation

The ten images remain direction, and `DESIGN_CORRECTIONS_REQUIRED.md` overrides
their contradictory demo text. `EAC_NEXT_MISSION.md` requires them to be
**materially implemented**, not merely used as IA inspiration.

| Ref | Screen | Status | Evidence / notes |
| --- | --- | --- | --- |
| 01 | Today | **PARTIAL** | Renders with plan chooser + AI CTA; hero copy still partly generic ("Your next city, already considered"), not yet "厦门之旅 / 今天要做什么" |
| 02 | Trip detail (multi-day) | **PARTIAL** | Real day-grouped itinerary with week strip for >7 days, inside a sub-tabbed Trips screen; not the full reference layout |
| 03 | Create step 1 | **DONE** | destination + arrival/departure + dates, inferred region, 高级设置 |
| 04 | Create step 2 | **DONE** | travellers/rooms/budget/pace/interests/special requirements |
| — | Create step 3 | **DONE** | review + back + confirm (corrections §4) |
| 05 | AI intent | **DONE** | natural-language sheet, examples, no internal vocabulary |
| 06 | Generation progress | **DONE** | real 4-stage stepper, no fabricated percentage |
| 07 | Plan comparison | **DONE** | real cost, budget band, stops, walking, highlights; labelled 方案 A/B/C rather than invented styles |
| 08 | Activity detail | **NOT DONE** | per-stop time/duration/type exist inside the itinerary; no dedicated screen |
| 09 | Hotel comparison | **DONE (new)** | 4 real Xiamen stays with price/walking/fit/cancellation/reason and select |
| 10 | Live + replan | **DONE (new)** | 发生了什么 / 受影响 / 保持不变 / 接受 / 仅调整今天 / 稍后提醒, driven to `ACCEPTED` |
| — | Trips IA | **DONE (new)** | 行程 / 住宿 / 预订 / 花费 sub-tabs; default screen answers "what is planned" within one screen |
| — | Order import | **NOT DONE** | see ORDER_IMPORT_RESULTS.md |
| — | Error boundary | **DONE** | bilingual retry / back / reload |

## Visual direction

Snapshot H reused the old console styling. This round added a real product
layer rather than a re-skin:

* sub-tab navigation with 40px touch targets and an active pill;
* card surfaces for hotels and proposals with status badges
  (已选择 / 预算内 / 超预算);
* sticky primary CTA on the create-trip wizard;
* traveller copy in Chinese on every acceptance surface.

It is **not** yet a full visual match to the reference system: typography scale,
illustration and spacing rhythm are still closer to the previous console than to
the reference images. Recorded as remaining work, not claimed as done.

## Consumer vocabulary rule

Checked across the acceptance surfaces:

```
provider evidence · deterministic gate · authority envelope · Twin context ·
PlanVersion · C4 · REQUEST_PLACE_SEARCH · raw enums
```

None of these appear on Today, Trips, Map, Copilot, the create wizard or Live.
Traveller equivalents are used instead (实时数据 / 已核验 / 已确认预订 /
需要重新规划 / 当前行程).
