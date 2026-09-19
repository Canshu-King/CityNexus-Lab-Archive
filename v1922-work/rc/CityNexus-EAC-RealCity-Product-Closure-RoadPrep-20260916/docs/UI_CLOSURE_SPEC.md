# UI CLOSURE SPEC

The previous 10-screen reference package remains the visual source of direction.

Snapshot H implemented structure, not the intended product-quality UI.

## Required visual closure

### Today
Replace generic engineering hero copy with traveler-specific information:
- 厦门之旅
- current trip status
- next action
- today's plan
- booking/risk summary
- compact Copilot

No `STILL UP`, `PLANNING READY`, or `One Day in Nexus City` on the acceptance
journey.

### Create trip
Rebuild the 3 steps to look like a real mobile wizard:
- card hierarchy
- readable labels
- touch-size controls
- destination context
- sticky CTA
- Chinese-first acceptance screenshots

Do not rely on browser-default input styling.

### Plan comparison
Cards must represent actual differences.

If the backend has three candidates with the same mode/highlights, do not fake
names like "轻松版/经典版/深度版".

Either:
- generate genuinely differentiated candidates, or
- honestly label them 方案 A/B/C and show their actual differences.

### Trips
Do NOT stack itinerary + studio + booking JSON + authority text into one giant
page.

Use a trip-level structure such as:
- 行程
- 预订
- 住宿
- 花费
- 同行人/资料

or compact cards/sub-tabs.

The default Trips screen should answer:
- where am I going
- what is planned
- what needs attention
- what is confirmed

### Map
Once Xiamen coordinates are available, show Xiamen.
Before they are available, keep the truthful empty state.

### Copilot
For `鼓浪屿好玩吗` with live AI/provider available:
- useful answer
- current-trip context
- traveler actions
- no internal enum
- no authority/Twin jargon on the default view

### Hotel compare
Implement reference 09 as a real traveler page.

### Activity detail
Implement reference 08 as a real traveler page.

### Live/replan
Implement reference 10:
- current status
- next stop
- disruption
- affected
- unchanged
- recommendation
- accept / today-only / remind later

### Orders
Consumer UI:
- screenshot/paste/manual
- parsed preview
- confirm

Developer-only:
- raw structured JSON

### Consumer vocabulary rule
Move these to Advanced/Developer surfaces:
- provider evidence
- deterministic gate
- authority envelope
- Twin context
- PlanVersion
- C4

Traveler equivalents:
- 实时数据
- 已核验
- 已确认预订
- 需要重新规划
- 当前行程
