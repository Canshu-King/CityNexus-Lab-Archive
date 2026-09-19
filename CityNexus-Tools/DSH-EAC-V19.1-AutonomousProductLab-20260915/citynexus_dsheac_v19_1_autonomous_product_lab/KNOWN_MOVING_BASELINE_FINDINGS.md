# Known Moving-Baseline Findings

The WorkBuddy V19 red-team measured an older V18.3 snapshot first, then observed
Codex changing the main tree during the run.

At the later snapshot, Codex had introduced a real capability domain including:

- `backend/app/capabilities.py`
- capability codes/severity/scope/evidence states
- `traveler_capabilities` persistence
- SemanticEnvelope capability wiring
- capability projection into feasibility

That direction is correct, but the red-team's later snapshot found several
important defects. These may already be fixed by the time this task starts, so
RE-CHECK them; do not assume they remain true.

Known delta candidates:

1. `capability_payload` missing while imported by `app.main`, causing import failure.
2. HARD downgrade guard may be tautological.
3. negation/history fallback may operate on the entire text instead of the relevant clause.
4. duplicate capability codes may survive with conflicting severity.
5. numeric walking/rest/nap constraints may be under-parsed.
6. capability rule codes may be emitted into a feasibility gate that does not interpret them.
7. TRAVELER scope may be unreachable from natural language.
8. accessibility evidence state machine itself looked good:
   UNKNOWN was not treated as verified.

Do NOT spend the whole task repeating these findings.

Use them as an initial contract check, then move forward.
