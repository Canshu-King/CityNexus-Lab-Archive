# CityNexus Autonomous City Intelligence V3

Status: **IMPLEMENTED / local gates green / DeepSeek model-backed path verified**

This iteration added the Delegated Autonomous Journey Agent path in the
current CityNexus repository:

```text
raw Event truth + DeepSeek semantic hypothesis
  -> ImpactAssessment provenance and maturity
  -> deterministic post-action feasibility/business-fact gate
  -> user-owned Autonomy Envelope
  -> Agent Mission / DeepSeek tool loop / MCP V2-compatible Gateway
  -> scoped approval receipt when required
  -> persisted domain mutation and audit projection
```

Key authority results:

- AI semantic targeting is operation-scoped and never overwrites
  `Event.affected_activity_id`.
- `AI_ONLY` cannot self-escalate on retry and is never persisted as a
  `validated_activity_id`.
- Caller-owned `user_confirmed` is compatibility-only. User approval is a
  server-issued, Journey-scoped, expiring, one-use receipt bound to the exact
  action, target, policy version, facts, and arguments.
- Advisory Commitment mutation cannot auto-execute. Explicit higher-policy
  and provider/loss conditions still determine whether step-up can complete a
  protected action.
- MCP V1 remains pinned at six tools. V2 exposes all eleven inspect/plan/action
  tools in one server, including typed
  `replace_activity`, `reschedule_activity`, `create_booking`,
  `cancel_refundable_booking`, and `request_commitment_change` commands; high
  risk calls remain visible and return Gateway policy decisions.
- Impact Intelligence retains a primary recovery target and secondary risk IDs,
  with fuzzy aliases, time windows, polygon scope, and route intersection
  evidence.
- JourneyMission and AgentRun/AgentRunStep are persisted; natural-language
  commands compile to bounded one-run authority and are reloadable.
- Place-backed replacement materializes a server-owned candidate without
  cannibalizing another scheduled Activity.
- Solver V2 is available behind explicit `CITYNEXUS_SOLVER=v2`: it searches
  multiple remaining mutable slots against protected anchors, opening windows,
  budget, risk, preferences, and a frozen mobility matrix, then sends normal
  proposals through the existing deterministic gate. Solver V1 remains the
  default and fallback path.

Current verification:

- V3 focused Agent/impact/solver regressions plus Solver V2: **green**; exact
  final counts are recorded in `TEST_RESULTS.md`.
- MCP V1/V2 boundary and stdio tests: **6 passed**.
- OpenAPI formal/runtime parity: **52/52**, missing 0, extra 0.
- Frontend build: **PASS**; serial Playwright Control Tower: **4/4 passed**.
- Real DeepSeek model-backed smoke: **PASS** with model-selected tool order,
  autonomous bounded acceptance, protected Commitment preservation, and
  persisted trace reload. No credential is stored in source or reports.

Hermes CLI itself remains an external environment boundary; the V2 MCP stdio
surface and backend DeepSeek adapter are verified separately. Live Valhalla,
production identity/WebAuthn, and optional Phoenix/Promptfoo polish remain
follow-on evidence items.
