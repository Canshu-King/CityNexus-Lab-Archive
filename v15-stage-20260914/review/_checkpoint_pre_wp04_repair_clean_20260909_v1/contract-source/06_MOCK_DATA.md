# 06 - Deterministic Mock Data

All mock data is synthetic and intentionally deterministic. It exists to make the coursework demo reproducible without network access.

Demo city code: `CNX-DEMO`
Timezone: `Asia/Shanghai`
Currency: `CNY`

## Canonical disruption scenario

Traveler: Alex Chen (synthetic demo user)

Journey: `One Day in Nexus City`

- 09:00-19:00 local time
- budget CNY 500.00
- preferences: culture, local food, waterfront
- hard constraint: preserve the paid 15:30 river cruise commitment
- soft constraint: minimise unnecessary plan changes

At 13:10 a CLOSURE event makes `Tech Art Center` unavailable. The active plan contains a paid/locked 15:30 river cruise. The replanner must replace or remove the disrupted activity while preserving the locked cruise and keeping the remaining schedule feasible.

Expected deterministic behavior:

1. Current/completed prefix remains unchanged.
2. Tech Art Center cannot remain in a feasible candidate after closure.
3. River Cruise remains at its committed time.
4. At least one alternative candidate inserts City Park or another available cultural/waterfront activity.
5. Candidate score includes all eight source-backed utility components.
6. No candidate may pass if a hard constraint fails or a locked commitment is lost.
7. The user must accept a ReplanProposal before it becomes active.
8. Disabling the AI adapter changes explanation mode but not feasibility.
