# ACTIVITY_DETAIL_RESULTS.md

## Coordinates — fixed at the source

Activity Detail must use real Place coordinates. The activity metadata only
carries them on some materialisation paths, so `activity_schema()` and
`plan_schema()` now resolve the related **Place row** and merge:

```
latitude · longitude · crs · category · opening_hours
```

into the activity payload. Frontend never invents coordinates.

Regression: `test_real_place_coordinates_survive_into_the_plan_payload`
asserts that a plan whose activity metadata has no coordinates still exposes the
Place's `24.4798 / 118.0894` through the API payload.

## Cost — three distinct states

| State | Condition | UI |
| --- | --- | --- |
| KNOWN FREE | `cost_minor = 0`, evidence `KNOWN` | 免费 |
| KNOWN PAID | positive amount | `CNY 50` |
| UNKNOWN | no reliable price | 暂无价格 |

Unknown is never inferred merely from zero. Regressions:
`test_known_free_is_not_reported_as_unknown_price`,
`test_known_paid_amount_is_preserved`.

## Nearby — truthful

Carried over from Snapshot L and retained: a stop is only called 附近 when the
real coordinates put it within 1.5 km; otherwise the heading is
**这趟行程的其他停靠点** with an explicit note that they are not necessarily
walking distance, and every entry shows its real straight-line distance.

## Map action

Enabled only when coordinates exist; disabled with an honest explanation when
they do not.

## Fields shown

title · day and time slot · duration · travel from previous stop · cost ·
opening hours · category · coordinates · nearby stops · actions (map, ask
Copilot, open another stop).

Anything the backend did not supply is shown as 暂无… rather than invented.
