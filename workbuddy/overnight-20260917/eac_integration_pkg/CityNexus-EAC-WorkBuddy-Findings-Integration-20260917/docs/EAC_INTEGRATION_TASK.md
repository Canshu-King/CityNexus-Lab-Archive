# EAC Integration Task — absorb WB-O1 without regressing current work

Authoritative repository:

D:\moodle\CityNexus

Use:
- the CURRENT repository state;
- current overnight-continuation work;
- WB-O1 only as independent evidence/reference.

Do NOT roll back to the WorkBuddy 01:15 snapshot.

==================================================
STEP 1 — CURRENT-STATE REVALIDATION
==================================================

Re-test these against CURRENT code:

1. AI planning false-success
2. booking natural-language / raw JSON default path
3. price/origin/destination preservation
4. Copilot raw enum/provider leaks
5. Today/Copilot no-plan empty states
6. hotel no-candidate pseudo-evidence

Create:

`WORKBUDDY_FINDINGS_REVALIDATION.md`

Each item:
- STILL_OPEN
- FIXED_BY_CURRENT_EAC
- PARTIALLY_FIXED
- NOT_REPRODUCIBLE

with screenshot/trace.

==================================================
STEP 2 — PORT ONLY STILL-OPEN FIXES
==================================================

Use WorkBuddy patches as references, NOT as blind apply artifacts.

For each still-open issue:
- port against current source;
- preserve current architecture;
- avoid reverting newer EAC changes.

==================================================
STEP 3 — ROOT-CAUSE COMPLETION
==================================================

AI:
- terminal success requires a real plan artifact.

Booking:
- consumer text/manual import first;
- confirmed price/location facts survive backend confirm.

Copilot:
- no raw enums / model brands / semantic runtime in default UI.

Today:
- useful empty/current-trip state.

Hotels:
- no pseudo-evidence when no real option exists.

==================================================
STEP 4 — REGRESSION
==================================================

Preserve positive behavior:
- offline read-only mode;
- duplicate protection;
- honest Map/Trips empty states;
- protected replan semantics.

Run current canonical same-Xiamen flow after fixes.

Do not declare success from isolated component screenshots alone.
