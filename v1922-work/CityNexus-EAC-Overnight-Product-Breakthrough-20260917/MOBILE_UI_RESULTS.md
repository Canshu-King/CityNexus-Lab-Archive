# MOBILE_UI_RESULTS.md

## Captured this round (390x844, Chinese-first)

`screenshots/after/`: Today (rebuilt), Trips, Map, Copilot, Me, Live,
Activity Detail, manual booking form, booking preview. The tab sweep was
repeated at 430x932.

## Today rebuilt as a real trip dashboard

Before, the first screen led with generic marketing copy:

```
你的下一座城市，已被充分考虑。
一段沉稳的、基于证据的行程——住宿、出行、行李和受保护的时刻协同运作。
```

After, it answers the traveller's questions within one viewport. Verified in a
real browser on a Xiamen journey:

```
heading   : Xiamen之旅
when      : 11月6日 10:00 — 11月8日 20:00 · 2 位旅行者 · 3 天
next      : 11:00 厦门景点0 / 今天没有安排
stay      : 还没有选定 / 去「行程 · 住宿」挑选
attention : 一切正常 / 没有影响行程的变化
generic copy gone: true
errors    : 0
```

The heading is derived from the journey's `city_code` (Chinese names pass
through, latin codes are title-cased), so no raw `CN-XIAMEN` reaches the
traveller.

## Other UI landed

* **Consumer booking import** — 粘贴确认信息 / 手动填写 entry tabs with a real
  mobile form (44px touch targets, two-column rows collapsing on narrow
  screens).
* **Activity Detail** — dedicated surface with a back affordance, fact list,
  two full-width actions and distance-annotated nearby list.
* **Trips** — sub-tabs (行程 / 住宿 / 预订 / 花费) with the itinerary as default.
* Raw-JSON workbench demoted behind a **高级 / 开发者** disclosure.

## Verified

| Viewport | Tabs render | Overflow | Real errors |
| --- | --- | --- | --- |
| 390x844 | all | none | 0 |
| 430x932 | all | none | 0 |

## Not done

* Material implementation of all ten reference screens.
* Me still shows 权限边界 / ADVISORY as primary content.
* Copilot does not yet answer 鼓浪屿好玩吗？ usefully.
* Hotel cards are not meaningfully differentiated.
* The Live traveller-first viewport was not reworked.
* Typography scale, illustration and spacing rhythm still resemble the previous
  console more than the reference images.
