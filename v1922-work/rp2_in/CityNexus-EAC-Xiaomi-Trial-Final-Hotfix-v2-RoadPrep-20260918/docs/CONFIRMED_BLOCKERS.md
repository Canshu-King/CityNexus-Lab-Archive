# Confirmed blockers after WorkBuddy v2 recheck

## P0/P1 — R1-a: booking-first closure can be falsely rejected as protected

Current code:

```python
if trigger_event.event_type in {"CLOSURE", "WEATHER"} and    trigger_event.affected_activity_id in {row.activity_id for row in c4_rows}:
```

If:
- trigger_event.affected_activity_id is None
- an imported booking/commitment has activity_id=None

then:

`None in {None}`

is True, and the closure is incorrectly rejected as protected.

Required:
- only run membership protection check when affected_activity_id is non-null;
- after semantic impact resolution identifies selected_activity_id, persist/use
  that resolved identity for protection logic;
- add regression for "booking imported first -> mutable POI closure".

## P1 — R1-b: closure target resolution is nondeterministic

WorkBuddy observed the same command sometimes resolves the target and sometimes
returns unresolved_references.

Required:
- semantic compiler may propose the target;
- if unresolved, use deterministic title/place matching against the current
  journey;
- never silently guess the first/current activity;
- if deterministic match is ambiguous, ask for clarification.

## P1 — R2: indistinguishable Live replan cards

Current `LiveRecovery.tsx` renders every PRESENTED/GENERATED proposal with:
- same heading;
- same protected-commitment copy;
- only removed/added counts.

Required:
- dedupe proposals with identical semantic diff;
- if alternatives are genuinely different, show actual traveler-facing
  differences;
- give each card a meaningful option label;
- fix the `移除 1 项 ·` trailing separator when added=0.

## P1 — R3: booking review still leaks internal enums

Default JourneyInboxWorkbench still renders:
- item.role
- draft.artifact_type
- draft.status
- draft.extraction_mode
- anchor_role
- payment_status
- UNKNOWN
- provider_key such as `manual-entry`

Required:
- humanize in default consumer UI;
- raw values only under Advanced/Developer;
- correct misleading comment in V8Experience.

## P1 — R4: Copilot mission timeline leaks raw tool_name

Current default rail still renders:

`<code>{event.tool_name}</code>`

outside Advanced details.

Required:
- use human toolLabels on the default rail;
- if unmapped, show human status/friendly label;
- raw tool_name only in Advanced.

## P1 — R5: Trips/Activity Detail expose raw taxonomy

Examples:
- check_out
- departure
- museum

Required:
- one shared traveler label map;
- use it in TripItinerary, ActivityDetail, disruption notice;
- Chinese-first canonical path;
- unknown value may fall back safely, but common roles must be localized.

## P1 — R6: Copilot dock obscures sheets / Live content

Current:
- dock z-index 25
- AI sheet backdrop z-index 20
- dock does not know modal/sheet state

Required:
- dock must auto-minimize/hide or sit below critical sheet while one is open;
- verify 390x844 and Xiaomi-like viewport;
- no primary CTA or proposal card may be obscured.

## P1 — R8: AI run-success baseline still fails open

Current existingPlanIds():

- fetch failure -> empty set
- later successful GET of old plans -> old plans appear "new"

Required:
- baseline plan snapshot failure means run attribution is indeterminate;
- terminal state must NOT be success;
- success requires proof attributable to the current run.

## Product-quality / non-blocking but should close if cheap

### R7 hotel comparison
- do not fabricate differences;
- add address/area/provider identity where real;
- if evidence cannot rank, say so.

### R9 package hygiene
- mark old evidence PRE_HOTFIX/SUPERSEDED;
- include required schema/test fixture material for replay where practical.
