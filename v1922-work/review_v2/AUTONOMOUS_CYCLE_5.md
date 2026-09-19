# AUTONOMOUS CYCLE 5 — Budget & honesty

## Hypothesis
On a very low-budget trip the product states the budget relationship truthfully
(within / near / over, with a reason) instead of fabricating a "within budget"
claim, and unknown prices are shown as unknown rather than 0.

## Method
Drivers: `cycle5.cjs`, `probe_budget_claim.cjs`, `probe_tiny_budget.cjs`,
`probe_priced_city.cjs`, `probe_over_budget.cjs`, `probe_price_sweep.cjs`
(Playwright + Chrome; mobile 390x844 and desktop 1280x900, `locale: zh-CN`).

Cases driven through the visible UI:
* **A** — very low budget: 厦门, budget **CNY 300**, stay budget **CNY 100**.
* **B** — comfortable budget: 厦门, budget **CNY 8000**, to compare the verdict.
* **C** — unknown-price sweep: plan chosen + live OSM hotel pinned, then every
  surface read for `¥0.00` and for budget claims.
* **D** — Studio's safety-check copy vs the actual cost evidence.
* **E** — budget **CNY 60**, to try to force an "over budget" verdict.
* **F/G** — 天津 via the normal wizard, and with the real discovery endpoint
  asked for places, to reach a city whose sealed fixture carries real prices.

## Evidence

### Unknown prices are never printed as 0 (PASS)
Sweep across 14 surfaces on a journey where all 14 stops and all 10 hotels have
no provider price:
```
anyZeroYuan: []
hub / trips(itinerary,stay,bookings,spend) / live / map / copilot / me /
authoritative / twin / wallet / studio / stay-explorer   zeroYuan=false
```
Concrete text:
* Plan cards: `方案 A 花费未知 总花费 暂无价格` (x3) — no `预算内` at all.
* Trips·Spend: `住宿合计（已选） 价格未知（供应商未提供房价）`.
* Studio: `住宿总计 价格未知`.
* Stay Explorer: `价格未知（供应商未提供房价）`.
* Backend agrees: `planTotalMinor=13200, stops=14, pricedStops=0, unknownStops=14`.

### The plan's own total is mobility-only while every stop price is unknown
```
backend: total_cost = 13200 minor (CNY 132), stops=14, pricedStops=0, unknownStops=14
         score_breakdown.stay = 0, mobility = 13200
activities: all 14 have estimated_cost_minor = 0 and cost_status = UNKNOWN
```
`total_cost_minor` is `stay.total_amount_minor + poi_cost + sum(selected modes)`
(`backend/app/planning/authoritative_v12.py`), so on a live OSM city the "total"
is purely synthetic mobility estimates and contains **no** stop or stay price.
The comparison cards handle this correctly (`花费未知`), but Studio did not.

### DEFECT — Studio claimed the budget was verified when no price existed
```
backend : plan a818d03a-… total ¥132, 14/14 stops UNKNOWN, 0 priced
Studio  : 已通过全部安全检查
          到达、出发、预算和受保护承诺已验证。
```
The deterministic gate treats an unknown cost (0) as satisfying the budget rule,
so it passes — but that is not the same as *verifying* a budget. The screen told
the traveller their budget had been checked when not one price on the itinerary
was a real fact. A low-budget traveller is exactly the person who must not be
told this.

Screenshots (pre-fix): `shots/lab_5_D_studio_budget_claim.png`,
`shots/lab_5_A_low_budget_spend.png`, `shots/lab_5_E_tiny_budget.png`.

### The "over budget" verdict was not reachable in this environment
Neither the live OSM city nor 天津 produced a single priced stop:
```
probe_over_budget (天津 + live discovery): places=3, all cost_status UNKNOWN
                                           plans total=0, known=0, unknown=3 / 2
probe_tiny_budget  (厦门, budget CNY 60): bands = 花费未知 x3
```
`data/v9/city_operations.json` carries real activity prices only for the sealed
fixture, and `GET /places?city_code=CN-TIANJIN` returns `[]`, so the compose path
never sees them. The `超预算` branch is therefore **untested**, not disproved —
see residual risk.

### What the product does say on a tight budget (honest)
With budget CNY 300 for 2 travellers over 3 days, Hub adds a real warning:
```
厦门之旅 3 天 · 2 人 · 每人每天约 ¥50
按这个预算，住宿、交通和吃饭很可能超出计划。可以先调整预算，或你确认继续也可以。
调整预算 / 我知道了，继续
```
and plan cards stay at `花费未知` rather than claiming `预算内`.

## Verdict: CONFIRMED_DEFECT

## Fix
1. **`frontend/src/app/V8Experience.tsx`** (`Studio`) — takes a new `plan`
   prop (the authoritative `PlanVersion`, whose activities carry `cost_status`),
   computes `pricedStops` / `hasPricedEvidence`, and only claims the budget was
   verified when at least one stop has real cost evidence.
   `TripsWorkspace` forwards the plan to the Studio on the Spend tab; both call
   sites pass `authoritativePlan`.
2. **`frontend/src/i18n/LocaleContext.tsx`** — two new zh/en keys:
   * `studio.feasibilityPassedPartial` → 安全检查已通过，预算未验证
   * `studio.feasibilityNoPrice` → 到达、出发和受保护承诺已验证。预算未验证：目前没有任何一站拿到供应商价格。

`npx vite build` clean.

### Re-verification (same journey `c9696395-…`, backend total ¥132 / 14 unknown)
```
BEFORE: 已通过全部安全检查 / 到达、出发、预算和受保护承诺已验证。
AFTER : 安全检查已通过，预算未验证
        到达、出发和受保护承诺已验证。预算未验证：目前没有任何一站拿到供应商价格。
```
Full sweep after the fix (`probe_price_sweep.cjs`):
```
anyZeroYuan: []            anyWithinBudgetClaim: []      anyBudgetVerifiedClaim: []
studio: budgetNotVerified=true   stay-explorer: zeroYuan=false
```
Fresh Cycle-5 run (`cycle5.cjs`, three new journeys): all three cases report
`bands = ["花费未知","花费未知","花费未知"]`, `totals = ["暂无价格", ...]`, and
`zeroYuan=false` on Trips itinerary / spend / bookings / Studio / Hub, with
`backendStay = {options:10, zeroPriced:10, selected:["汉庭酒店"]}`.

Screenshots after fix: `shots/lab_5_H_hub.png`, `lab_5_H_trips_spend.png`,
`lab_5_H_studio.png`, `lab_5_H_stay-explorer.png`, `lab_5_C_unknown_price_sweep.png`.

## Residual risk / what a real user trial should watch
* **The `超预算` (over budget) branch is still unverified.** It needs a city
  whose places carry real `price_known=true` costs; neither the live OSM city
  nor the 天津 fixture reaches the compose path in this environment. A trial
  should run a trip on a priced city and confirm that "超预算 ¥N" appears with a
  reason and that the card is not shown for an unknown-priced plan.
* **`total_cost` means "mobility only" on a live city.** The card calls it
  "总花费" (total cost). Even with the unknown guard, a traveller on a live city
  may read `总花费` as the trip total. Consider labelling it explicitly as
  transport-only when the stay and stops are unpriced.
* **`budget_fit` is still scored from that mobility-only total**
  (`budget_fit: 0.956` on this journey) and is used to rank candidates. A
  ranking derived from an incomplete total is a soft honesty risk even though
  the UI no longer states a budget verdict.
* The Studio safety card still reads 安全检查已通过 while the plan contains
  unknown-priced stops; the sub-line now discloses it, but a trial should check
  whether travellers read the sub-line on a phone.
* `TripItinerary`/`ActivityDetail` were not re-audited for cost display in this
  cycle (ActivityDetail already showed `暂无价格` in earlier runs).
