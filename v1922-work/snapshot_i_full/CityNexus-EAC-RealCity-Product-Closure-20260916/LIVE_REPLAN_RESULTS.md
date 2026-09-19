# LIVE_REPLAN_RESULTS.md — live disruption to governed replan

## Driven on the same Xiamen journey

No fixture, no demo journey: the disruption was raised against a real stop on
`89695905-f434-447b-9477-72abffc1903d`.

| Step | Route | Result |
| --- | --- | --- |
| Raise event | `POST /journeys/{id}/events` | 201, `CLOSURE`, `USER_REPORTED`, targeted at a real stop |
| Governed replan | `POST /journeys/{id}/replans` | 201, proposal `6a555ab7…`, status `PRESENTED` |
| C4 preserved | same response | `locked_commitments_preserved = true` |
| Traveller view | `GET /replans/{id}` | diff removed/added + explanation available |
| Accept | `POST /replans/{id}/accept` | 200, status `ACCEPTED` |
| Final state | `GET /journeys/{id}/experience` | new active plan `8c4c6f6f…`, recovery consistent |

## Traveller-visible surface

`frontend/src/features/execution/LiveRecovery.tsx` is mounted on `/v8/live` and
renders exactly the language the mission requires:

* **发生了什么** — the event in traveller words (CLOSURE → "有一处地点临时关闭")
* **受影响** — the affected stop by name
* **推荐怎么改** — the proposal
* **保持不变** — "已确认的预订和到达/离开时间保持不变" when
  `locked_commitments_preserved` is true
* **接受新方案 / 仅调整今天 / 稍后提醒** — three real actions

Bilingual, with no internal vocabulary: the surface never contains
`PlanVersion`, `C4`, `semantic_key`, `deterministic gate` or a raw action enum.

## Three real bugs found and fixed while driving this

Driving the flow end to end exposed three genuine identity/evidence defects that
route-opening never would have:

1. **Replan requested mobility pairs by `place_id`** while the frozen evidence
   and the gate key on `metadata.semantic_key`, so every leg failed with
   `MOBILITY_DATA_UNAVAILABLE` ("identity drift").
   Fixed in `main.py::_activity_location`.
2. **The structural anchor had two key spellings.** Activity metadata carries
   `v12:{journey}:arrival-anchor` while the materialised Place row is stored
   under the bare `arrival-anchor`, so the runtime provider raised `KeyError`.
   Fixed in `mobility/runtime.py::_place_lookup`, which now resolves both.
3. **Stay-internal nodes have no routable Place row.** A stay-materialised plan
   contains `stay:…:check-in → stay:…:night:1`, which only exist inside the
   plan's own frozen evidence. The replan now reuses those recorded facts and
   only asks the provider for genuinely new pairs, instead of failing the whole
   recovery.
4. **Copied activities looked up travel time by `place_id`** again
   (`missing frozen travel estimate`). Fixed to use the same routing key as the
   gate.

Without a driven end-to-end run these four would all have shipped.

## Not claimed

* The disruption was injected through the API the product uses; it was not a
  real-world weather or closure feed.
* No physical-device push notification was verified.
