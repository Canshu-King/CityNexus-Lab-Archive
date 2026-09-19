# CityNexus P1 quota-saver rescue summary

Date: 2026-09-08
Purpose: minimize further Codex reasoning/quota use by handing back already-validated route witnesses, blockers, and targeted helpers.

## Ground truth

- C1/C2/C3/C4 remain FROZEN_PASS.
- The authoritative `phase1-routing-rc6-candidate.yaml` was not promoted or modified by this rescue work.
- The three C4E1 Extend routes remain immutable.
- Formal RC6 and formal Visio rendering remain BLOCKED until V2 and V3 pass on a complete 18-Association candidate.

## Concrete progress completed outside Codex

A sequence of exact, contact-free partial witnesses was constructed and independently validated.

Best verified result:

- 15 / 18 Associations simultaneously routed.
- + 3 frozen Extend routes checked at the same time.
- exact geometry validation PASS.
- zero cross-route contacts inside that partial witness.
- zero route-level failures.

Four independent 15-Association witnesses are included because they preserve different genus-zero source rotations/corridors:

1. `P1_PARTIAL15_WITNESS.yaml` — upper-separated plan.
2. `P1_PARTIAL15B_WITNESS.yaml` — Mobility source rotation.
3. `P1_PARTIAL15C_WITNESS.yaml` — dual City-Data/Mobility source rotation.
4. `P1_PARTIAL15H_WITNESS.yaml` — dual rotation with CE09 lower detour.

The remaining unresolved Associations in all selected 15-route witnesses are:

- `A-CD-UC-10`
- `A-M-UC-08`
- `A-M-UC-10`

Do NOT interpret 15/18 as a freeze. It is a strong exact candidate-family seed only.

## Important diagnosis

Trying to add the three missing routes one-by-one against a fully fixed 15-route witness fails. This proves that at least a small subset of the 15 routed Associations must remain mutable during the final solve.

A direct attempt to extend the upper-separated 15-route witness with `A-M-UC-10` after rerouting the upper `A-CD-UC-04` / `A-M-UC-04` pair reached 16 routes structurally, but exact validation found contacts with:

- `A-B-06`
- `A-PA-07`

So the next useful search is NOT "route only the last three around a frozen 15".

The current high-value joint mutable cluster is:

- `A-B-06`
- `A-PA-07`
- `A-CD-UC-10`
- `A-M-UC-08`
- `A-M-UC-10`

Potentially include `A-CE-09` if the lower corridor is still blocked.

## Verified code state

The reconstructed rescue workspace test suite was run locally:

`24 passed`

The included topology/runtime/self-contact contract tests are therefore already exercised. Codex does not need to spend quota rediscovering these invariants.

## What Codex should NOT redo

- Do not revisit native Visio connector geometry experiments.
- Do not reopen C1-C4.
- Do not rerun genus-1/genus-2 plans.
- Do not regenerate the already validated 15-route witnesses from scratch.
- Do not freeze the 15-route witness as hard obstacles.
- Do not spend a long model turn explaining the history.
- Do not render RC6.

## Remaining real task

Find a complete genus-zero 18-Association exact witness by using one of the supplied 15-route witnesses as a soft seed, ripping up only the smallest blocker cluster needed for the three missing provider routes.

After an 18/18 staging candidate exists, run the existing full gate chain. First V2 PASS + V3 PASS + full pytest zero failures => STOP and package for external freeze.
