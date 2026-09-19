# WorkBuddy next delta after EAC final package exists

Do NOT rerun the whole overnight audit.

When EAC produces its final continuation package:

1. compare final EAC changed files against WB-O1;
2. rerun only WB-H1 through WB-H5;
3. audit the final `VISIBLE_UI_TRACE.json`;
4. verify one same-Xiamen journey;
5. inspect final Today / Trips / Booking / Copilot / Hotels / Live screenshots;
6. check that positive offline/duplicate behaviors remain intact.

Final verdict:

`BLOCKED`

or

`WORKBUDDY_ACCEPTS_FOR_XIAOMI_13_ULTRA_TRIAL`

Do not use "has a commit" as a readiness condition.
Use reproducible product evidence.
