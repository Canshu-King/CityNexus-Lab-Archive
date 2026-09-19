# V19.1 Acceptance Matrix

## Backend boot
- `import app.main` passes.
- migrations/schema initialize.
- capability list/read APIs return stable shapes.

## Canonicalization
- hard accessibility code cannot be downgraded by model/API label.
- duplicates collapse by code using strongest valid severity.
- negation is clause-local, not global.
- contradictory clauses resolve conservatively.
- unknown codes do not become authority.

## Semantic
- raw natural language -> model envelope -> canonical capability -> final policy.
- hard/soft pairs remain distinct.
- historical/negated statements do not create active hard needs.
- explicit permanent vs this-trip scope is distinguishable or honestly unresolved.

## Numeric/time
- walking units validated.
- negative/zero/huge/string/null cases handled explicitly.
- rest/nap windows validated in journey timezone.
- malformed values rejected early.

## Feasibility
- capability codes are interpreted or remain an explicit evidence/unsupported state.
- wheelchair hard requirement:
  VERIFIED can pass if all other constraints pass.
  UNKNOWN cannot silently pass.
  CONFLICT fails.
- recovery/What-If use the same capability logic.

## Lifecycle
- create/update/deactivate/delete audited.
- journey/traveler scope isolated.
- mid-trip capability update produces safe recovery/review semantics.

## Commitment conflict
- protected C4 is not silently removed.
- hard capability is not silently ignored.
- conflict response names both capability and commitment.

## Hermes
- read-only capability context available if current design exposes it.
- Hermes cannot mutate hard capability/evidence truth.

## UI
- hard/soft/evidence state truthful.
- unknown not shown as accessible.
- mobile/desktop survive long capability lists.
