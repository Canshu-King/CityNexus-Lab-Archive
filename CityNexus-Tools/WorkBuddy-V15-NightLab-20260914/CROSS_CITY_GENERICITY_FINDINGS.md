# V15 Cross-City Genericity Findings

**Cities exercised:** 福州 (CN-FUZHOU / Asia-Shanghai / CNY),
上海 (CN-SHANGHAI), 北京 (CN-BEIJING),
Singapore (SG-SINGAPORE / Asia-Singapore / SGD),
Tokyo (JP-TOKYO / Asia-Tokyo / JPY),
London (GB-LONDON / Europe-London / GBP).

**Raw data:** `evidence/cross_city_probe.json`, `evidence/v14_command_probe.json`.
**Tests:** `backend/tests/test_v15_cross_city_genericity.py` (green guarantees +
`xfail` gaps), `backend/tests/test_v15_copilot_v14_gaps.py` (locale gap).

---

## Summary of confirmed leaks

| # | Leak | Where | Severity | Status |
|---|---|---|---|---|
| CC-1 | Copilot replies in Chinese to Singapore and Tokyo journeys | `backend/app/main.py` `copilot_message` | High — visible to every non-CN user | test + `xfail` |
| CC-2 | `海河沿线` (Tianjin's Haihe river) injected into any journey when the message says "river" | `backend/app/main.py` `run_agent_command` | High — invents a place in the wrong city | test + `xfail` |
| CC-3 | Mission budget bound is a currency-less minor-unit int, scaled ×100 | `backend/app/agent/mission.py` | High — 100× error on JPY | test + `xfail` |
| CC-4 | Money regex misses the English word "budget" | `backend/app/agent/mission.py` `_MONEY_PATTERN` | Medium | test + `xfail` |
| CC-5 | Frontend renders every amount as `CNY` and divides by 100 | `frontend/src/app/V8Experience.tsx` etc. | High — wrong symbol **and** wrong magnitude | see `FRONTEND_UX_REVIEW.md` |
| CC-6 | Trial setup defaults currency to `CNY` regardless of timezone | `frontend/src/features/setup/JourneyTrialSetup.tsx` | Medium | see `FRONTEND_UX_REVIEW.md` |
| CC-7 | Frontend supports only `en` and `zh-CN` | `frontend/src/i18n/LocaleContext.tsx` | Medium | see `FRONTEND_UX_REVIEW.md` |

## What already holds (verified, keep it)

* Journey `timezone`, `currency` and `city_code` round-trip correctly for all five
  cities — the storage layer is not the problem.
* `capture_real_city_candidates` refuses to substitute Tianjin replay data for a
  non-Tianjin city, and reports `wrong_city_replay_blocked: true`, for **all four**
  non-Tianjin cities. The V14 guard generalises; only the copilot layer does not.

---

## CC-1 — Copilot locale coercion

`backend/app/main.py`, `copilot_message`:

```python
locale="zh" if journey.timezone.startswith("Asia/") else "en",
```

Measured (deterministic fallback provider, no API key needed):

| journey | timezone | declared UI locale | reply language | correct? |
|---|---|---|---|---|
| CN-FUZHOU | Asia/Shanghai | zh-CN | Chinese | yes |
| CN-SHANGHAI | Asia/Shanghai | zh-CN | Chinese | yes |
| SG-SINGAPORE | Asia/Singapore | en | **Chinese** | **no** |
| JP-TOKYO | Asia/Tokyo | ja | **Chinese** | **no** |
| GB-LONDON | Europe/London | en | English | yes |

Two of the five cities are wrong, and both are wrong in the same direction. Any
`Asia/*` zone is treated as China. The declared traveler locale — which the API
already has — is ignored entirely.

**Fix shape (reference implementation provides `resolve_locale`):** prefer the
traveler's declared locale, then a small timezone→language map
(`Asia/Singapore→en`, `Asia/Tokyo→ja`, `Asia/Seoul→ko`, `Asia/Shanghai→zh`),
then a default. Never derive language from `startswith("Asia/")`.

## CC-2 — Tianjin place hint injected into a London journey

`backend/app/main.py`, `run_agent_command`:

```python
"affected_place_hint": "海河沿线"
if any(token in normalized for token in ("海河", "haihe", "river"))
else None,
```

Measured against a **GB-LONDON** journey:

| message | `affected_place_hint` |
|---|---|
| 现在海河那边涨水了。 | `海河沿线` |
| **The river is flooding near the pier.** | **`海河沿线`** |
| haihe is flooded | `海河沿线` |

Any English sentence containing the word "river" stamps a Tianjin place name onto
a London event payload. This is the same class of defect the V14
`wrong_city_replay_blocked` guard was built to stop, but it survives in the
free-text command path.

**Fix shape:** drop the hardcoded literal. Either leave the hint `None` and let
the Journey projection supply the target (which the surrounding comment already
claims is the intent), or resolve the hint through the journey's own
discovery/place provider.

## CC-3 — Currency-less, ×100 budget bound

`backend/app/agent/mission.py`:

```python
match = _MONEY_PATTERN.search(command)
max_cost = round(_parse_number(match.group(1)) * 100) if match else 0
```

`MissionSpec.as_dict()` and `mission_payload()` expose `max_cost_delta_minor`
and `max_loss_minor` with **no currency field anywhere**. Consequences:

* a Tokyo bound of `8000 日元` becomes `800000` "minor units" — a 100× inflation,
  because JPY has no minor unit;
* downstream code cannot tell whether a bound of `20000` means 200 CNY, 200 GBP
  or 20000 JPY.

**Fix shape:** carry `{amount_minor, currency}` together, and scale by the
currency's exponent (`0` for JPY/KRW, `2` for CNY/GBP/SGD, `3` for KWD) rather
than a hardcoded `100`.

## CC-4 — Money vocabulary gaps

`_MONEY_PATTERN` matched / did not match:

| message | matched | note |
|---|---|---|
| 最多多花 500 元 | yes | |
| 不超过 3000 元 | yes | |
| 预算 5000 元 | yes | |
| under 500 SGD | yes | number captured, currency suffix not |
| less than 200 GBP | yes | currency suffix not |
| 不超过 8000 日元 | yes | currency suffix not |
| 预算不超过 100 新加坡元 | yes | currency suffix not |
| **budget 50000 JPY** | **no** | English "budget" keyword missing |
| loss limit 100 EUR | no (in `_MONEY_PATTERN`) | handled by the separate `_LOSS_PATTERN` |

The currency suffix alternation is `(?:元|块|CNY)?` — optional, and only ever CNY.
So the parser silently accepts non-CNY amounts and drops their currency. Add the
English "budget" keyword, and capture the currency token instead of discarding it.

## CC-5/6/7 — Frontend

See `FRONTEND_UX_REVIEW.md`. The important one: `money()` in
`frontend/src/app/V8Experience.tsx` **always divides by 100** and is called with a
hardcoded `"CNY"` at ~15 sites, so a Tokyo stay budget of ¥80,000 renders as `¥80`.

---

## Priority for V15

1. **CC-2** — one-line literal to delete; highest ratio of damage to effort.
2. **CC-1** — a wrong-language reply is the first thing a trial user notices.
3. **CC-3** — silent 100× money errors are the kind of thing that ends a trial.
4. **CC-4** — cheap vocabulary fix.
5. **CC-5/6/7** — frontend; bigger, but CC-5 is a two-line change
   (`currency` from the journey + a per-currency exponent).
