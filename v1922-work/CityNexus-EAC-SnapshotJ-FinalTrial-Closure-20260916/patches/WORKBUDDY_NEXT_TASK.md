# WorkBuddy next targeted delta

Read-only.

Freeze Snapshot J:
CityNexus-EAC-FinalConsumer-Truth-UX-Closure-20260916(1).zip

Do not modify main tree.
Do not rerun the historical giant corpus.

Target only these checks:

1. Stay structural operations
   - CHECK_IN preserved
   - CHECK_OUT preserved
   - LUGGAGE_DROP preserved when required
   - nights preserved
   - no duplicate structural nodes

2. Locked truth
   - hotel selection does not move locked/C4 activities
   - impossible conflicts are explicit

3. Replan reason
   - REPLAN_TARGET_UNRESOLVED reachable
   - REPLAN_PROTECTED_CONFLICT reachable where applicable
   - REPLAN_NO_ALTERNATIVE reachable
   - generic fallback does not mask them

4. Ambiguous target
   - no explicit/grounded target -> clarification/review
   - no arbitrary first-activity guess

5. Stay + recovery
   - choose hotel
   - close mutable POI
   - no mobility identity mismatch
   - material repair or honest NO_ALTERNATIVE

6. Visible UI trace
   - same Xiamen journey id
   - create/select hotel/import booking/accept replan are browser actions
   - no demo reset

7. Product/UI
   - activity detail exists
   - consumer order import exists
   - Copilot default view is traveler-facing
   - Chinese-first
   - screenshots materially closer to supplied reference UI

Final verdict:

BLOCKED

or

SNAPSHOT_ACCEPTED_FOR_XIAOMI_13_ULTRA_TRIAL
