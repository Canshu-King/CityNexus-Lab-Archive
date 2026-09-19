# CityNexus V19.2.5 C4 Interior Truth Hotfix Road-Prep

Snapshot G (V19.2.4) is materially improved and is accepted for **physical-device plumbing precheck**.

However, an extra independent edge probe found one narrow shared-gate truth gap:

- a `MID_TRIP` C4 anchor before ARRIVAL can still pass the shared feasibility gate;
- a `MID_TRIP` C4 anchor after DEPARTURE can still pass;
- a role-less interior booking/order C4 can also escape ARRIVAL/DEPARTURE boundaries.

The generator already refuses these schedules. The defect is the shared deterministic gate used as
defense-in-depth for imported, persisted, edited and stale plans.

This hotfix is intentionally tiny. Do not start V19.3.

Recommended:
1. Apply/port the one-file starter patch.
2. Add regression tests for the five probe cases.
3. Re-run only the relevant V19.2.4 gate + broad regression.
4. Let WorkBuddy perform a narrow delta.
5. In parallel, the user may perform phone **plumbing precheck** (HTTPS/PWA/GPS/SSE) but not yet
   call a multi-anchor outdoor Shadow Journey fully accepted.
