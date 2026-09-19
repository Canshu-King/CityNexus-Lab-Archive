# Codex Merge Handoff — After V16 Real-User Lab

**Source workspace:** `D:\moodle\CityNexus-Tools\WorkBuddy-V16-RealUserLab-20260914`
**Target worktree:** `D:\moodle\CityNexus` (do **not** let the patch touch this file tree
outside a normal Codex review; the lab worked on an isolated copy).

## What V16 changed

V16 did not add framework. It closed the gap between the V15 semantic router
(verified but never wired in) and the production command endpoint, and added three
missing planner representations that no amount of language modelling could supply
(day rhythm, uncaptured-city templates, currency minor units).

### Files to merge (production)

| File | Change | Why |
|------|--------|-----|
| `backend/app/agent/command_intent.py` | **new** | The seam that maps one traveller command to a server-owned, auditable decision (intent + whether a real city Event is warranted + which of 4 types + severity). |
| `backend/app/agent/semantic_router.py` | edit | Added closure verbs (`关门/没开门/歇业/维修/施工中/暂停开放/停电/停水` + English) so "博物馆关门了。" reaches `CLOSURE`. |
| `backend/app/agent/mission.py` | edit | Guardian/mission now learns a traveller's day rhythm from self-description. |
| `backend/app/planning/authoritative_v12.py` | edit | Applies day rhythm when composing options. |
| `backend/app/planning/day_rhythm.py` | **new** | Day-rhythm model: `extract_day_rhythm`, `apply_day_rhythm`, `merge_rhythms`. |
| `backend/app/planning/city_registry.py` | **new** | `DERIVED_GENERIC` template for the 60+ cities with no captured provider data; real centres; county-scale awareness. |
| `backend/app/stay_mobility.py` | edit | Per-currency `_MODE_FARES_MINOR` (0-decimal currencies correct), `discover` NameError guard. |
| `backend/app/schemas.py` | edit | Relaxed the agent-command length gate so short valid messages are accepted. |
| `backend/app/services.py` | edit | Template guard — derived profiles can never be presented as captured evidence. |
| `backend/app/main.py` | edit | Wired `command_intent.decide_command` into `POST /journeys/{id}/agent/commands`. |
| `backend/tests/test_v16_realuser_fixes.py` | **new** | 17 offline regression tests (all passing) locking the fixes. |
| `frontend/src/app/V8Experience.tsx` | edit | Surface rhythm / derived-profile state. |
| `frontend/src/features/agent/AgentComposer.tsx` | edit | Render the new decision envelope (intent + event + severity) in the chat desk. |
| `frontend/src/features/setup/JourneyTrialSetup.tsx` | edit | Structurally address untagged money/party fields. |
| `frontend/src/i18n/LocaleContext.tsx` | edit | Fix `Asia/*` → Chinese locale leak. |

### How to apply

```bash
cd D:\moodle\CityNexus
git apply --check CityNexus-Tools/WorkBuddy-V16-RealUserLab-20260914/patches/v16_production.patch
git apply            CityNexus-Tools/WorkBuddy-V16-RealUserLab-20260914/patches/v16_production.patch
```

The patch is production-only and excludes the V16 test harness
(`frontend/_v16_trial/`, `tools/v16_realuser/`), the local vite config, the
scratch probes and the live `citynexus.db*`. Run `pytest tests/test_v16_realuser_fixes.py -q`
in the target backend after applying.

## What V16 explicitly did NOT fix (flagged for next iteration)

* **Accessibility modelling** (F11). Wheelchair step-free routing, elevator
  requirement, child/elder attention-span & nap-window insertion, midday-rest
  insertion, and child/elder ticket pricing are not yet represented. The
  day-rhythm and generic-profile work helps P03/P04/P11 partially but is not a
  substitute. This is a compliance risk, not just UX.
* **Real provider capture.** `DERIVED_GENERIC` is an honest template, not market
  data. Captured fixtures for the most-requested cities should be added over time.
