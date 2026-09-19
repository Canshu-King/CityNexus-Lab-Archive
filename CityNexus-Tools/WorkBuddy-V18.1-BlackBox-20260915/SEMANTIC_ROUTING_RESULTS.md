# Semantic Routing Results (V18.1)

Two layers were checked: **E — DeepSeek/Hermes routing** and **F — semantic truth**.
Sources: `evidence/results_isolated.json` (E, live HTTP) and `evidence/results_semantic.json`
(F, deterministic offline).

## E — Routing (live HTTP, isolated backend)

| ID | Message | Expected | Actual | Result |
|---|---|---|---|---|
| E1 | 为什么这样安排？ | EXPLAIN_PLAN, no run | `intent=EXPLAIN_PLAN`, `agent_run=null` | **PASS** |
| E2 | 如果博物馆多待一小时会怎样？ | WHAT_IF, no run | `intent=WHAT_IF`, `agent_run=null` | **PASS** |
| E3 | Why is the plan arranged this way? | EXPLAIN_PLAN, no run | `intent=EXPLAIN_PLAN`, `agent_run=null` | **PASS** |
| E4 | What if we stayed one more hour… | WHAT_IF, no run | `intent=WHAT_IF`, `agent_run=null` | **PASS** |
| E5 | multi-step PLAN_ONLY (inspect → search → compare → propose) | native unavailable → explicit fallback, **never** fake `HERMES_NATIVE_MCP` | `agent_run=null`, no Hermes identity claimed | **PASS** |

The Hermes-suitable multi-step request returned `mode=FALLBACK`, `provider=deterministic`,
and **no** `runtime_identity` claim — i.e. the product did not pretend Hermes participated when
the gateway was not configured. This is the desired A2 behaviour.

## F — Semantic truth

### F-live (HTTP against the isolated backend)
**NOT_TESTED (5)** — the isolated instance ran with `CITYNEXUS_AI_ENABLED=false`, so no
DeepSeek envelope was produced and the deterministic fallback path was used. This is an
environment choice (no model credential was consumed), not a product failure. To run live,
start an instance with `CITYNEXUS_AI_ENABLED=true` + a model credential.

### F-offline (deterministic policy table) — 14/14 PASS
`apply_semantic_policy(envelope)` and `SemanticEnvelope.from_mapping()` were exercised directly.

| ID | Envelope | Expected route | Expected event | Result |
|---|---|---|---|---|
| F1 | ASSERTED + NOW + CLOSURE | DISRUPTION_REPORT | create | PASS |
| F2 | ASSERTED + FUTURE + WEATHER | DISRUPTION_REPORT | create | PASS |
| F3 | HYPOTHETICAL | WHAT_IF | no | PASS |
| F4 | UNVERIFIED | VERIFY_FACT | no | PASS |
| F5 | NEGATED | UNKNOWN | no | PASS |
| F6 | HISTORICAL | UNKNOWN | no | PASS |
| F7 | PERSONAL_ASSISTANCE / PERSONAL | PERSONAL_ASSISTANCE | no | PASS |
| F8 | ASSERTED + PAST | DISRUPTION_REPORT | **no** | PASS |
| F9 | EXPLAIN_PLAN | EXPLAIN_PLAN | no | PASS |
| F10 | missing required key | rejected (None) | — | PASS |
| F11 | out-of-enum assertion_status | rejected (None) | — | PASS |
| F12 | confidence = 1.7 | rejected (None) | — | PASS |
| F13 | HYPOTHETICAL where fallback leans DISRUPTION | WHAT_IF wins | no | PASS |
| F14 | NEGATED claim | UNKNOWN | no | PASS |

**Anti-override check (F13/F14):** the semantic policy is *not* re-overridden by the low-level
substring classifier. `如果明天下雨会怎样？` → WHAT_IF (`create_event=False`) even though the
deterministic fallback classifier is tempted toward a disruption; `博物馆没有关门。` → UNKNOWN
with no Event.

## Notes / risks

- The gating key `create_event` is honoured by the copilot handler:
  `semantic_allows_event = envelope is None or bool(envelope.get("create_event"))`
  (`main.py:7922`). So a hypothetical/negated/unverified envelope cannot create a city Event.
- **Residual risk:** when the DeepSeek call fails or returns an unparsable envelope,
  `_copilot_fallback_or_ai` silently falls back to `classify_copilot_message` — a substring
  classifier. In that degraded mode the F13/F14 protections do **not** apply. Recommend the
  product surface a distinct `mode` (it already returns `FALLBACK`) and that downstream UI not
  treat fallback intent as semantically verified. This is a design observation, not a defect.
