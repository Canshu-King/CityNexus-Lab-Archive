# V16 Real-User Lab — Product-Logic Findings Catalogue

**Scope:** CityNexus Smart-City Traveller System. A simulated "real user" drove the
product's own front end across 12 traveller personas in 12 different cities
(including county towns and non-CNY currencies), injecting the kinds of
disruptions and requests a real traveller types into the DeepSeek chat desk.
Every product-logic defect found was fixed **in place** and re-tested, in the
spirit of the V16 directive ("你发现产品不符合正常逻辑的地方…就进行自己完善").

**Severity legend:** Critical = the product produced a wrong or empty result for a
common, real input. High = correct only for the two demo cities / CNY, silently
wrong otherwise. Medium = edge-case breakage. Roadmap = recognised gap this patch
does not yet close.

---

## F2 — Every free-text command became a fabricated city WEATHER event  `CRITICAL`

**Observed:** The V14 endpoint `POST /journeys/{id}/agent/commands` had a
two-line classifier:

```python
has_traffic = any(tok in text for tok in ("交通管制","拥堵","封路",...))
event_type = "TRAFFIC_DELAY" if has_traffic else "WEATHER"
```

So a **self-description** ("我们 11 点才起"), a **question** ("如果明天下雨会怎样？"),
a **comfort preference** ("我想少走路。") and a **personal emergency** ("我护照丢了。")
all became a `MAJOR` city WEATHER event. The V15 lab built and verified a semantic
router that separates these cases, but *no production path ever imported it* — it
was reachable only from tests.

**Fix:** New module `backend/app/agent/command_intent.py` is the missing seam. It
consults the router, then decides whether a city Event is warranted, and if so
which of the four actionable types (`WEATHER / TRAFFIC_DELAY / CLOSURE /
SCHEDULE_DELAY`) and how severe. Personal situations (passport, fever, dead phone,
stolen wallet) file **no** city Event.

**Validated end-to-end:**
`self-description → REPLAN_REQUEST / no-event` · `WHAT_IF → no-event` ·
`"我想少走路。" → PREFERENCE_CHANGE / no-event` · `"我护照丢了。" → no-event` ·
`"火车晚点三个小时" → SCHEDULE_DELAY / CRITICAL` · `"博物馆关门了。" → CLOSURE / MAJOR`.
Regression tests: `test_decide_command_*`.

---

## F1 — Closure reports were silently dropped  `CRITICAL`

**Observed:** "博物馆关门了。" (the verb people actually use) was classified
`UNKNOWN`, so the disruption opened no mission and no event. The closure
vocabulary only contained nouns like `关闭 / 闭馆`, never `关门 / 没开门 / 歇业 /
维修 / 施工中 / 暂停开放 / 停电 / 停水`.

**Fix:** `semantic_router.DISRUPTION_NOUNS` extended (lines 139–151) with the
closure verbs above plus English (`shut`, `out of service`, `under maintenance`,
`no longer open`, `power cut`, `closed today`).

**Validated:** `"博物馆关门了。" → DISRUPTION_REPORT / CLOSURE / MAJOR / creates_event=True`.

---

## F4 — Uncaptured cities returned ZERO plan options and Null-Island geometry  `CRITICAL`

**Observed:** `data/v9/city_operations.json` contains exactly two captured cities
(`CN-TIANJIN`, `CN-BEIJING`). For every other city the planner silently:
(a) produced **zero** stay/plan options (a 3-day Fuzhou trip was an empty product);
(b) fell back to centre `(0.0, 0.0)` — Null Island in the Gulf of Guinea — so any
synthesised place sat 12 000 km from the hotel; (c) raised `HTTP 500`
(`MobilitySnapshotCaptureError`) because the legacy composer captured mobility for
hard-coded demo place ids before checking they existed.

**Fix:** New module `backend/app/planning/city_registry.py`. Uncaptured cities get
a clearly-labelled `DERIVED_GENERIC` template built from a real `CITY_CENTRES`
table (60+ destinations incl. county towns and Hong Kong / Macao / Taipei recorded
with the `CN-` prefix). County towns receive a shorter, walkable day (no metro).
Every synthesised place carries `cost_status = UNKNOWN/ESTIMATED`, never `KNOWN`.

**Validated:** Fuzhou `options=3` (was 0); 沙县 `options=3`; 敦煌 `options=3`;
`city_centre("CN-FUZHOU")["latitude"] == 26.0745` (not 0.0).

---

## F5 — Currency minor-unit bug: 0-decimal currencies were wrong by 100×  `HIGH`

**Observed:** All fares were hard-coded in CNY minor units for every journey, so a
London bus was priced at £4.00 and a Tokyo ride at ¥4. JPY/KRW/VND/IDR have **no**
minor unit, so `1600` minor meant ¥16 instead of ¥1600, and GBP's 2 decimals were
mishandled. Real consequence: a Tokyo business-trip traveller (P08) saw meaningless
money.

**Fix:** `_MODE_FARES_MINOR` is now a per-currency table storing each currency's own
*indicative* minor amount (JPY `AUTO=1600` = ¥1600, not ¥16). CNY keeps the
historic `KNOWN` status; every other currency is explicitly `ESTIMATED`.

**Validated:** Tokyo stay total `22960 JPY`, nightly `11480 JPY`, mobility
`AUTO 1600 JPY ESTIMATED`.

---

## F3 — No traveller "body clock": everyone treated as a 09:00–18:30 sightseer  `HIGH`

**Observed:** Candidate activities carry absolute clock times and the overnight
block is hard-coded `22:30 → 06:30`. A couple who sleep at 02:00 / wake at 11:00
(P01) got a 07:30 breakfast and 08:00 museum slot; a photographer who leaves at
04:00 (P11) got the opposite mismatch. This is **not** a language problem — the
words are unambiguous, the *planner* has no representation for rhythm.

**Fix:** New module `backend/app/planning/day_rhythm.py` reads the traveller's own
words (`extract_day_rhythm`), filters optional sightseeing to the waking window
(`apply_day_rhythm`), and re-times the overnight block. It is strictly advisory:
locked anchors (arrival / check-in / check-out / departure) are never moved.

**Validated:** P01 self-description extracted `wake 11:00 / bed 02:00 / brunch`;
after the Guardian/mission learned it, days 2–3 dropped 8 → 4 activities (morning
slots removed, TRANSIT → BICYCLE), `options_regenerated=True`.

---

## F6 — Short-message length gate rejected valid input  `MEDIUM`

**Observed:** A schema length rule rejected the perfectly valid 6-character Chinese
message "我想少走路。" as "too short", so a comfort preference could not be entered
at all.

**Fix:** `schemas.py` length gate relaxed/removed for the agent command field.

**Validated:** "我想少走路。" now routes to `PREFERENCE_CHANGE` and is accepted.

---

## F7 — Party-size / room-count not reflected in stay options  `MEDIUM`

**Observed:** A 6-friend group (P09) and a family with two kids (P06) received the
same standard-twin room options regardless of party size.

**Fix:** `city_registry.derive_generic_profile` selects `Family room` when
`party_size > 3`; stay option generation threads party size through.

---

## F8 — Derived templates could be presented as captured evidence  `MEDIUM`

**Observed:** Nothing stopped a synthesised, indicative template from being shown
as if it were real provider data.

**Fix:** `services.py` template guard + every derived place carries
`provenance=DERIVED_GENERIC` and `cost_status=UNKNOWN/ESTIMATED` (see F4).

---

## F9 — `stay_mobility.discover` NameError crash on generic profiles  `MEDIUM`

**Observed:** When a derived profile was used, `discover` referenced an attribute
that only existed on captured fixtures, raising an uncaught `NameError` and failing
plan generation.

**Fix:** `stay_mobility.py` guards the attribute and falls back to the generic path.

---

## F10 — Locale leak: `Asia/*` timezones rendered as Chinese  `MEDIUM`

**Observed:** The locale rule was `"zh" if timezone.startswith("Asia/") else "en"`,
so Singapore (P09) and Tokyo (P08) were wrongly forced into Chinese UI text.

**Fix:** `i18n/LocaleContext.tsx` prefers the declared UI locale, then a small
timezone→language map, then a default.

---

## F11 — Accessibility is not modelled at all  `ROADMAP / COMPLIANCE`

**Observed:** Wheelchair user (P12), elderly parents (P03, no stairs / midday rest
/ toilet every 90 min) and infant family (P04, stroller / nursing room / nap window)
found the product has **no** accessibility, mobility-capacity or rest-window fields.
This is a compliance risk, not just UX.

**Status:** Out of scope for this patch. The day-rhythm and generic-profile fixes
help P03/P04/P11 partially (remove impossible early slots, give a sane day shape),
but full accessibility modelling (step-free routing, elevator requirement,
attention-span / nap-window insertion, child/elder ticket pricing) is flagged for
the next iteration. Documented here so it is not lost.

---

## F12 — `GET /twin` could 500 with "database is locked" under concurrent load  `LOW / ROBUSTNESS`

**Observed:** During the 12-persona run, one `GET /api/v1/journeys/{id}/twin` call
(P10) returned **500** with `sqlite3.OperationalError: database is locked`. The
`/twin` endpoint computes a projection and then *writes* it back to the
`journey_twins` cache row inside the same request. Under concurrent twin polling
against the isolated single-file SQLite DB (no `busy_timeout`), a transient write
lock collided and the read turned into a 500. The same journey served 200 on every
subsequent call, confirming the lock was transient, not systematic.

**Why it is still worth fixing:** a *read* path that can 500 under mild
concurrency is unreasonable, and a user who hits a locked-write race should not
lose the twin payload. This is an infrastructure-adjacent robustness gap, not a
core product-logic defect.

**Fix:** `_twin_snapshot` now persists the twin row in a **savepoint**-guarded,
best-effort block. A transient lock rolls back only that savepoint (never other
pending work in the request) and logs a warning; the computed snapshot payload is
returned regardless. The caller's `session.commit()` is unaffected.

**Validated:** backend reloads cleanly; regression suite still green; the guarded
path returns the snapshot for every persona on reload.

---

## Summary of fix surfaces

| ID | Severity | Module added / changed | Validated |
|----|----------|-----------------------|-----------|
| F2 | Critical | `agent/command_intent.py` (new) + `main.py` | ✓ 17 regression tests |
| F1 | Critical | `agent/semantic_router.py` | ✓ |
| F4 | Critical | `planning/city_registry.py` (new) | ✓ |
| F5 | High | `stay_mobility.py` | ✓ |
| F3 | High | `planning/day_rhythm.py` (new) + `mission.py` + `authoritative_v12.py` | ✓ |
| F6 | Medium | `schemas.py` | ✓ |
| F7 | Medium | `city_registry.py` | ✓ |
| F8 | Medium | `services.py` | ✓ |
| F9 | Medium | `stay_mobility.py` | ✓ |
| F10 | Medium | `i18n/LocaleContext.tsx` | ✓ |
| F11 | Roadmap | — | documented |
| F12 | Low | `main.py` (`_twin_snapshot`) | ✓ (reload + regression) |
