# V19.2 Acceptance Matrix

| ID | Acceptance test | Required result |
|---|---|---|
| A01 | Active C4 + generate | no candidate that authoritative validator immediately rejects for same C4/evidence |
| A02 | Active C4 + select + booking | select/booking agree on feasibility using the same snapshot/constraints |
| A03 | ARRIVAL C4 + start | never 500; ACTIVE or explicit recoverable 4xx/state |
| A04 | DEPARTURE/MID_TRIP C4 start | no regression |
| A05 | duplicate C4 confirmation ref | idempotent/rejected, never duplicate active commitments |
| A06 | `I don't need a wheelchair, I can walk` | no HARD STEP_FREE_REQUIRED |
| A07 | `朋友说我可能需要轮椅，但我不这么认为` | no HARD STEP_FREE_REQUIRED |
| A08 | third-party/facility/speculation corpus | 0 false-HARD from local fallback |
| A09 | permanent language | TRAVELER scope reachable when semantics are explicit |
| A10 | this-trip language | JOURNEY scope reachable |
| A11 | same code at two scopes | both survive canonicalization |
| A12 | `toilets:wheelchair=yes` | only toilet-scoped fact; not whole step-free proof |
| A13 | `wheelchair=yes + step_count=5` | ACCESSIBILITY_CONFLICT |
| A14 | `{"wheelchair":["yes"]}` | normalized; not silently dropped |
| A15 | route step-free without route proof | UNKNOWN / NEEDS_LIVE_EVIDENCE |
| A16 | top-level supported evidence vs nested tags | same intended requirement result |
| A17 | negative/absurd walking value | reject/clarify |
| A18 | `1 公里` | 1000m or explicit rejection; never 1m |
| A19 | invalid 14:00->12:00 window | reject/clarify; never usable window |
| A20 | interval constraints | actual feasibility changes at the boundary |
| A21 | ACTIVE journey + new HARD need | reevaluation + proposal/conflict state |
| A22 | failed regeneration/revalidation | old candidate not still presented as viable current plan |
| A23 | runtime vs checked-in OpenAPI | exact parity for supported path surface |
| A24 | broad regression | no unexplained trial-critical failure |
| A25 | 390x844 and 430x932 | core flow usable, no horizontal overflow |
| A26 | real-phone geolocation | update succeeds or shows an actionable permission/error state |
| A27 | PWA standalone | install + launch passes under HTTPS/secure context |
| A28 | SSE reconnect | state recovers without duplicate/corrupt events |
| A29 | release truth | V19.2 top-level reports match final tree |
| A30 | fresh extract | packaged artifact reproduces focused gate once from a clean extract |
