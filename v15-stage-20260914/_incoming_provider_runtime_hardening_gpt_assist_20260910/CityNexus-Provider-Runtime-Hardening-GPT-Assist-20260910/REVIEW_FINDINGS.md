# External Review Findings

## Verdict

The GPT Web Codex Provider Runtime implementation is a **substantial engineering
advance** over the previous Vertical Slice milestone, but the uploaded checkpoint
is **not yet FROZEN_PASS**.

The supplied PRT-01..PRT-08 tests are real and all pass. The full backend also
reproduced independently at:

```text
165 passed, 1 skipped
```

However, five new adversarial tests expose five semantic defects that the current
PRT suite misses:

```text
5 failed
```

After applying the reference hardening in an isolated copy:

```text
PRT-01..PRT-08 + GPT hardening = 13 passed
full backend = 170 passed, 1 skipped
compileall = PASS
OpenAPI formal/runtime = 38/38
```

## What GPT Web Codex did well

1. Introduced a clean runtime boundary around mobility capture.
2. Captures one operation-scoped snapshot before candidate evaluation.
3. Reuses the snapshot through F3 and generation-time feasibility.
4. Added pair-level fallback and per-fact provenance.
5. Persisted snapshot evidence in ReplanProposal evidence.
6. Kept JourneyTwin free of live provider calls.
7. Added an actual Valhalla MockTransport contract.
8. Kept the offline Golden Scenario alive.
9. Wrote a useful gap analysis and architecture note instead of pretending all
   provider work was complete.

## Five defects found externally

### PRH-01 - `MobilitySnapshot` is not actually immutable

The dataclass is frozen, but `facts` is a normal mutable `dict`. Code can mutate:

```python
snapshot.facts[("a", "b")] = ...
```

That violates the core claim that every candidate is judged against the same
frozen reality.

Reference fix: defensive copy + `MappingProxyType` in `__post_init__`.

### PRH-02 - JourneyTwin reports the primary provider, not the provider of the fact it used

With a partial fallback:

```text
Tech Art -> River Cruise
actual fact provider = mock-mobility
snapshot primary      = valhalla
```

The current Twin reports `provider = valhalla`, despite using the mock fallback
fact for the displayed C4 buffer.

Reference fix: report `fact.provider_key` as the effective provider and preserve
`source_provider` separately.

### PRH-03 - Provider degradation does not reach FeasibilityEnvelope / robustness score

A proposal can have:

```text
verified_evidence.mobility.degraded = true
```

while simultaneously reporting:

```text
after_feasibility_envelope.degraded_providers = []
robust = true
score_breakdown.robustness = 1.0
```

That is internally contradictory and can over-rank a degraded proposal.

Reference fix: propagate the primary degraded provider into both before/after
FeasibilityEnvelope and therefore into verified robustness scoring.

### PRH-04 - `travel_delta_min` compares two different mobility realities

Candidate activities are recomputed from the new frozen snapshot, but the base
plan total is taken from old persisted `travel_from_prev_min`, which may have
come from deterministic mock planning.

A test with a constant one-minute frozen provider produced:

```text
actual travel_delta_min = -85
expected same-snapshot delta = 0
```

The delta therefore measured a **provider switch**, not the replan itself.

Reference fix: recompute both base route total and candidate route total from the
same frozen snapshot before scoring/diff evidence.

### PRH-05 - Accept-time revalidation silently falls back to MockMobilityProvider

Generation-time feasibility injects the snapshot correctly. But `accept_replan()`
currently calls:

```python
validate_plan_feasibility(... include_active_c4=True)
```

without a mobility provider, which falls back to `MockMobilityProvider`.

So a proposal can be generated under Valhalla evidence and accepted/rejected
under a different mock reality.

Reference minimum fix: reconstruct the persisted proposal snapshot and inject it
into accept-time feasibility.

Longer-term option: an explicit fresh **acceptance snapshot** may be captured
outside the gate when a freshness policy requires it, but the accept path must
never silently use an unrelated default mock provider.

## Non-blocking review-package issues

The uploaded GPT Web Codex checkpoint contains generated/runtime artifacts:

```text
16 __pycache__ directories
135 .pyc files
2 SQLite .db files
```

The previous Luna Vertical Slice checkpoint contained none of those. This does
not invalidate the source or tests, but Luna's checkpoint packaging was cleaner.
Future review ZIPs should exclude pycache, pyc, runtime DBs, `.venv`, node_modules,
dist and pytest caches.

## Comparison with Luna

This is not an apples-to-apples benchmark because GPT Web Codex implemented the
next, harder Provider Runtime milestone while Luna completed the preceding
Vertical Slice hardening.

Still, the useful comparison is:

| Dimension | Luna previous checkpoint | GPT Web Codex provider checkpoint |
|---|---|---|
| Scope leap | Vertical Slice hardening | Real provider runtime wiring |
| Architectural initiative | Strong | Stronger |
| Tests-first/provider design | N/A / previous gate | Very good, 8 explicit PRT tests |
| External adversarial misses | No new blocking defect at freeze | 5 semantic defects found |
| Package hygiene | Cleaner | Worse: pyc/DB artifacts included |
| Documentation of architecture | Good | Better for this stage |
| Ready to freeze as uploaded | Yes | No, harden first |

Bottom line:

> GPT Web Codex showed **better autonomous architecture work**, but Luna's final
> checkpoint was **cleaner at the moment of freeze**. The Web result becomes the
> stronger engineering milestone after the five provider-semantic gaps are
> closed.
