# FINDINGS.md

Three findings. One fixed, one false positive corrected, one open and blocking.

---

## FINDING 1 — FIXED: a closed venue was replaced by itself under another id

**Severity: high. Silent. User-visible.**

A closed restaurant could be "recovered" by substituting *that same restaurant*,
stored under a different Place row. The traveller was sent to a closed venue and
the UI reported a successful, minimal-change recovery.

Evidence from journey `aa17d2b7-a199-4466-ad11-8ed9092782fe`:

| | base plan (closed) | accepted replan |
|---|---|---|
| activity | `7f284b17` | `c5ca0c06` |
| place_id | `e1ced246-e238-5e48-a816-1b82e8b2953c` | `real-place-07e7689756fa27109a8bff96` |
| provider | `citynexus-v9-domain` | `overpass` |
| external_id | `CN-XIAMEN:real-place-07e7689756fa27109a8bff96` | `overpass:node/1588295483` |
| coordinates | 24.4581979, 118.0689473 | 24.4581979, 118.0689473 |
| name | OSM restaurant | OSM restaurant |

Same physical venue, two ids. `metadata.replaced_place_id` even pointed at the
wrapper it had just replaced.

Root cause: `rank_closure_replacements` excluded candidates by id equality only.

Fix: `is_same_physical_venue` (same id, OR identical coordinates, OR a shared
identity token recovered from `id`/`external_id`) is used to keep the closed
venue — and every already-used venue — out of the candidate family.
See `R1_D_PHYSICAL_IDENTITY_PATCH.txt`.

Consequence in that journey: the *only* proposal that looked feasible was the one
that changed nothing real (utility 0.67); the two proposals that substituted
genuinely different venues scored higher (0.70) but were invalidated when the
first was accepted.

---

## FINDING 2 — FALSE POSITIVE CORRECTED: the harness assertion could never fail

`run_final_v2.cjs` asserted:

```js
postActs.some((a) => (a.place_id ?? null) === targetPlace)
```

`/journeys/{id}/experience` returns activities with keys
`id, sequence_no, type, title, start_at, end_at, locked, protected, metadata` —
there is **no top-level `place_id`**. So `targetPlace` was always `null` and the
assertion became "does any activity have a null place_id", which is trivially
true. It printed `closedPlaceReappeared=true` on every run — including correct
ones — and simultaneously masked Finding 1.

This is the same family as the R1-a `None in {None}` bug: a null identity
compared against a null-containing set.

Fix: compare `metadata.semantic_key`. The companion
`closed_semantic_reappeared` assertion was already correct.

---

## FINDING 3 — OPEN, BLOCKING: every new replan leg costs a fabricated 20 minutes

**Do not ship the Xiaomi trial with this open.**

`data/mock/mobility_matrix.json` holds **9 real routes** and a single
`default_minutes: 20`. Any pair not in those 9 gets the constant 20.

A replan creates adjacencies that are absent from the frozen baseline, so
`_replan_estimate` captures a runtime snapshot; with no live routing provider
configured, that is the mock, and **every new leg becomes exactly 20 minutes**.

Measured: 115 `_replan_estimate` calls during one real replan, all returning 20,
against real baseline legs of 4–11 minutes.

The re-timing pass then shifts unlocked rows by 20 minutes into the pinned
check-in at 06:00, which cannot move. The deterministic gate — correctly —
refuses:

```
422 ACTIVITY_OVERLAP,
    INSUFFICIENT_TRAVEL_GAP:real-place-1564f860645d87ceaae7949a|stay:osm:node/583066505:check-in
```

7 of 8 mutable stops fail this way. The traveller is told no replacement exists
while genuine, closer alternatives were found (香村瓦缸煨汤馆 is 816 m from the
closed venue and 575 m from the next locked stop).

The gate is right; the travel time is the lie. Full analysis, evidence and three
remediation options: **`MOCK_MOBILITY_LIMITATION.md`**.

---

## Also noted by the independent cycles (not fixed here)

- Two surfaces disagreed on the same instant (`02:00` vs `10:00`) — zone slicing.
- Un-chosen data presented as the traveller's trip; "no price" printed as ¥0.00.
- A handled disruption stayed escalated as `1 项变化` after acceptance.
- "Budget verified" claimed on a plan with 14/14 unknown prices.
- Remaining English/provider leaks (`WGS84`, `TRANSIT`, `Check in`, `V12`).
- The over-budget branch is unverifiable with the available cities (no priced stops).

Details and reproduction: `AUTONOMOUS_CYCLE_1..5.md`.
