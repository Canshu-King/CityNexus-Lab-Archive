# High-confidence WorkBuddy findings

These are strongly supported in WB-O1 and should be rechecked first.

## WB-H1 — AI planning can falsely report success

Observed:
- UI says `方案已准备好`;
- progress stepper completes;
- `plan_versions = 0`;
- `/plans = []`;
- no selected/active plan.

This is a severe trust defect.

Required current behavior:
- success terminal only when a real plan artifact exists;
- otherwise honest failure/empty state;
- user journey must remain unchanged.

## WB-H2 — Booking import default flow is still developer-shaped

Observed:
- primary `预订 JSON` textarea;
- natural-language rail message causes `JSON.parse` error and no visible feedback;
- price shape mismatch can silently lose amount;
- internal labels `UNKNOWN_REALTIME` and `受保护 C4` are user-visible.

Required:
- paste text/manual/screenshot path is the default consumer flow;
- raw JSON only under Advanced;
- parse/extraction failures are localized and actionable;
- confirmed amount/origin/destination are visible and preserved.

## WB-H3 — Copilot leaks internal implementation language

Observed screenshot shows:
- DeepSeek;
- Hermes;
- Semantic / Execution / Truth;
- DISCOVER;
- giant `REQUEST_PLACE_SEARCH`.

Required:
- human traveler copy;
- human action buttons;
- provider/model/runtime detail only under Advanced.

## WB-H4 — Today / Copilot empty states can become blank

Observed no-plan state:
- `/v8/today` body largely empty;
- `/v8/copilot` route does not provide a useful traveler state.

Required:
- trip/no-trip aware empty state;
- primary next action;
- AI planning entry;
- no apparent white/dead page.

## WB-H5 — Hotel no-data state can masquerade as evidence

Observed:
- `Provider price unavailable · explicit`;
- `captured hotel · 0% confidence`;
- no actual `stay_journey_options`.

Required:
- explicit no-hotel/no-price state;
- never render absence as an evidence card.

## Positive controls worth preserving

WB-O1 also found good behavior:
- offline read-only state is explicit and honest;
- double-submit duplicate protection works;
- Trips and Map empty states can be honest;
- Copilot replan response can correctly say it will not directly mutate the plan.

Do not break these while fixing the blockers.
