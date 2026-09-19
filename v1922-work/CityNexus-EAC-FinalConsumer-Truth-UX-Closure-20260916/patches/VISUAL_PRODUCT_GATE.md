# Visual product gate

Use the previous 10-screen UI reference package as the visual direction.

## Core rule

Functional PASS and Visual/Product PASS are separate.

EAC may self-certify:
- route works
- state transitions
- API results
- no runtime crash

EAC may NOT self-certify final visual quality merely because:
- page loaded
- no horizontal overflow
- button exists.

## Required visual targets

### Today
Must answer:
- what trip am I on?
- what do I do next?
- what needs attention?

Use actual Xiamen trip title and status.
Remove generic hero copy.

### Trips
Must feel like a trip control center, not raw records.

Subsections:
- 行程
- 住宿
- 预订
- 花费

Keep each screen concise.

### Copilot
Hide by default:
- 权限边界
- 语义边界
- UNVERIFIED / UNKNOWN / NONESEARCH
- What-if Studio
- protected/internal vocabulary

Expose an "Advanced details" affordance only if needed.

### Hotels
Cards should be visually differentiated.
Show truthful unknowns without making every card look identical.

### Live
Top half should focus on:
- current state
- next stop
- disruption
- proposed change
- actions.

Move mode/risk/guardian/evidence diagnostics behind an advanced section.

### Chinese-first
The canonical acceptance screenshots must not contain large English blocks such as:
- Check in
- Overnight
- Sunday / Friday
unless the original provider name is genuinely English.

Translate product labels.

## Screenshot set required

390x844 and Xiaomi-like viewport:

- Today
- Create step 1/2/3
- AI intent
- AI progress
- Plan compare
- Trips
- Activity detail
- Hotels
- Bookings import preview
- Map
- Copilot answer
- Live disruption
- Live after accept
- Error/offline state
