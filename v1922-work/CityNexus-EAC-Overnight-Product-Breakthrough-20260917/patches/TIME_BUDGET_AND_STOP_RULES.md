# TIME BUDGET AND STOP RULES

This is an 8–9 hour run.

The purpose of the time budget is to prevent another night where all effort is
absorbed by backend edge cases while the product remains unusable.

## Suggested allocation

- 0:00–1:30 — Snapshot M truth closure + permanent tests
- 1:30–3:00 — booking import + Activity Detail truth + hotel flow
- 3:00–5:00 — Today / Trips / Copilot / Live / Me consumer rebuild
- 5:00–6:30 — same-Xiamen visible UI chain
- 6:30–7:30 — failure states + hostile loops
- 7:30–8:30 — mobile visual polish + screenshots + regression
- final 30 min — package evidence and final verdict

These are guides, not hard timers.

## Backend stop rule

After the known P0 truth blockers are fixed:

- do not continue searching for hypothetical low-probability scheduler corner
  cases unless one appears during the actual product flow;
- prioritize failures that a real traveler can hit.

## External-service rule

If DeepSeek/provider access is temporarily unavailable:
- implement all UI/product paths;
- preserve honest failure state;
- test with deterministic/local evidence where appropriate;
- keep moving.

Do not waste the entire night retrying one public API.

## Green-build rule

A green build is the beginning of user testing, not the end of work.

If all required tasks finish early:
- continue through `AUTONOMOUS_PRODUCT_LAB.md`;
- keep finding and fixing real product weaknesses until the overnight window is
  substantially used.
