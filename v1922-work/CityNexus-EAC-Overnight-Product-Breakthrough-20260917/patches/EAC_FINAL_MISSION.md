# EAC Final Mission — Snapshot M

Authoritative repository:

D:\moodle\CityNexus

Freeze:
CityNexus-EAC-SnapshotL-ConsumerShip-Closure-20260916.zip

Read:
README_FIRST.md
docs/INDEPENDENT_AUDIT.md
docs/SCHEDULER_TRUTH_V3.md
docs/ACTIVITY_DETAIL_TRUTH.md
docs/NETWORK_POLICY_V2.md
docs/PRODUCT_FINISH_GATE.md

Run:
probes/snapshot_m_truth_edges.py

FIRST.

Do not start unrelated architecture work.

==================================================
P0 — NO SILENT ACTIVITY DURATION SHRINK
==================================================

Remove the policy that silently truncates a planned visit to fit the hotel.

Preserve original duration.

If the same-day calendar cannot fit it:
- explicit conflict; or
- governed visible adjustment proposal.

Add permanent repository regression tests.

==================================================
P0 — PINNED-TO-PINNED MOBILITY TRUTH
==================================================

Validate travel reachability between consecutive pinned truths.

Non-overlap is not enough.

If:
previous.end + travel > next.start
then:
- explicit pinned mobility conflict;
- option cannot claim hard-constraint pass.

Add permanent tests.

==================================================
P1 — ACTIVITY DETAIL DATA TRUTH
==================================================

Join/expose Place coordinates to Activity Detail.

Fix known-free cost rendering:
- FREE_KNOWN / known zero -> 免费
- known paid -> amount
- unknown -> 暂无价格

Do not fabricate missing facts.

==================================================
P1 — NETWORK CONTRACT
==================================================

Make AUTO implementation match its documentation.

Either implement bounded proxy->direct fallback or simplify the documentation to
the actual proxy-aware behaviour.

==================================================
P0/P1 — PROVE HOTEL -> LIVE RECOVERY
==================================================

Use one real Xiamen multi-day plan:

choose hotel
-> reload
-> intended day structure remains
-> original durations remain
-> check-in/stay/check-out valid
-> pinned travel valid
-> explicit mutable Xiamen POI disruption
-> material replan or honest NO_ALTERNATIVE
-> no mobility identity failure

==================================================
NOW STOP BACKEND-ONLY ITERATION
==================================================

After the narrow truth items above, spend the majority of the round on the
consumer product.

Implement:
- consumer booking import;
- traveler-facing Today;
- real multi-day Trips;
- useful Copilot;
- clean Me;
- focused Live;
- budget advisory;
- material reference-UI implementation.

==================================================
VISIBLE UI ACCEPTANCE
==================================================

Complete docs/PRODUCT_FINISH_GATE.md in one visible browser journey.

Produce:
- VISIBLE_UI_TRACE.json
- screenshots for 390x844, 430x932, Xiaomi-like viewport
- PRODUCT_ACCEPTANCE_RESULTS.md

Critical actions must be UI actions.

==================================================
FINAL VERDICT
==================================================

Only:

BLOCKED_FOR_REAL_USER_TRIAL

or

READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

Target:

CityNexus-EAC-SnapshotM-TruthToProduct-FinalClosure-20260917.zip

Do not return another backend-only package unless a real external dependency
prevents all consumer UI work.
