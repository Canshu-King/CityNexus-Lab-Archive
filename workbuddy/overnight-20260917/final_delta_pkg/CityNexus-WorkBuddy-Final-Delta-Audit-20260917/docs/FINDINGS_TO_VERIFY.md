# Findings to verify

## F1 — Copilot place question evidence is stale

The canonical final visible trace still shows:

`鼓浪屿好玩吗？`

answered with:

`我没有可靠识别这条请求`

A later source change appears to add a DISCOVER classifier for "好玩/值得/怎么样",
but there is no post-fix visible proof in the submitted canonical trace.

Verify the FINAL current UI after the fix.

Expected:
- useful Chinese answer or grounded search result;
- current-trip context;
- human actions;
- no raw enum.

## F2 — Copilot still leaks engineering vocabulary

Final source still contains traveler-facing strings involving:
- PlanVersion
- TravelerTwin
- deterministic feasibility / internal planning vocabulary

Verify common intents, not only the place question.

Default traveler UI must not expose these terms.

## F3 — Me still exposes policy internals

Final Xiaomi screenshot/source shows:
- `我的 · 权限边界`
- `ADVISORY`
- `CN-XIAMEN`

These belong behind Advanced/Developer.

Normal Me should use human city names and traveler settings.

## F4 — Booking canonical path still leaks internal labels

Canonical evidence shows strings such as:
- Journey Memory
- manual-entry
- Departure anchor
- UNKNOWN
- STRUCTURED_JSON
- DETERMINISTIC

Verify current primary booking flow.

Raw internal extraction/semantic labels must not be the default traveler surface.

Also verify confirmed:
- amount;
- origin/destination;
- booking identity;
- Trips/Today appearance.

## F5 — Secondary Wallet route remains raw JSON-first

Inspect `/v8/bookings` / wallet secondary surface.

If raw JSON remains primary:
- it must be clearly Advanced/Developer;
- consumer booking import must remain the normal path.

## F6 — Activity Detail known-free rendering

Final source appears to compute price-known as:

`amount_minor > 0`

This makes a known-free attraction display `暂无价格`.

Verify:
- known free -> `免费`
- known paid -> amount
- unknown -> `暂无价格`

## F7 — Partial price evidence can still produce false budget labels

Plan comparison appears to treat "any known price" as enough to call the total:
- 预算内
- 接近预算
- 超预算

Verify partial coverage.

Expected:
- incomplete cost coverage -> `总价未知`, `已知部分`, or equivalent;
- no false confidence from a partial sum.

## F8 — Budget sanity advisory is missing

The overnight mission required an advisory for extreme combinations such as:

39 days / 2 people / CNY 3000

Verify the FINAL UI.

Expected:
- approximate daily budget;
- warning;
- edit budget;
- continue intentionally.

Do not require an exact forecast.

## F9 — Direct `/v8/today` and `/v8/copilot` resilience

Final route parser may only understand canonical keys:
- hub
- agent

Verify deep links:
- `/v8/today`
- `/v8/copilot`

Expected:
- redirect/alias or useful page;
- no blank route.

## F10 — AI planning false-success can recur when old plans already exist

The current UI may decide planning succeeded merely because:

`plans.length > 0`

after the run.

Test:
1. journey already has an old/selected plan;
2. start a NEW AI planning request;
3. force the new run to produce no new candidate plan;
4. observe terminal state.

Expected:
- the NEW run is not marked success merely because an old plan exists;
- success requires a new artifact/candidate relationship attributable to the run.

## F11 — Final trace acceptance claims are weak in two places

Inspect:
- stay truth evidence showing `undefined` check-in/out fields;
- "triple agreement" where Trips visible count and backend count differ.

This may be explainable by UI filtering, but the assertion must prove what it claims.

Do not accept vague "consistent" statements without a defined comparison.

## F12 — Package replayability

The exported source package may be missing root-level data expected by tests and
the review environment may lack dependencies.

This is not automatically a product blocker.

But distinguish:
- EAC self-reported test count;
- independently replayed tests;
- tests that cannot be replayed from the packaged artifact.
