# Independent audit of Snapshot L

## Confirmed progress

Snapshot L is a genuine new package and not a duplicate.

Confirmed from source and submitted evidence:

- Stay Calendar V2 reserves travel around flexible activities and pinned
  boundaries.
- Cross-day compaction is blocked in the tested scenario.
- Pinned overlap is rejected.
- Old-hotel structural operations are filtered when switching property.
- `CITYNEXUS_PROVIDER_NETWORK_MODE` now exists with `auto`, `env_proxy`, and
  `direct`.
- Activity Detail computes real straight-line distance before using "附近".
- Frontend build and broad backend regression are reported green.
- EAC correctly refuses READY.

## New truth gap M1 — hotel selection may silently shorten a planned activity

The scheduler now contains:

```python
kept = min(duration, available)
```

with a minimum of only 15 minutes.

Therefore a two-hour or three-hour planned visit can be silently reduced to
15–20 minutes simply to make a hotel fit.

This is a material itinerary change.

The product contract previously required:
- preserve the user's itinerary where possible;
- otherwise return a conflict or governed adjustment proposal.

Choosing a hotel is not consent to turn a two-hour museum visit into fifteen
minutes.

Required:
- preserve original duration by default;
- if the full duration does not fit, do not silently shrink it;
- return an explicit `STAY_ACTIVITY_DURATION_CONFLICT`, or build a visible
  proposed adjustment requiring user acceptance.

## New truth gap M2 — pinned-to-pinned travel can still be physically impossible

Snapshot L validates pinned intervals for overlap, but not for travel time.

Example:

- CHECK_IN ends 12:00 at hotel A
- locked/C4 activity starts 12:10 several kilometres away

The intervals do not overlap, so the pinned calendar itself accepts them.

But ten minutes may be insufficient to travel between the two pinned truths.

The current transition reservation only applies while placing flexible items.

Required:
- every consecutive pinned pair must be reachable using valid mobility
  evidence/allowed mode assumptions;
- otherwise return an explicit pinned mobility conflict;
- do not present an accommodation option as hard-constraint-safe when its pinned
  schedule is physically unreachable.

## New product truth gap M3 — Activity Detail loses Place coordinates

The current `ActivityDetail.tsx` expects:

- `activity.metadata.latitude`
- `activity.metadata.longitude`

But `_active_plan_payload()` only returns Activity metadata and does not enrich
the activity payload from its related `Place` coordinates.

The submitted real browser evidence confirms the symptom:

`厦门景点0 | 暂无坐标`

and the "在地图上查看" action is disabled.

Yet CityNexus already stores coordinates on `Place`.

Required:
- expose real Place coordinates in the active-plan activity payload, or provide
  a dedicated activity-detail API that joins the Place;
- never duplicate/fabricate coordinates in frontend code.

## New product truth gap M4 — known free activity is rendered as "price unavailable"

Activity Detail declares price known only when:

```ts
amount_minor > 0
```

So a provider-backed, known-free attraction (`0 CNY`) is displayed as:

`暂无价格`

instead of:

`免费`

Use the explicit price/cost evidence status, not positive amount, to distinguish:

- known free;
- known paid price;
- unknown price.

## Network-policy claim mismatch

`provider_config.py` comments describe AUTO as:

> honour env/proxy first, then a bounded direct retry

but the implementation only returns `trust_env=True`.

No bounded direct retry is implemented in the submitted public-provider clients.

Either:
- implement the documented bounded fallback; or
- change the contract/documentation so AUTO truthfully means "honour environment
  proxy".

Do not claim retry behaviour that does not exist.

## Durable-test gap

The Snapshot L edge probe is packaged evidence, but the changed-file list adds no
new authoritative backend test file for the three scheduler fixes.

The regressions should be converted into permanent repository tests so later
work cannot reintroduce them.

## Product status remains blocked

The package itself correctly admits:

- no full visible create -> plan -> hotel -> booking -> Live -> accept chain;
- no consumer booking import;
- Today / Live / Me cleanup partial;
- reference UI implementation partial;
- budget advisory missing;
- no physical Xiaomi test.

Independent verdict remains:

`BLOCKED_FOR_REAL_USER_TRIAL`
