# NO EARLY EXIT PROTOCOL

This mission exists because the previous 8–9 hour task was packaged after a
very short run.

The continuation must behave differently.

## Wall-clock ledger

At start, record the real system clock using the host OS.

On Windows PowerShell:

`Get-Date -Format o`

Append to:

`OVERNIGHT_RUN_LEDGER.jsonl`

For every major checkpoint include:
- timestamp;
- phase;
- current top blocker;
- files changed since previous checkpoint;
- browser scenarios completed;
- remaining P0/P1 count.

Minimum checkpoints:
- START
- C1
- C2
- C3
- C4
- C5
- FINAL

## Early-exit rule

Do NOT produce the final package merely because:
- build is green;
- backend tests pass;
- one browser flow works;
- a subset of backlog is complete.

Final packaging is allowed only when BOTH are true:

A. all mandatory acceptance items in `FINAL_ACCEPTANCE.md` are completed or
   explicitly externally blocked;

AND

B. at least FIVE autonomous product-lab cycles have been completed after the
   initial canonical flow attempt.

If an external service blocks one path:
- record it;
- continue all other product work;
- do not stop the entire run.

## No fake waiting

Do not idle just to satisfy time.

Use remaining time for:
- user-flow testing;
- UI refinement;
- accessibility;
- copy cleanup;
- failure recovery;
- patching discovered P0/P1 issues;
- additional personas.

## Package integrity

The final package must include:
- `OVERNIGHT_RUN_LEDGER.jsonl`;
- the five autonomous-cycle reports;
- final visible trace;
- screenshots;
- changed files;
- tests;
- honest unresolved blockers.

If those are missing, the mission is incomplete.
