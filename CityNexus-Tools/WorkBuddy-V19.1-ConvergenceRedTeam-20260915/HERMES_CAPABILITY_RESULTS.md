# HERMES_CAPABILITY_RESULTS.md

**Scope:** is the Hermes agent surface read-only with respect to capability context — i.e. can
the agent see, create, or mutate a traveller's capabilities?
**Evidence:** `evidence/lifecycle_a.json` → `hermes`, `evidence/lifecycle_b.json` → `hermes`
**Probe:** `tools/v191_probe_lifecycle.py` (`hermes` step)

---

## 1. Result: no capability tool exists, and the tool set is stable

| Measure | Snapshot A | Snapshot B |
|---|---|---|
| `GET /api/v1/agent/tools` count | **6** | **6** |
| `GET /api/v1/agent/tools/v2` count | **11** | **11** |
| Tool lists identical A vs B | **yes** | — |
| Any tool exposing or mutating capability context (`any_capability_tool`) | **`false`** | **`false`** |
| `GET /api/v1/agent/hermes/capabilities` | **200** | **200** |

`GET /api/v1/agent/hermes/capabilities` returns:

```json
{"configured": false, "reachable": false, "runs": false, "ready": false}
```

So the Hermes capability endpoint is a **status probe**, not a capability reader — it reports
whether the Hermes runtime is configured, and it is not. It exposes no traveller data.

**Conclusion: the Hermes agent surface is read-only with respect to capability context, and it
is not even aware of it.** No tool in either tool set (v1 = 6, v2 = 11) names, reads, or
mutates a capability. Tag: holds.

---

## 2. A probe artefact that must not be reported as a finding

An earlier version of this probe recorded `agent_can_create_capability: true`. **That reading
was wrong and is retracted here.**

The probe inferred "the agent can create a capability" from a `422` response on a POST to a
capability route, treating anything other than `404`/`405` as "the route exists and accepts
agent writes". A `422` means *unprocessable entity* — the route exists but the payload was
rejected — which says nothing about agent authority. The correct reading is that the route is
a **user-facing** endpoint with no agent identity requirement to test, and the tool-set
inspection (§1) is the authoritative evidence that no agent tool touches capabilities.

**Reported as a probe artefact, not as a defect.** Any future run of this probe should assert
against the tool sets (`any_capability_tool`) rather than against HTTP status codes.

---

## 3. Context: what the agent surface *does* expose

The 6 v1 and 11 v2 tools are the journey-operations set (agent runs, approvals, commands).
The capability vocabulary is entirely absent from them. This is consistent with the product's
stated authority model — capabilities are user-stated facts confirmed through
`/capabilities/confirm`, not agent-inferred state.

The one adjacent surface is `POST /journeys/{id}/agent/commands` (used by the mid-trip
probes), which operates on the journey, not on the capability set.

## 4. Verdict table

| # | Finding | Result | Tag |
|---|---|---|---|
| 1 | No agent tool reads capability context | **holds** — `any_capability_tool: false` | — |
| 2 | No agent tool mutates capability context | **holds** | — |
| 3 | Tool sets are stable across the round | **holds** — 6 / 11 identical at A and B | — |
| 4 | `GET /agent/hermes/capabilities` leaks traveller data | **holds** — status-only, `configured: false` | — |
| 5 | Earlier `agent_can_create_capability: true` reading | **RETRACTED — probe artefact** | — |

## 5. Recommendation

Keep the assertion in the focused suite (`any_capability_tool is False` for both tool
versions). Do not add a capability tool to the agent surface without an explicit authority
model and an audit path, since the current design has the user — not the agent — as the only
source of a HARD accessibility need.
