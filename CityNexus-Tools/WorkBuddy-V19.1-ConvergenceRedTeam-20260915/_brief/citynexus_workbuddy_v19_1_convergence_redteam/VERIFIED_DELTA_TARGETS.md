# Verified Delta Targets

Previous red-team later-snapshot findings to re-check:

D0. `app.main` import blocker because `capability_payload` was missing.
D1. HARD accessibility severity downgrade guard was ineffective.
D2. text-global negation/history logic caused false positives and false negatives.
D3. duplicate capability codes could coexist at different severities.
D4. walking numeric forms were under-parsed.
D5. rest/nap time-window forms were under-parsed.
D6. capability rules reached a feasibility gate that did not interpret them.
D7. TRAVELER scope was unreachable from natural language.

Additional lifecycle findings from the earlier baseline:

- capability declaration mid-trip could strand an ACTIVE journey;
- numeric values were not meaningfully enforced;
- capability mutation audit was incomplete;
- journey-scoped preference semantics were weak;
- capability/commitment conflict explanation was missing;
- agent tools were capability-blind;
- MCP tool-call contract mismatch existed in the measured baseline.

Do not assume these still exist.

Reproduce first.
