# Autonomous Backlog Decisions

Selection rule: `user value × frequency × confidence ÷ merge risk`.

## 1. Evidence inspected

- Current V19 capability API and frontend consumers.
- Provider evidence architecture and OSM tag shapes.
- Existing plan/recovery explainability gaps.
- Existing PWA/build/test architecture.
- Existing audit and contract vocabulary.

## 2. Candidates considered

| Candidate | User value | Frequency | Confidence | Merge risk | Decision |
| --- | --- | --- | --- | --- | --- |
| Bounded text → capability extraction endpoint | High | High | High | Low | Implemented |
| Capability audit trail endpoint | High | Medium | High | Low | Implemented |
| Capability catalog endpoint | Medium | High | High | Low | Implemented |
| New agent framework | Low | Low | Low | Very high | Rejected |
| Speculative database rewrite | Low | Low | Low | Very high | Rejected |
| Endless colour polish | Low | High | Low | Low | Rejected |
| Full recovery replay engine | High | Medium | Low | High | Deferred |

## 3. Implemented autonomous improvements

### 3.1 `POST /api/v1/travelers/{id}/capabilities/extract`

Problem: setup/Copilot confirmation UX needed a bounded, deterministic way to
turn text into capability candidates without persistence or provider claims.

Implementation: returns `authority=UI_CANDIDATE_ONLY`, `confirmed=false`,
`source=DETERMINISTIC_TEXT_FALLBACK`.  Hard accessibility candidates are
visible but never silently persisted.

Tests: extraction, scope, candidate-only authority, HARD severity.

### 3.2 `GET /api/v1/travelers/{id}/capabilities/audit`

Problem: capability confirmations are durable authority decisions, but the UI
and operators had no inspectable change history.

Implementation: returns recent `TravelerCapability` audit events with action,
before/after, journey, and timestamp.  No secrets are returned.

Tests: confirm a capability then assert audit actions exist.

### 3.3 `GET /api/v1/capabilities/catalog`

Problem: UI and Copilot code could drift from the canonical vocabulary and
severity defaults.

Implementation: returns codes, classes, severities, scopes, accessibility
states, and default severity/class metadata.  Descriptive only; does not imply
provider evidence.

Tests: catalog contains hard codes and evidence states, and the
unknown-is-not-accessible flag.

## 4. Merge recommendation

All three are additive endpoints with unit tests and zero main-tree changes.
They are safe to merge as `patches/05_AUTONOMOUS_IMPROVEMENTS.patch`.

The deferred full recovery replay engine should wait for a real
`recovery/capability-diff` backend contract rather than being simulated in the
UI.
