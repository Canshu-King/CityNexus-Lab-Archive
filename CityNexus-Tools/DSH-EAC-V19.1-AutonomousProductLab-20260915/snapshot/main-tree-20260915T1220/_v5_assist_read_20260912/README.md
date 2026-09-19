# CityNexus Live Journey Autopilot V5 — GPT Assist

Start with `CODEX_NEXT_GOAL.txt`.

This package is based on an external review of the V4 final checkpoint. It deliberately does not contain a main-code patch. Codex should verify each finding against the current `D:\moodle\CityNexus` working tree and solve the implementation itself.

External review summary:

1. V4 is a strong real milestone: CP-SAT V2 exists, the standing mission and Guardian exist, Impact Intelligence uses RapidFuzz/Shapely, and the browser flow is backend-connected.
2. The current Guardian flagship is still not truly model-orchestrated. `scan_guardian()` creates a deterministic `citynexus-guardian / deterministic-recovery-controller-v1` AgentRun and hard-codes `inspect_twin -> request_replan -> accept_replan`.
3. The current browser "proactive" scenario itself creates WEATHER and TRAFFIC_DELAY events and then manually POSTs `/guardian/scan`. There is no autonomous provider pulse/scheduler.
4. `cooldown_until` is stored but not enforced.
5. Mission Compiler V2 currently allows a model draft to widen explicit numeric authority and potentially override explicit protection with a mutable interpretation. Unresolved model references are not persisted.
6. The V4 report says DeepSeek/Hermes live execution was not run in that iteration. V5 should make the live runtime path a first-class proof when credentials/runtime are available.
7. The delivered V4 archive also contains cache artifacts despite the hygiene claim. Treat final packaging as a real gate.

The V5 product target is not "another Guardian button". It is a live Journey Autopilot:
city signals arrive -> Guardian pulse evaluates them -> configured AI runtime reasons -> CP-SAT replans -> policy executes -> Control Tower updates without another user command.
