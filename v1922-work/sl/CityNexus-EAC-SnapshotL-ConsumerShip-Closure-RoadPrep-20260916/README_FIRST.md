# CityNexus Snapshot L Consumer-Ship Closure Road-Prep

Freeze the submitted package as Snapshot K:

`CityNexus-EAC-SnapshotK-RealUser-FinalClosure-20260916.zip`

Actual submitted ZIP SHA-256:

`d45accfac6b5f172f774055470ed942d3cedcccac473d1db5477fa2ca36d4360`

Independent verdict:

`BLOCKED_FOR_REAL_USER_TRIAL`

Snapshot K makes real progress:
- the two previously reported stay-calendar P0s are fixed in the submitted tests;
- activity detail now exists;
- Copilot hides several internal boundary strings;
- frontend work has finally resumed.

However, independent code review found three additional stay-calendar truth gaps
that are not covered by the submitted tests:

1. transition travel time to/from pinned windows is not reserved;
2. hotel selection can silently compress activities from later days into an earlier day;
3. overlapping pinned truths are not rejected by `_reschedule_with_carried()`.

The consumer product is also still incomplete:
- booking import is still raw JSON;
- the same-Xiamen visible UI chain is still absent;
- Copilot/Today/Live/Me remain too engineering-oriented;
- Activity Detail calls other itinerary stops "nearby" without proving spatial proximity;
- public discovery still hardcodes `trust_env=False`, risky in the user's Mihomo/proxy environment.

This Road-Prep is intended to end backend-only iteration.

Read:
- docs/INDEPENDENT_AUDIT.md
- docs/STAY_CALENDAR_V2.md
- docs/CONSUMER_SHIP_GATE.md
- docs/NETWORK_POLICY.md
- docs/EAC_TASK.md
- docs/WORKBUDDY_TASK.md

Run first:
- probes/snapshot_l_scheduler_edges.py
