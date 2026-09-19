# Self-Directed Backlog

After mandatory workstreams pass, Harness EAC must independently choose at least
THREE additional product improvements.

Process:

1. inspect current product once;
2. collect evidence;
3. rank candidate improvements by:
   user harm/value × frequency × confidence ÷ merge risk;
4. pick top 3–5;
5. implement in isolated tree;
6. test;
7. produce separate low-conflict patches;
8. explain why each should or should not be merged.

Suggested exploration areas:

## UX
- onboarding/setup friction
- city/provider unavailable flow
- Journey first-view clarity
- recovery/approval clarity
- empty-state usefulness
- bilingual consistency
- mobile navigation
- Copilot history

## Map
- accessibility evidence markers
- route-change focus
- layer clutter
- map loading/lazy loading
- offline/stale map state

## Performance
- bundle size
- MapLibre initialization
- rerender storms
- 1000-event timelines
- query cache behavior

## Reliability
- refresh/reconnect
- stale state
- browser back/forward
- route restore
- offline recovery

## Accessibility
- keyboard
- focus
- screen reader
- 200% zoom
- 320px
- reduced motion
- touch targets

## Engineering
- API/type drift
- test fragility
- release hygiene
- debugability
- error envelopes

Do not choose “add another framework” as an autonomous task.
