# AUTONOMOUS CYCLE 2 — Empty & degraded states

## Hypothesis
With no plan, no hotel and no booking, every screen shows a useful, honest state:
never a blank page, never invented data, never an internal enum or an
English/internal identifier in the Chinese UI.

## Method
Driver: `cycle2_probe.cjs`, `cycle2_deep.cjs`, `cycle2_studio.cjs`,
`cycle2_focus.cjs`, `cycle2_glance.cjs`, `cycle2_noopts.cjs`,
`cycle2_stay_price.cjs`, `cycle2_full.cjs` (Playwright + Chrome; mobile
390x844 zh-CN, and 1280x900 for the desktop-only routes).

Cases driven entirely through the UI:
* **A — no journey at all:** opened all 14 routes (`/`, `/v8/hub`, `/v8/trips`,
  `/v8/live`, `/v8/agent`, `/v8/map`, `/v8/me`, `/v8/stay`, `/v8/bookings`,
  `/v8/authoritative`, `/v8/studio`, `/v8/discover`, `/v8/intelligence`,
  `/v8/twin`) in a clean browser profile.
* **B — journey created but no plan chosen:** 3-step wizard (厦门,
  2026-11-06 10:00 → 2026-11-08 20:00, budget 3000 / stay 1000), then read
  Today, Trips (all four sub-tabs), Live, Studio, Stay Explorer, Bookings,
  Authoritative, Map, Me, Twin.
* **B2 — journey with zero stay options** (`/v8/stay` on a journey whose
  capture produced none).
* **C — desktop Stay Explorer** at 1280x900, including hard refresh.
* Backend `/experience` and `/stay-options` read out-of-band only to check the
  screens against truth.

## Evidence

### What held (PASS)
* **No blank page anywhere.** Case A: `blank=[]` for all 14 routes; every route
  rendered the 3-step setup sheet (`nonSetup=[]`), i.e. a traveller with no
  journey always gets a way forward.
* **Honest zero-option state** on the stay surface:
  `还没有可用的住宿候选 / 我们还没有拿到真实住宿数据，所以不会给你看一张假的价格卡片。可以先选好行程，再回来搜索住宿。`
* **No invented itinerary:** with no plan, Trips says
  `还没有可看的行程 / 这个行程还没有选定的方案。先让 AI 帮你规划，选定方案后这里会显示逐日安排。`
  and Authoritative says `你还没有选定方案。`, Live says `还没有选定的行程安排。`
* **Money honesty on the new stay list** (`HotelsPanel`, already correct):
  `价格 暂无价格` instead of `¥0.00`.
* No page errors in any case (`errors: []`).

### DEFECT 1 — Hub presented a candidate stay option as the traveller's trip
With `active_plan = null` and `selected_option_id = null` in the backend, Hub
rendered a full day-by-day "方案概览" that belonged to an un-chosen stay option,
with no indication it was only a preview:

```
backend: {"active_plan": null, "selected_option_id": null, "options": 10}
hub: 方案概览 每一天，紧密相连。 对比住宿 →
     第 1 天 Friday  厦门高崎国际机场 · Check in · 汉庭酒店 · Overnight · 汉庭酒店  TRANSIT ARRIVAL锚点
     第 2 天 Saturday Overnight · 汉庭酒店  WALK STAY锚点
     第 3 天 Sunday  Check out · 汉庭酒店 · 厦门北站  AUTO DEPARTURE锚点
```
The same thing happened on the Studio screen: `已选住宿 更换 / 汉庭酒店 hotel
¥0.00 合计`, `住宿总计 ¥0.00`, `方案健康度 受保护 · 417 分钟余量`, and
`已通过全部安全检查 到达、出发、预算和受保护承诺已验证。` — while
`selected_option_id` was `null` and no plan existed. Verified against the
backend: `studio.backend = {"selected_option_id": null, "active_plan": null,
"options": 10}`.

Root cause (frontend): the shell derives a display `selected` as
`options.find(id === selected_option_id) ?? options[0]` — correct for keeping
screens non-empty, but `Studio`/`Hub` treated that fallback as *the chosen*
option. `TripsWorkspace` also summed **every** candidate's
`stay_total_minor` into "住宿合计（已选）".

### DEFECT 2 — unknown prices rendered as `¥0.00` on the desktop stay surface
The live OSM provider deliberately returns `nightly_amount_minor = 0` with no
price (`backend/app/integrations/stay_osm.py`: *"OSM carries no price. Zero +
explicit unknown beats a fabricated nightly rate."*). The Stay Explorer printed
that zero as a real price, three times per card:

```
stay card : XIAMEN 01 汉庭酒店 hotel · 2 travelers · 不可退款 ¥0.00 total · ¥0.00//晚
detail    : 总计 / 币种  ¥0.00 · CNY
backend   : {"property_name":"汉庭酒店","total":0,"nightly":0,"price_basis":"per_night × nights"}
```
`¥0.00 total · ¥0.00//晚` reads as a free hotel; the `//` is a doubled unit.
The English `hotel`, `travelers`, `total`, `min walk`, `min slack`, `TRANSIT`
and the raw provider string `Non-refundable captured rate` also leaked into the
Chinese screen (Stay Explorer + Studio + Bookings cards).

### DEFECT 3 — a hard refresh swapped the screen on real desktop routes
`ROUTE_ALIASES` mapped `stay → trips` and `bookings → trips` *before* checking
`KNOWN_ROUTES`, so the alias shadowed real routes:

```
after nav click : {"path":"/v8/stay","stayExplorer":1,"tripsTabs":0,"breadcrumb":"行程 / 住宿选择"}
after reload    : {"path":"/v8/stay","stayExplorer":0,"tripsTabs":1,"breadcrumb":"行程 / 行程"}
/v8/stay        -> {"stayExplorer":0,"tripsTabs":1}   (deep link)
/v8/bookings    -> {"tripsTabs":1,"breadcrumb":"行程 / 行程"}
```
The traveller opened 住宿选择, reloaded, and silently landed on the Trips
workspace. `/v8/bookings` never reached the Travel Wallet at all.

Screenshots (pre-fix): `shots/lab_2_D_hub_noplan.png`,
`shots/lab_2_D_studio_noplan.png`, `shots/lab_2_C_stay_explorer_noplan.png`,
`shots/lab_2_G_studio_false_claims.png`.

## Verdict: CONFIRMED_DEFECT

## Fix
1. **`frontend/src/app/V8Experience.tsx`** — the shell now derives two distinct
   values: `selected` (what to preview) and `chosenOption` (the option the
   traveller actually committed to, or `null`).
   * `Hub` takes a new `hasChosenPlan` prop; the day cards carry an explicit
     `hub-glance-caveat` ("以下只是其中一个候选方案的预览，你还没有采用它。"),
     and an empty state is shown when there is nothing to preview.
   * `Studio` takes a new `chosen` prop. The "已选住宿" block, `studio-stay-total`,
     daily movement, walking exposure and plan health all read `chosen`, so an
     un-chosen option can no longer be called "your stay" or be counted as
     spend. Before a plan exists the feasibility card is replaced by
     `studio-no-plan` → "尚未核对 / 你还没有选定方案，因此没有可核对的内容。"
     A `studio-preview-caveat` marks the day list as a preview.
   * `TripsWorkspace` spend tab uses `chosen` (not the sum of all candidates)
     and shows `spend-stay-total` → "还没有选定住宿".
   * `Bookings` takes `chosen`; the stay card is labelled 住宿预览 / 尚未选择
     when nothing is committed, with a real no-stay state.
   * `ROUTE_ALIASES` no longer contains `stay`/`bookings`, and `routeFromPath`
     checks `KNOWN_ROUTES` **before** aliases, so a real route can never be
     shadowed by a redirect alias.
2. **`frontend/src/features/stay/StayExplorer.tsx`** — added `pricePair`,
   `roomLabel`, `modeLabel`; `priceLabel` now treats `null`, `undefined` **and
   `<= 0`** as unknown; the cancellation summary is mapped from the provider's
   English string to 不可取消 / 入住前可免费取消.
3. **`frontend/src/app/v8Types.ts`** — `journey.timezone` added to the `V8Data`
   type (it is already in the API payload; Cycle 1 reads it).
4. **`frontend/src/i18n/LocaleContext.tsx`** — new zh/en keys:
   `studio.noStaySelected`, `studio.chooseStay`, `studio.notChosen`,
   `studio.priceUnknown`, `studio.noPlanChecked`, `studio.noPlanCheckedSub`,
   `bookings.stayPreview`, `bookings.notChosen`, `bookings.noStaySub`.

`npx vite build` clean.

### Re-verification (`cycle2_full.cjs`, fresh journey on a fresh DB)
```
A blank=[] nonSetup=[]
B backend {"active_plan":null,"selected_option_id":null,"options":10}
hub            caveat "以下只是其中一个候选方案的预览，你还没有采用它。"  stay "还没有选定"
studio         aside "尚未选择住宿 选择住宿"  stayTotal "尚未选择"
               selectedStayBlock count = 0
               feasibility "尚未核对 你还没有选定方案，因此没有可核对的内容。…"
               studio-no-plan present = 1
tripsSpend     stayTotal "还没有选定住宿"
C stay explorer after reload: path /v8/stay, breadcrumb 行程 / 住宿选择,
               cards 4, priceUnknown 4, priceKnown 0,
               firstCard "… 酒店 · 2 位旅客 · 不可退款 价格未知（供应商未提供房价）…",
               detailTotal "价格未知（供应商未提供房价）",
               cancellation "不可取消", bodyHasZeroYuan false
errors []
```
Screenshots after fix: `shots/lab_2_v2_hub_noplan.png`,
`shots/lab_2_v2_studio_noplan.png`, `shots/lab_2_v2_trips_spend.png`,
`shots/lab_2_v2_stay_desktop.png`, `shots/lab_2_final_stay_explorer.png`.

## Residual risk / what a real user trial should watch
* The Studio day list still renders the previewed option's days (with a caveat).
  A traveller could still mistake a preview 
