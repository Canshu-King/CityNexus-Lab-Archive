# Minimal Codex continuation

You are quota-constrained. Do not repeat analysis already completed in this package.

## Read only these first

1. `RESCUE-SUMMARY.md`
2. `witnesses/P1_PARTIAL15C_WITNESS.yaml`
3. `evidence/P1_PARTIAL15C_VALIDATION.json`
4. `evidence/UPPER_BARRIER_DIAGNOSTIC.json`
5. `evidence/LOWER9_DIAGNOSTIC.json`

## Start state

Use `P1_PARTIAL15C_WITNESS.yaml` as the primary soft seed because its City Data and Mobility source rotations are both genus-zero and intentionally leave the three unresolved provider routes mutable.

Missing routes:
- A-CD-UC-10
- A-M-UC-08
- A-M-UC-10

Never freeze the 15 seed routes as immutable.

## Only worthwhile next search

Jointly route this mutable cluster first:

- A-B-06
- A-PA-07
- A-CD-UC-10
- A-M-UC-08
- A-M-UC-10

If required, add A-CE-09 to that mutable set.

Keep the other seed routes as temporary obstacles, but permit rip-up if a diagnostic proves one of them blocks all candidates.

Search order should be constraint-first / MRV, not fixed sequential A*.

For every new path candidate, enforce immediately:
- active port-plan topology genus = 0
- exact node clearance
- frozen Extend clearance
- self-contact = 0
- exact route-to-route contact = 0
- endpoint tangency
- min segment >= 0.10 cm

Do not rely on coarse raster occupancy as the final geometry truth.

## Reuse supplied evidence

`UPPER_PAIR_REACHABILITY.json` shows that alternate upper `A-CD-UC-04` / `A-M-UC-04` routing can open an exact route for `A-M-UC-10` before the lower B06/PA07 routes are reintroduced.

This strongly indicates the final blocker is corridor allocation among B06/PA07 and the three missing provider routes, not a lack of raw reachability.

## Stop condition

Only after a complete 18/18 staging candidate exists:

Topology PASS
-> V1 PASS
-> Contact Audit zero
-> self-contact zero
-> V2 PASS
-> V3 PASS
-> complete pytest zero failures

First all-green result: STOP. Do not render formal Visio or promote RC6 in the same turn. Package for GPT external freeze.
