# Confirmed blockers from WorkBuddy final delta

## B1 — final evidence is stale / contradictory

The final Copilot place-answer fix was made after the submitted canonical trace.

Required:
- run one NEW canonical same-Xiamen visible flow after all fixes;
- capture the Copilot place question after the final code;
- correct ledger/archive references;
- no stale screenshot used as final proof.

## B2 — Me page still exposes internal policy

Default Me still shows:
- 权限边界
- ADVISORY
- internal city code

Required:
- move policy/delegation internals behind Advanced/Developer;
- show traveler profile/preferences/bookings/settings on default Me.

## B3 — price and budget truth defects

Fix all:
1. known free attraction -> `免费`
2. known paid -> actual amount
3. unknown -> `暂无价格`
4. partial price coverage must NOT claim total `预算内/超预算`
5. extreme low-budget long-trip advisory must exist

Example:
39 days / 2 people / CNY 3000

Show:
- approximate per-day / per-person sanity figure;
- warning;
- edit budget;
- continue intentionally.

## B4 — secondary Wallet route remains developer-shaped

`/v8/bookings` still leaks:
- Journey Memory
- UNKNOWN_REALTIME
- C4/internal labels
- raw JSON-first workflow

Required:
- normal traveler flow = text/manual/import + preview + confirm;
- raw JSON only under Advanced;
- JSON parse failure gets visible localized feedback;
- amount/origin/destination survive confirm.

## B5 — direct deep links can blank

Support or redirect:
- `/v8/today`
- `/v8/copilot`

with active journey and no active journey.

No blank body.

## B6 — AI planning success must be run-specific

Do not use:
`plans.length > 0`

as proof the NEW planning run succeeded.

Required:
- snapshot candidate ids/count before the run;
- success only when the current run creates attributable new candidate artifact(s),
  or use an explicit backend run/result contract;
- old ACTIVE/SELECTED/SUPERSEDED plans must not satisfy a failed new run.

## Secondary cleanup

Copilot/Agent default traveler surfaces must hide:
- What-if Studio
- JourneyTwin
- deterministic
- raw policy decision/enums

Advanced may retain them.

## Evidence assertion cleanup

Do not accept:
- `undefined in=undefined out=undefined` as stay truth;
- `Trips=7 / backend=14 / live=text` as "consistent" without a defined mapping.

Define what is being compared and prove it.
