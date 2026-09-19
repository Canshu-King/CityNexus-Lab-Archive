# CAPABILITY_SEMANTICS_RESULTS.md — Conservative semantic fallback

## Policy implemented

| Input class | Behaviour |
| --- | --- |
| Explicit first-person need | candidate capability (HARD only when genuinely mandated) |
| Hedged first-person need | `STRONG` + `needs_confirmation`, candidate only, never silently HARD |
| Explicit negation / exclusion | no traveller HARD need |
| Third-party need | never silently a traveller HARD need |
| Unknown travelling-party relation | clarification / candidate only |

DeepSeek remains the primary interpreter. This round hardens the **local
fallback** so it fails conservatively, and never invents a need from a denial.

## Numeric language correctness

| Sentence | Result |
| --- | --- |
| `走路不能超过 1.5 公里` | `max_m = 1500` |
| `走路不能超过 2.5 公里` | `max_m = 2500` |
| `走路不能超过 0.5 公里` | `max_m = 500` |
| `走路不能超过 1.5 米` | `max_m = 2` (half-up) |
| `走路不能超过 0.5 米` | `max_m = 1` (half-up) |
| `走路不能超过 0 米` | `max_m = 0` **and** `needs_clarification = true`, severity `STRONG` — never a clean HARD zero cap |
| `连续走不能超过 20 分钟` | `MAX_CONTINUOUS_WALKING_MIN = 20`, and **no** `MAX_WALKING_PER_LEG_M` |
| `我每天走路不能超过 3000 米` | daily semantics only (`MAX_DAILY_WALKING_M`), not per-leg |
| `每段不超过 100 米` / `单段步行不超过 100 米` / `每次走路不超过 100 米` / `不要走超过 100 米` | per-leg |
| `walk no more than 100 m` | per-leg 100 m |

The clause splitter is decimal-safe (`(?<!\d)\.(?!\d)`), so `1.5` is never
split into `1` and `5`. Units are classified (distance vs duration) and scope
tokens are explicit (daily vs per-leg). `no more than` is treated as a bound,
not a denial.

## Conservative fallback — verified cases

**Preserved (no traveller need created):**

* `I don't need a wheelchair, I can walk`
* `朋友说我可能需要轮椅，但我不这么认为`
* `my friend needs a wheelchair, not me`
* `my mother uses a wheelchair`
* `我妈妈坐轮椅`
* `the station has an accessible toilet`
* `我朋友需要轮椅，不是我`
* `说不定到时候我需要轮椅` / `if I end up in a wheelchair I will tell you`

**Kept as a need (never silently dropped):**

* `if possible I need step-free access` -> `STEP_FREE_REQUIRED` STRONG
* `如果可能的话我需要无障碍通道` -> `STEP_FREE_REQUIRED` STRONG
* `maybe I need a wheelchair` -> `STEP_FREE_REQUIRED` STRONG
* `我可能需要轮椅` -> `STEP_FREE_REQUIRED` STRONG
* `如果能推婴儿车就方便多了` -> `STROLLER` STRONG (context preference under a conditional is surfaced, never HARD)
* `我妈妈要午休` -> `MIDDAY_REST_WINDOW` STRONG
* `我父亲走不了远路` -> `MAX_WALKING_PER_LEG_M` STRONG with `needs_clarification`
* `just for today I cannot walk far` -> journey-scoped walking limit

## Evidence

* `evidence/capability_semantics_d.json` — independent WorkBuddy probe:
  **64/64 ok, 0 failing** across
  `G1_false_hard 9/9`, `G1_mandated_guard 2/2`, `G2_scope_dedup 2/2`,
  `G2_numeric_merge 1/1`, `G2_permanence_scope 1/1`, `G2_this_trip_scope 1/1`,
  `G3_facility_tags 12/12`, `G3_route 2/2`, `G3_positive 4/4`,
  `G3_contradiction 7/7`, `G3_tag_shapes 5/5`, `G4_numeric 8/8`,
  `G4b_natural_phrasing 6/6`, `G4_zero_policy 1/1`, `G4_window 2/2`,
  `G4_nap 1/1`.
* `evidence/p0_numeric_d.json` — `n1_violations 0/7`, `n2_n3_defects 0/6`.
* `evidence/guard_suites_run.txt` — capability guard suites 181 passed.

## Known contradictory pair

`走路不能超过 0 米` is claimed by two mutually exclusive expectations; see
`TEST_RESULTS.md` §2.1(a). The chosen resolution satisfies the upstream V19.2
contract and keeps the parsed value, but never as a clean authoritative HARD
cap.
