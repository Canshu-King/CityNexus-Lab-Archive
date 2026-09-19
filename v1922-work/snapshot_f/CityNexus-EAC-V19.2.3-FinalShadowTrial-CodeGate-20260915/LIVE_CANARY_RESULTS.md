# LIVE_CANARY_RESULTS.md — Live semantic canary (P1-4, A01)

## Availability

`DEEPSEEK_API_KEY` was present in the user's Windows environment
(HKCU\Environment), so one **bounded live canary** was run through the real
primary semantic compiler (`app.integrations.ai.semantic_compiler.compile_semantic_envelope`)
using `DeepSeekResponsesClient`.

The key was read into the process environment only. It was **never printed**,
never written to a log, and does not appear anywhere in this package. Only its
length (35) is recorded, as a redacted provenance note.

## Result — LIVE_DEEPSEEK_CANARY_PASSED

| Input | Live DeepSeek | Local fallback | Agreement |
| --- | --- | --- | --- |
| `I don't need a wheelchair, I can walk.` | no capability; assertion status `NEGATED` | no capability | yes |
| `I need step-free access for this trip.` | `STEP_FREE_REQUIRED` HARD | `STEP_FREE_REQUIRED` HARD | yes |
| `走路不能超过 1.5 公里。` | `MAX_WALKING_PER_LEG_M` `max_m = 1500` | same | yes |

The canary deliberately covers the two behaviours this round cares about most:

* a **negation** must not manufacture a traveller need (the live model returns
  `NEGATED` with no capability, matching the hardened local fallback);
* a **decimal distance** must survive intact (`1.5 公里` -> `1500 m`, not `1`).

## Scope

This is one bounded semantic call per input, not a full live-provider trial. It
establishes that the primary interpreter is reachable and agrees with the
conservative fallback on these inputs. It does not establish live performance,
cost, rate-limit behaviour under load, or behaviour on arbitrary phrasing.

## Evidence

`evidence/live_deepseek_canary.json` (no credential material inside).

## If credentials are unavailable elsewhere

The expected status in that case is
`LIVE_DEEPSEEK_CANARY_PENDING_PHYSICAL_TRIAL`, which is reported as a pre-trial
blocker rather than a pass. That branch was not taken here because the
credential was available.
