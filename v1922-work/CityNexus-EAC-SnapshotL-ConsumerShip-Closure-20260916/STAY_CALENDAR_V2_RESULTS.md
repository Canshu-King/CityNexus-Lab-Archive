# STAY_CALENDAR_V2_RESULTS.md

## The three gaps, reproduced first

`probes/snapshot_l_scheduler_edges.py` was run against the authoritative
backend **before** any change:

```
FAIL case_inbound_outbound_pinned_travel
  => first flexible stop did not reserve travel from ARRIVAL
FAIL case_pinned_overlap_rejected
  => overlapping pinned CHECK_IN and locked activity were emitted
FAIL case_no_silent_cross_day_compaction
  => Day-2 activity was silently moved to another day by hotel selection
```

All three reproduced exactly as the independent review described.

## What changed

`_reschedule_with_carried()` was rewritten again, this time around the
`STAY_CALENDAR_V2` contract rather than around overlap avoidance.

### 1. Transition travel time around pinned boundaries

Free intervals are no longer bare `[start, end]` pairs. Each interval carries
its **bounding nodes**:

```
[left_node, free_start, free_end, right_node]
```

so placement can reserve both legs:

```
candidate = free_start + travel(left, activity)
candidate + duration + travel(activity, right) <= free_end
```

The first flexible stop after ARRIVAL now includes the inbound leg, and the last
one before CHECK_IN leaves the outbound leg.

### 2. Day semantics — no silent cross-day compaction

Each flexible activity keeps its **original local date**. A slot on another day
is not eligible, so choosing a hotel can no longer compress Day-2 content into
Day 1. When the original duration does not fit the same-day window the visit is
**shortened to fit** (never below 15 minutes); when even that is impossible the
calendar raises `STAY_ITINERARY_CONFLICT:NO_SAME_DAY_SLOT:<key>` instead of
moving the traveller to another day or dropping the stop.

### 3. Pinned truth is validated before anything is placed

`_reschedule_with_carried()` now checks every pinned interval up front and
rejects:

```
INVALID_WINDOW · PINNED_BEFORE_ARRIVAL · PINNED_AFTER_DEPARTURE
PINNED_OVERLAP  · CHECK_IN_AFTER_FIRST_STAY · CHECK_OUT_BEFORE_LAST_STAY
```

as `STAY_PINNED_CONFLICT:<reasons>`. An overlapping pinned CHECK_IN and locked
activity can no longer be emitted.

### 4. Superseded-property operations are dropped, not run in parallel

While making the calendar reject pinned overlap, a real defect surfaced: when
the traveller switches hotel, the *previous* property's luggage-drop / check-in
/ night / check-out nodes were still being carried forward and ran at the same
clock times as the new hotel's. `_offer_of()` extracts the property from a
structural key (`stay:{offer}:check-in`), and operations belonging to a
different property than the one being selected are now dropped as superseded.

## Verification

Probe, after the fix:

```
PASS case_inbound_outbound_pinned_travel
PASS case_pinned_overlap_rejected
PASS case_no_silent_cross_day_compaction
```

Snapshot K's own timeline suite is still green (all ten invariants), and
Snapshot J's B1–B4 suite is still green.

## Network policy (P1)

The hard-coded `trust_env=False` is gone. Three public-provider clients
(`real_city.py` ×2, `stay_osm.py`) now read a configurable policy:

| `CITYNEXUS_PROVIDER_NETWORK_MODE` | Behaviour |
| --- | --- |
| `auto` (default) | honour the environment/proxy configuration — correct for a Mihomo setup |
| `env_proxy` | always honour the environment proxy |
| `direct` | never use the environment proxy |

Implemented in `provider_config.py` as `provider_network_mode()` and
`trust_environment_for_public_providers()`. No credentials are read, logged or
printed. Default resolved to `auto` / `trust_env=True`.

## Truthfulness fix carried in the same round

Activity Detail previously labelled every other stop on the plan as 附近
("nearby"). It now computes straight-line distance from the real coordinates and
only calls stops "nearby" when at least one is within 1.5 km; otherwise the
heading is 这趟行程的其他停靠点 and the note says plainly that they are **not
necessarily within walking distance**. Each entry shows its real distance.
