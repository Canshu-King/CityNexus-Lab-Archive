# EAC Snapshot L Consumer-Ship Closure

Authoritative repository:

D:\moodle\CityNexus

Freeze:
CityNexus-EAC-SnapshotK-RealUser-FinalClosure-20260916.zip

Read:
README_FIRST.md
docs/INDEPENDENT_AUDIT.md
docs/STAY_CALENDAR_V2.md
docs/NETWORK_POLICY.md
docs/CONSUMER_SHIP_GATE.md

Run first:
probes/snapshot_l_scheduler_edges.py

Do not start unrelated architecture work.

==================================================
P0 — STAY CALENDAR V2
==================================================

Fix all three independent findings:

1. reserve inbound/outbound travel around pinned boundaries;
2. preserve original local-day semantics; no silent cross-day compaction;
3. reject pinned-vs-pinned overlap explicitly.

Do not solve this with another cosmetic cursor patch.

Keep all existing Snapshot K timeline tests green.

==================================================
P0 — PROVE HOTEL -> RECOVERY ON THE SAME REAL PLAN
==================================================

After the calendar fix:

real Xiamen multi-day plan
-> choose hotel
-> reload
-> same POIs on their intended days
-> CHECK_IN/STAY/CHECK_OUT valid
-> locked/C4 truth unchanged
-> explicit mutable POI closure
-> material replan or honest NO_ALTERNATIVE
-> no mobility identity error

==================================================
P1 — CONFIGURABLE PUBLIC NETWORK POLICY
==================================================

Remove hard-coded product dependence on `trust_env=False`.

Support direct/proxy-aware configuration suitable for the user's Mihomo/network
environment.

Do not expose secrets.

==================================================
P1 — STOP BACKEND-ONLY ITERATION AND SHIP THE CONSUMER FLOW
==================================================

Finish:
- booking text/manual import + preview + confirm;
- Activity Detail truth wording (`附近` only when actually spatially near);
- useful Copilot;
- Today/Trips/Live/Me traveler-facing cleanup;
- material implementation of the 10-screen UI direction;
- Chinese-first canonical path;
- budget sanity advisory.

==================================================
VISIBLE UI ACCEPTANCE
==================================================

Drive the entire same-Xiamen flow through visible UI.

Create `VISIBLE_UI_TRACE.json`.

API calls may prepare an explicit disruption fixture or inspect final truth,
but may not replace:
- create;
- plan selection;
- hotel selection;
- booking confirmation;
- replan acceptance.

Required screenshots:
- Today
- Create 1/2/3
- AI intent/progress
- plan compare
- Trips
- Activity detail
- Hotels
- Booking import preview
- Map
- Copilot answer
- Live disruption
- Live after accept
- error/offline

390x844, 430x932, Xiaomi-like viewport.

==================================================
FINAL
==================================================

Verdict only:
BLOCKED_FOR_REAL_USER_TRIAL
or
READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

Target:
CityNexus-EAC-SnapshotL-ConsumerShip-Closure-20260916.zip

Do not return another backend-only package unless a hard external dependency
truly blocks all browser/product work.
