# Cross-Journey Scope Results

**Question:** does a need expressed for *this trip* stay in this trip?
**Evidence:** `evidence/cross_journey_scope_probe.json`, `evidence/semantic_live_results.jsonl`

---

## 1. The two scope surfaces, and their asymmetry

CityNexus has exactly two places a traveller's expressed wish can land, and they are scoped differently.

### Journey-scoped — `constraints`

```sql
CREATE TABLE IF NOT EXISTS constraints (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('HARD','SOFT')),
    category TEXT NOT NULL,
    rule_code TEXT NOT NULL,
    params_json TEXT NOT NULL DEFAULT '{}',
    weight REAL NOT NULL DEFAULT 1.0 CHECK (weight >= 0.0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    ...
);
```

Correctly journey-scoped. `journey_id NOT NULL REFERENCES journeys(id) ON DELETE CASCADE`.

### Traveller-scoped — `preferences`

```sql
CREATE TABLE IF NOT EXISTS preferences (
    id TEXT PRIMARY KEY,
    traveler_id TEXT NOT NULL REFERENCES travelers(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    preference_key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 0.5 CHECK (weight >= 0.0 AND weight <= 1.0),
    source TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(traveler_id, category, preference_key)
);
```

**There is no `journey_id`.** And the `UNIQUE(traveler_id, category, preference_key)` constraint makes the consequence sharper than "unscoped":

> A traveller saying *"for this trip, avoid stairs"* does not merely create a global preference — it **overwrites** whatever value they previously held for that `(category, key)`, for every journey, past and future. There is no history, no per-journey copy, and no UI to see or undo it.

Confirmed at runtime — `PREFERENCE_SCOPE_FIELDS` returned exactly:

```json
{"preference_count": 1,
 "keys": ["category", "id", "key", "traveler_id", "value", "weight"]}
```

No `journey_id`. No `created_for_journey`.

---

## 2. Measured behaviour

### 2.1 The mission surface is correctly scoped (guard holds) ✔

`evidence/cross_journey_scope_probe.json`

| Case | Result |
|---|---|
| `CREATE_TWO_JOURNEYS` | A `201`, B `201` |
| `BASELINE_PLANS` | A and B produce identical 3-plan sets (same seed catalog) |
| `MISSION_SCOPED_SET_ON_A` | `200` — mission stored on A with `objective_codes: ["MINIMIZE_WALKING", "PREFER_INDOOR"]` |
| `THIS_JOURNEY_ONLY_LEAK_CHECK` | `journey_a_changed: false`, `journey_b_changed: false` |

`PUT /journeys/{id}/guardian/mission` is the **only** journey-scoped preference surface, and it does **not** leak. The mission correctly captured `MINIMIZE_WALKING` and `PREFER_INDOOR` on journey A, and journey B was unaffected. The regression suite locks this as `test_v19_guard_f12a`.

The problem is not that the mission leaks. The problem is what happens when the traveller *doesn't* use the mission surface.

### 2.2 Traveller-scope: the "this journey only" trap

| Step | Result |
|---|---|
| `PUT /travelers/{id}/preferences` with `[{category: interest, key: indoor, value: true, weight: 1.0}]` | `200` |
| Stored row | `{category: interest, key: indoor, value: true, weight: 1.0, id: cba32689-…, traveler_id: 11111111-…}` |
| Scope field present? | **no** |
| `TRAVELER_SCOPE_LEAK` — journeys A and B after the write | identical plans (the preference applies to both, by design of the table) |

The probe's own recorded verdict:

> `"the preferences table has no journey_id: a 'this journey only' intent stored here silently becomes a permanent traveller-scope preference"`

### 2.3 Why this is worse for a capability than for a taste

Compare the two intents that can land in `preferences`:

| Traveller says | Stored as | Consequence of being permanent |
|---|---|---|
| *"This trip I'd like indoor activities"* | `interest.indoor = true` | minor — the traveller may notice a preference drift |
| *"Just for this trip, avoid stairs"* | `interest.<something> = true` | **the traveller's profile now permanently claims a mobility need they may not have — or permanently *fails* to record one they do** |

And the `UNIQUE(traveler_id, category, preference_key)` clause means the second write destroys the first. A traveller who says *"this trip I need step-free"* and later says *"this trip I don't"* has no way to hold both, and no way to see which one won.

Worse, because `preferences` is traveller-scoped and `constraints` is journey-scoped, the **same sentence** routed to two different surfaces has two different lifetimes. Which surface it lands on depends on the semantic policy — and finding F8 shows the policy does not read the constraint payload at all, so routing is not governed by whether the traveller meant "this trip".

### 2.4 A HARD capability is properly journey-scoped

| Case | Result |
|---|---|
| `HARD_CAPABILITY_BLOCKS` on one journey | `422` on that journey |
| Other journey | unaffected — `constraints.journey_id` does its job |

So a traveller *can* hold a per-journey capability. It just cannot be expressed in language, and it cannot be softened or removed once set (findings F5, F6, F9).

---

## 3. TravelerTwin scope and the escalation question

The task book asks specifically whether learned evidence can manufacture a HARD capability. Measured:

| Case | Result |
|---|---|
| `LEARNED_EVIDENCE` | one item: `dimension: low_walking`, `direction: low_walking`, `confidence: 0.95`, `strength: 1.0`, `evidence_count: 6`, `journey_ids: [demo journey]`, `expires_at: 2027-03-14`, `source: "LEARNED_SOFT"` |
| `source_labels` | `["LEARNED_SOFT"]` only |
| `LEARNED_FED_TO_PLANNER` | `learned_item_count: 1`, `weights: [1.0]`, `categories: ["interest"]` |
| `LEARNED_TO_CONSTRAINT_ESCALATION` | `learned_created_any_constraint: **false**` |
| Constraint rule codes present after the twin learned | `BUDGET_MAX`, `JOURNEY_END_BY`, `MINIMISE_PLAN_CHANGES`, `STEP_FREE_REQUIRED` — the last one injected by the probe itself |
| `LEARNED_CLEARED` | `200` |
| `TWIN_AFTER_CLEAR` | `learned_soft: []`, `evidence_count: 0` |

**Verdict: the escalation does not happen, and the design is right.**

- Learned evidence lives in `learned_soft_preferences_json`, labelled `LEARNED_SOFT`.
- It reaches the planner as `category="interest"` at weight `1.0` — an *interest*, never a `JourneyConstraint`.
- It carries `journey_ids` and an `expires_at`, so it is both scoped and time-bounded.
- `clear_learned` empties it completely.

Note the nuance worth keeping in mind for the fix: the learned item's `dimension` is `low_walking` — a **mobility** signal. It is handled safely *because* it is confined to the interest channel. If a future capability model starts reading `low_walking` from the twin, this guard becomes the thing standing between "the app noticed you took the lift six times" and "the app decided you need step-free routing". **Preserve `LEARNED_SOFT` as an interest-only channel.** The regression suite locks this as `test_v19_guard_f13`.

---

## 4. Audit scope

| Case | Result |
|---|---|
| `AUDIT_TRAIL.actions` | `["constraint.created"]` |
| `AUDIT_TRAIL.constraint_actions` | `["constraint.created"]` |
| `AUDIT_TRAIL.capability_actions` | **`[]`** |

The only constraint-adjacent audit action in the product is `constraint.created`. There is no:

- `constraint.deleted` — yet `DELETE` returns `204` and restores planning (finding F6)
- `constraint.deactivated` — yet `active=0` silences a HARD capability (finding F6)
- `capability.declared` / `capability.weakened` / `capability.evidence_changed` (finding F16)

Combined with the two scope facts above, the audit gap has a specific shape:

> An accessibility requirement can be **created** (journey-scoped, audited), **silenced** (journey-scoped, unaudited), **deleted** (journey-scoped, unaudited), or **leaked into a traveller's permanent profile** (traveller-scoped, unaudited).

Only the first leaves a trace.

---

## 5. Findings index for this document

| ID | Finding | Severity |
|---|---|---|
| F12a | Mission surface is correctly journey-scoped and does not leak (guard holds) | — ✔ |
| F12b | `preferences` has **no `journey_id`**; `UNIQUE(traveler_id, category, preference_key)` makes a "this trip only" intent permanent **and destructive** | **P0** |
| F12c | The same sentence can land on a journey-scoped or a traveller-scoped surface, with different lifetimes, governed by a policy that never reads the constraint payload | **P0** |
| F13 | Learned evidence stays `LEARNED_SOFT`, creates no constraint, is scoped by `journey_ids` and `expires_at`, and clears cleanly (guard holds) | — ✔ |
| F16 | Audit vocabulary has no capability action; `DELETE` and `active=0` leave no trace | P1 |
| — | A HARD capability *is* correctly journey-scoped via `constraints.journey_id` — the scope model exists, it is just unreachable by language | — |

---

## 6. Acceptance criteria

1. A traveller can express a journey-scoped preference **in language** and have it stored with a `journey_id` — or the product refuses the statement and says so.
2. `preferences` gains a journey scope (nullable `journey_id`, or a `journey_preferences` table) so that `UNIQUE(traveler_id, category, preference_key)` cannot destroy a traveller's prior value.
3. Routing between the journey-scoped and traveller-scoped surfaces is decided by an explicit scope signal from the semantic envelope, not by which route the policy happens to pick.
4. Every capability mutation writes an audit entry naming the capability and the action (`created` / `updated` / `deactivated` / `deleted`).
5. `LEARNED_SOFT` remains an interest-only channel and is never read as a capability source — lock this with a test before adding any capability model.
6. A traveller can see, and undo, every preference the product has stored against them, with its scope.
