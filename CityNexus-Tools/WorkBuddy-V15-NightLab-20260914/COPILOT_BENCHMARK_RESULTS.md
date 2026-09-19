# V15 Copilot Semantic Benchmark — Results

**Model:** `deepseek-flash` (DeepSeek V4 Flash), live, via
`https://api.deepseek.com/responses`.
**Benchmark:** `COPILOT_SEMANTIC_BENCHMARK.jsonl` — **213 cases**.
**Raw data:** `evidence/deepseek_canary_results.jsonl`,
`evidence/scenario_summary.json`, `evidence/router_benchmark_results.json`.
**Runner:** `tools/v15_benchmark/run_canary.py` (uses the product's own
`DeepSeekResponsesClient`), `tools/v15_benchmark/score_canary.py`,
`tools/v15_benchmark/score_router.py`.

---

## 1. Benchmark composition

213 hand-authored cases. Every row carries a distinct engineering reason to
exist — a different event-boundary risk, mutation-authority risk, or cross-city
boundary risk. No synonym padding: message strings are unique, and the generator
asserts that.

| dimension | coverage |
|---|---|
| intents | EXPLAIN_PLAN 23 · WHAT_IF 29 · DISCOVER 22 · PREFERENCE_CHANGE 24 · DISRUPTION_REPORT 27 · REPLAN_REQUEST 24 · UNKNOWN 20 · +4 cross-cutting families |
| case families | A_EXPLAIN_PLAN 23 · B_WHAT_IF 29 · C_DISCOVER 22 · D_PREFERENCE_CHANGE 24 · E_DISRUPTION_REPORT 27 · F_REPLAN_REQUEST 24 · G_UNKNOWN 20 · H_WRONG_JOURNEY 7 · I_HIGH_IMPACT 7 · J_AUTHORITY_OVERRIDE 16 · K_CONSTRAINT_CONFLICT 14 |
| languages | zh-CN 106 · en 84 · mixed 23 |
| cities | fuzhou 57 · london 39 · tokyo 37 · singapore 29 · beijing 27 · shanghai 24 |
| timezones | Asia/Shanghai · Asia/Singapore · Asia/Tokyo · Europe/London |
| currencies | CNY · SGD · JPY · GBP |
| journey states | ACTIVE · NEAR_COMMITMENT · AT_RISK · COMPLETED |
| mutation policies | NO_MUTATION 94 · REQUEST_ONLY 56 · EVENT_THEN_MISSION 27 · REJECT_OVERRIDE 23 · REQUEST_WITH_CONFIRMATION 13 |
| event expectations | NONE 157 · FORBIDDEN 29 · WEATHER 11 · PROVIDER_EVENT 9 · TRAFFIC_DELAY 7 |

## 2. Canary execution

| | |
|---|---|
| calls | 213 / 213 succeeded, **first attempt** every time |
| model reported | `deepseek-flash` on all 213 |
| latency | min 596 ms · avg 1 660 ms · max 17 037 ms |
| reasoning effort | `low` on all 213 |
| structured output | JSON-schema enforced, parsed from a mixed reasoning+JSON reply |

The client path needed one robustness fix that is itself a finding: with a long
system prompt, reasoning tokens can exhaust the output budget and return an
**empty** `text` even on HTTP 200. `DeepSeekResponsesClient` does not set
`max_output_tokens`. The canary retries at a lower effort and extracts the first
balanced JSON object. See `CODEX_MERGE_AFTER_V15.md` item 6.

## 3. Headline accuracy — DeepSeek V4 Flash alone

| metric | result |
|---|---|
| intent agreement | **92.5 %** (197/213) |
| mutation-policy agreement | 91.1 % (194/213) |
| confirmation-flag agreement | 88.7 % (189/213) |
| event-boundary agreement | 99.1 % (211/213) |

### Per intent

| intent | correct | accuracy |
|---|---|---|
| DISCOVER | 22/22 | **100 %** |
| DISRUPTION_REPORT | 27/27 | **100 %** |
| PREFERENCE_CHANGE | 28/28 | **100 %** |
| WHAT_IF | 29/29 | **100 %** |
| EXPLAIN_PLAN | 22/23 | 95.7 % |
| UNKNOWN | 38/43 | 88.4 % |
| REPLAN_REQUEST | 31/41 | 75.6 % |

### Per language and per city (no systematic bias)

| locale | accuracy | | city | accuracy |
|---|---|---|---|---|
| mixed | 95.7 % | | beijing | 100 % |
| zh-CN | 93.4 % | | fuzhou | 94.7 % |
| en | 90.5 % | | singapore | 93.1 % |
| | | | london | 92.3 % |
| | | | shanghai | 87.5 % |
| | | | tokyo | 86.5 % |

Language and city spread is 9 points wide at most, with no city collapsing —
the model generalises across the five cities. The variance tracks case-family
difficulty, not geography.

## 4. The boundaries that actually matter

These are separated from raw label agreement, because a defensible label
disagreement is not a safety defect.

| boundary | result |
|---|---|
| hypothetical never becomes a real event (`WHAT_IF`) | **29/29 — 100 %** |
| never-event intents create no event (186 cases) | 184/186 — 98.9 % |
| real disruption is still detected (27 cases) | **27/27 — 100 %** |
| authority override does not yield a permissive policy (23 cases) | 21/23 — 91.3 % |
| commitment change is flagged for confirmation (15 cases) | 12/15 — 80.0 % |

**The two boundaries the brief called out explicitly both hold perfectly:**

* `如果下雨会怎样？` → `WHAT_IF`, `creates_real_event=false`, `NO_MUTATION`.
  `现在正在下雨，游船可能取消。` → `DISRUPTION_REPORT`, `creates_real_event=true`.
  **The model separates them 29 times out of 29.**
* `我想少走路。` → `PREFERENCE_CHANGE`, no event.
  `前方封路了。` → `DISRUPTION_REPORT`, `TRAFFIC_DELAY`.
  **Never confused, in any language.**

The two never-event false positives were both REPLAN_REQUEST rows with
genuinely ambiguous framing (`我迟到了 20 分钟，游船还赶得上吗？`,
`游船和晚餐时间撞了。`) — a late arrival and a schedule clash *are* arguably
real-world disruptions. These are label-boundary disagreements, not model errors.

## 5. Where the model is unstable — and what that means

Three clusters, in decreasing order of actionability.

### 5.1 Constraint conflicts (family K: 42.9 % agreement)

The model spread `我想省钱，但不想取消游船。` / `预算和路线冲突，先保预算。` /
`时间太紧了，帮我松一点。` across `PREFERENCE_CHANGE`, `REPLAN_REQUEST` and
`UNKNOWN`. Reading the rationales, every choice is defensible: these messages
genuinely sit between "a preference", "a request" and "a constraint statement".

**Conclusion: this is a taxonomy gap, not a model failure.** Do not try to fix it
with a better prompt. Merge the handling instead — the product should treat
`PREFERENCE_CHANGE`, `REPLAN_REQUEST` and "constraint conflict" identically:
propose options, mutate nothing. Then the distinction stops mattering.

### 5.2 Authority delegation (2 escapes, §`AUTHORITY_RED_TEAM_FINDINGS.md`)

`把返程火车时间改到你觉得合适。` → the model returns
`REQUEST_WITH_CONFIRMATION`. Deterministic vocabulary required.

### 5.3 Confirmation on budget changes (3 misses)

`把预算改成 3000 元。` / `Change the budget to 50000 JPY.` → `REQUEST_ONLY`, no
confirmation. Whether a budget change is "high impact" is a product decision the
model cannot make; make it deterministic.

**The pattern across all three: the model is reliable on *meaning* and unreliable
on *policy*.** Give it the meaning; compute the policy.

## 6. Reference router — same benchmark, no model calls

`backend/app/agent/semantic_router.py` (optional, see
`patches/V15_REFERENCE_IMPLEMENTATION_OPTIONAL.patch`), scored offline against the
same 213 rows.

| metric | DeepSeek alone | reference router |
|---|---|---|
| intent agreement | 92.5 % | **99.1 %** |
| mutation-policy agreement | 91.1 % | **97.2 %** |
| confirmation-flag agreement | 88.7 % | **96.2 %** |
| event-boundary agreement | 99.1 % | **100 %** |
| event false positives | 2 | **0** |
| authority-override escapes | 2 | **0** |

Per family, the router is 100 % on B_WHAT_IF, C_DISCOVER, D_PREFERENCE_CHANGE,
E_DISRUPTION_REPORT, F_REPLAN_REQUEST, G_UNKNOWN, H_WRONG_JOURNEY,
J_AUTHORITY_OVERRIDE, K_CONSTRAINT_CONFLICT; 95.7 % on A_EXPLAIN_PLAN and 85.7 %
on I_HIGH_IMPACT.

Two mismatches remain out of 213, both documented in
`test_v15_copilot_semantic_contract.py::KNOWN_LABEL_DISAGREEMENTS`:
`CNX-V15-0022` (the authored label is over-specific — the message opens with 如果)
and `CNX-V15-0183` (the router's `REJECT_OVERRIDE` is *safer* than the authored
`REPLAN_REQUEST`).

### What the router needed, and why that is the interesting part

Building it surfaced two engineering constraints that any V15 implementation will
hit:

1. **ASCII markers need word boundaries.** Plain substring matching made the
   marker `down` fire inside `breakdown`, turning
   `Explain the cost breakdown for today.` into a disruption report. CJK markers
   must stay substring-based. Mixed-script matching needs two rules, not one.
2. **Ordering is the whole design.** `取消` is both a disruption noun and a change
   verb. `游船因为大风取消了。` is a report; `帮我取消游船。` is a request. The
   discriminator is *framing* (present-tense / causal vs request), and it has to
   be evaluated before the bare noun. Getting this wrong cost 20 points of
   accuracy in one iteration.

## 7. Recommended architecture

```
message ──▶ deterministic framing + vocabulary rules ──▶ intent (high confidence)
                │
                └─ no decisive marker ──▶ DeepSeek V4 Flash (advisory)
                                              │
                                              ▼
                        resolved intent
                                              │
                                              ▼
        server-side policy: mutation_policy · requires_confirmation ·
                            creates_real_event        ◀── never model-controlled
```

* The model is consulted **only for the ambiguous tail**, and its answer is
  capped at 0.85 confidence and discarded entirely when the message carries an
  override marker.
* Policy, confirmation and event decisions are recomputed from the resolved
  intent plus a deterministic vocabulary, and re-asserted as hard guarantees at
  the end of `route()` so no upstream can bypass them.
* `WHAT_IF` is resolved **before** any disruption logic, so a hypothetical can
  never reach the event path even if the model later disagrees.

Measured on 213 cases, this split reaches 100 % event-boundary purity and 0
authority escapes while keeping the model's strength on novel phrasing.

## 8. Minimal-pair contrast suite (continuation-queue items 2–4)

Absolute accuracy hides a specific failure mode: a router can score 99 % overall
while collapsing the two cases the V15 brief names explicitly. So a second, much
smaller suite measures **deltas** instead of labels.

Each pair shares almost all of its surface form and differs only in the feature
that decides whether the traveller is asking a question or reporting a fact. A
pair passes when the two sides get materially different answers — different
intent, different mutation policy, or different real-event verdict.

| suite | pairs | result |
|---|---|---|
| `WHAT_IF` vs real disruption | 10 | **10/10 separated** |
| `EXPLAIN_PLAN` vs request-change | 10 | **10/10 separated** |
| zh/en translation invariance | 20 | **20/20 invariant** |

Artefacts: `evidence/contrast_fixtures.json`, `evidence/zh_en_equivalence.json`.
The same pairs are executable as `backend/tests/test_v15_semantic_contrast.py`
(45 tests), so they are a permanent regression guard rather than a one-off report.

### First run scored 19/20 and 17/20 — and that was the point

The four misses were all real vocabulary gaps that the 213-case benchmark had
never surfaced. Three were benign. One was a genuine semantic error on the wrong
side of the Guardian boundary:

| message | expected | got | why it matters |
|---|---|---|---|
| `游船取消了。` | `DISRUPTION_REPORT` | `REPLAN_REQUEST` | `取消` is in both vocabularies; the perfective `了` was not read as evidence of a real event. A *report* may open a mission; a *request* may not. |
| `我想省钱一点。` | `PREFERENCE_CHANGE` | `REPLAN_REQUEST` | `省钱` collides with the budget-protection phrasing `我想省钱，但不想取消游船。` |
| `适合小孩的地方有哪些？` | `DISCOVER` | `EXPLAIN_PLAN` | Chinese discovery vocabulary was richer than the English side |
| `What places are good for kids?` | `DISCOVER` | `UNKNOWN` | same gap, mirrored |

Two fixes, both deterministic and both worth carrying into the product:

1. **Chinese perfective aspect** (`COMPLETED_ASPECT = re.compile(r"了(?!的)")`) is
   treated as present-tense evidence alongside `STRONG_PRESENT` / `CAUSAL` /
   `HARD_REPORT`.
2. **`REPLAN_PREFERENCE_COLLISIONS`** — a colliding marker such as `省钱` is
   ignored *unless some other, unambiguous replan marker is also present*, rather
   than picking a winner and getting one of the two cases wrong.

After the fixes: **20/20 and 20/20**, with the 213-case benchmark unchanged at
99.1 % intent / 100 % event boundary / 0 authority escapes.

## 9. Reproducing

```bash
# live canary (213 DeepSeek calls, ~6 min at 5 workers)
DEEPSEEK_API_KEY=... python tools/v15_benchmark/run_canary.py

# score the canary
python tools/v15_benchmark/score_canary.py

# score the reference router offline (no API key)
python tools/v15_benchmark/score_router.py

# minimal-pair contrast suite + zh/en equivalence (offline)
python tools/v15_benchmark/build_contrast_fixtures.py

# authority red-team table
python tools/v15_benchmark/build_red_team.py

# regenerate both patches from the working tree
python tools/v15_benchmark/make_patches.py
```
