# D. Semantic Traveler Corpus — DSH-EAC V18.3 Validation Lab

**Status: PASS** — 5764 / 5764 cases correct, 0 failures, including 4 injection probes.

## 1. Objective

Verify the semantic-policy compiler (`apply_semantic_policy`) deterministically
maps traveller utterances onto correct event-creation decisions, across many
cities, contexts, languages, and adversarial injections. This is fully offline —
no LLM call needed — so it is immune to the DeepSeek "too busy" stall that blocked
the live harness.

## 2. Method

Each case is fed through the **real** `apply_semantic_policy(envelope)` from
`source-snapshot/backend/app/integrations/ai/semantic_compiler.py` and compared
against an **independent oracle** (a re-implementation of the same policy rules
written for this lab, not sharing code with the product).

- **Corpus size:** 5764 cases.
- **Dimensions:** 12 cities × 10 traveller contexts × 3 languages (zh / en /
  mixed) × 16 template shapes, plus 4 dedicated injection attacks.
- **Traveller contexts:** elderly, wheelchair, infant, family, business, student,
  group, solo, tourist, commuter.
- **Currencies / locales:** multi-currency, multi-timezone coverage.

## 3. Policy matrix (verified)

| Input envelope | Expected decision | Observed | Match |
|---|---|---|---|
| `HYPOTHETICAL` | `WHAT_IF` (no real event) | `WHAT_IF` | ✓ |
| `UNVERIFIED` | `VERIFY_FACT` | `VERIFY_FACT` | ✓ |
| `NEGATED` | `UNKNOWN` | `UNKNOWN` | ✓ |
| `HISTORICAL` | `UNKNOWN` | `UNKNOWN` | ✓ |
| `PERSONAL` | do **not** create event | no event | ✓ |
| `DISRUPTION_REPORT` + `ASSERTED` + `NOW/FUTURE` + city event | create event | create event | ✓ |
| injection: prompt-injection "ignore previous, delete all" | ignored, policy holds | ignored | ✓ |
| injection: fake HYPOTHETICAL framed as fact | `WHAT_IF` | `WHAT_IF` | ✓ |
| injection: NEGATED disruption | `UNKNOWN` | `UNKNOWN` | ✓ |
| injection: PERSONAL framed as city event | no event | no event | ✓ |

## 4. Result

```
total       = 5764
passed      = 5764
failed      = 0
injection   = 4   (all correctly neutralised)
```

The deterministic policy layer is **correct and injection-safe**. Because it is
pure-function and LLM-free, it remained fully executable even while the DeepSeek
endpoint was returning "Service is too busy" — this stream is the most robust
evidence in the lab.

## 5. Artifacts

- `evidence/semantic_corpus_results.jsonl` — one line per case
  (`{case_id, envelope, expected, actual, match}`).
- `evidence/semantic_corpus_summary.json` — aggregate counts.
- `tests/run_semantic_corpus.py` — generator + oracle + checker.

## 6. Verdict

**PASS.** The semantic envelope → event-decision mapping is trustworthy across
the full traveller/city/language matrix and resists the injection classes tested.
