# Validation Matrix

## A. Isolated Native Hermes E2E
Build a throwaway test stack and prove:

Copilot
-> DeepSeek SemanticEnvelope
-> HERMES_NATIVE_MCP
-> Hermes Runs/SSE
-> real CityNexus MCP tool
-> Gateway / Guardian
-> proposal/result

Use:
- isolated backend port, e.g. 8022
- isolated SQLite DB
- dedicated Hermes profile, e.g. `citynexus-harness-lab`
- no authoritative DB writes

## B. Hermes Chaos
Test:
- gateway unavailable
- gateway killed during run
- restart/reconnect
- SSE interruption
- duplicate event
- out-of-order event
- malformed event
- stale run
- stop during tool execution
- stop after proposal
- MCP unavailable
- DeepSeek unavailable
- backend unavailable

## C. Concurrency / Idempotency / Approval
Test:
- concurrent runs same journey
- concurrent runs different journeys
- duplicate request IDs
- conflicting request IDs
- approval replay
- approval cross-journey misuse
- approval cross-action misuse
- expiry
- double-click
- stop-vs-complete
- approve-vs-stop
- superseded proposal

## D. Semantic Corpus
At least 240 meaningful cases:
Chinese / English / mixed,
multiple cities/currencies,
elderly / wheelchair / infant / family / business / student / group travel.

## E. API Contract
Re-check:
- native Hermes unconfigured proxy behavior
- capabilities schema consistency
- runtime truth
- unknown run
- stop unknown run
- SSE unconfigured behavior
- empty-place-catalogue plan generation
- error envelopes
- retryability/status codes

## F. Web/Mobile Truth
Desktop: 1440x900, 1280x720
Mobile: 390x844, 430x932

Check:
- DIRECT vs Hermes truth
- run timeline
- stopped/failed/offline
- approval
- keyboard
- focus
- reduced motion
- long bilingual text
- no horizontal overflow

## G. Lightweight Stability
- 10 sequential agent runs
- 3 concurrent read-only runs
- 2 concurrent proposal-only runs
- 100 / 300 / 1000 event rendering
- p50 / p95 observations
- duplicate rate
- reconnect storm check
