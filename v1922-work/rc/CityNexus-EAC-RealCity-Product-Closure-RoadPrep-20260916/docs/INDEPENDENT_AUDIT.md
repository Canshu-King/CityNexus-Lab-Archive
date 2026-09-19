# Independent audit of Snapshot H

## Overall verdict

`BLOCKED_FOR_REAL_USER_TRIAL`

EAC's own verdict is correct.

The result is a meaningful improvement over the previous frontend, but its
"primary traveller chain works end to end" statement is too broad.

The evidence actually proves several useful subflows, not one continuous
real-Xiamen end-to-end flow.

---

## What is genuinely fixed

Confirmed from the submitted source, reports, and browser screenshots:

- `/` now opens the modern product instead of LegacyApp.
- primary bottom navigation is now Today / Trips / Map / Copilot / Me.
- Wallet no longer occupies a primary bottom tab.
- three-step create-trip flow exists.
- country/currency/timezone inference exists.
- Wallet/Bookings `data is not defined` crash was fixed.
- a product Error Boundary exists.
- Xiamen no longer silently falls back to Tianjin on the map.
- AI planning UI uses an honest staged progress model instead of fake percentage.
- candidate-plan selection UI exists.
- trip itinerary rendering exists.
- backend-offline recovery exists.
- raw `REQUEST_PLACE_SEARCH` is no longer exposed.
- V19.2.5 C4 interior truth hotfix is reported 5/5 green.
- package hygiene is good: no db/log/cache pollution.

These are real gains.

---

## P0/P1 finding 1 — the Xiamen chain was NOT proven end-to-end

This is the most important issue.

The package explicitly states:

- the newly-created Xiamen Journey cannot produce plans in this environment;
- Xiamen has no sealed provider fixture;
- `CITYNEXUS_AI_ENABLED=false`;
- the reachable plan-generation/adoption chain was exercised on the sealed
  Tianjin demo Journey.

The browser evidence confirms this.

The Xiamen create screen exists, but the candidate-plan / itinerary evidence
contains:

- Old Town Gate
- Riverside Museum
- Central Food Hall
- Tech Art Center
- Nexus River Cruise Pier
- Skyline Dinner House
- `One Day in Nexus City`

Those are not the Xiamen journey the user created.

Therefore the following sentence is **not yet proven**:

> Create Xiamen -> ask AI -> compare Xiamen plans -> adopt one -> see Xiamen
> itinerary -> see Xiamen map -> choose Xiamen hotel -> live/replan Xiamen.

The next acceptance run must use the **same journey id and same city_code**
through the whole chain.

No acceptance evidence may switch to `/demo/reset` or the sealed Tianjin
journey after creating Xiamen.

---

## P1 finding 2 — hotel comparison/selection is missing

EAC says this itself.

The product currently has an entry / existing Stay Explorer, but not the
reference product flow:

- price
- area
- distance to current itinerary
- reason for recommendation
- cancellation / breakfast where available
- compare
- select
- selected hotel visibly changes the Journey/plan context

This is a required core traveler workflow.

---

## P1 finding 3 — live disruption -> governed replan is missing

`Live` opens, but the submitted evidence does not prove:

event/disruption
-> traveler-language explanation
-> affected activities
-> unchanged commitments
-> proposed replacement ordering
-> user accepts
-> active/selected plan truth updates
-> recovery state resolves

The current live screenshot still looks like an engineering operation surface,
not the intended traveler product.

---

## P1 finding 4 — the UI reference set was not materially implemented

The 10 reference screens were used as information-architecture guidance, but the
submitted UI remains visually very close to the old V8 engineering console.

Examples from the real screenshots:

### Create trip
Still looks like raw desktop-form controls squeezed onto a phone:
- plain text fields
- narrow default inputs
- almost no visual hierarchy
- mostly English
- no reference-quality destination hero/card system

### Today
Still contains:
- `STILL UP`
- `Your next city, already considered.`
- `One Day in Nexus City`
- `PLANNING READY`

This is not the Chinese-first Xiamen traveler dashboard reference.

### Trips
It concatenates:
- itinerary
- Trip Studio
- Stay state
- raw reservation JSON
- authority/delegation explanation

into one very long scrolling page.

That recreates the original "phone novel" problem in a different route.

### Plan comparison
The reference calls for distinct plan identities.
The actual evidence shows three cards all called:

`Balanced`

with the same highlights.

This is technically three candidates, but not a meaningful traveler comparison.

### Copilot
The raw enum is gone, which is good.
But with AI disabled the answer to `鼓浪屿好玩吗` is effectively:
"I could not route this request reliably."

That is honest, but it is not yet a useful Copilot product path.

### Live
The current Live screenshot still exposes route/mode/operation concepts and does
not implement the supplied disruption/replan visual hierarchy.

Conclusion:

The next round must be a real mobile visual/product implementation, not another
"functionally reachable" pass.

---

## P1 finding 5 — order import is still an engineering surface

Current core UI exposes:

`Reservation JSON`

That belongs in advanced/dev tooling, not the normal traveler path.

The consumer path must be:

- upload screenshot (if supported)
- paste confirmation text
- manual entry
- parsed preview
- user confirms
- only then create/lock the reservation commitment

Structured JSON may remain under Advanced / Developer tools.

---

## P1 finding 6 — activity detail is not a real screen

Current itinerary shows time/duration/type.

Still missing the dedicated traveler activity detail experience:
- opening hours
- expected cost
- transit
- why recommended
- best time
- nearby food
- replace
- add to day
- map

---

## P1 finding 7 — localization and consumer vocabulary remain incomplete

Primary/secondary screens still contain engineering/product-development copy:

- provider
- deterministic
- authority envelope
- Twin context
- hard commitments
- protected C4
- PlanVersion/JourneyTwin in secondary surfaces

Some may remain in advanced tools, but not in the default traveler journey.

The final Xiaomi acceptance must run the entire core flow in Chinese.

---

## P1 finding 8 — the morning "20/20" gate is not a full product gate

The package correctly refuses READY, but the displayed 20/20 number is easy to
misread.

For example:
- "住宿入口可见" counted PASS even though hotel compare/select is not built.
- "Live 可进入" counted PASS even though disruption -> replan is not built.

Future gates must score **completion**, not merely route visibility.

---

## Additional product logic item — 39 days + CNY 3000

If the user creates a 39-day, 2-person Xiamen trip with total budget CNY 3000,
the product should warn that the budget is likely extremely constrained.

Do not block automatically, but show:
- trip duration
- approximate daily budget
- warning
- option to adjust budget or continue intentionally

This is a traveler-facing feasibility issue, not just a backend constraint.

---

## Independent status

Snapshot H is a good structural rescue, but not a finished consumer product.

Status:

`BLOCKED_PENDING_REAL_CITY_PRODUCT_CLOSURE`
