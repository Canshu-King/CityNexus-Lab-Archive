# SEMANTIC_HARDPAIR_RESULTS.md

**Scope:** raw-language capability interpretation — what a user's sentence actually becomes.
**Corpora:**
- `evidence/semantic_cases.jsonl` — **120 cases / 116 unique texts / 39 pairs**, driven through
  the **live** DeepSeek path (`compile_semantic_envelope` + `apply_semantic_policy`), Snapshot A
  and Snapshot B. Results: `evidence/hardpairs_{a,b}.jsonl`, `evidence/hardpairs.jsonl`,
  `evidence/semantic_analysis_{a,b}.json`.
- `evidence/eac_differential.jsonl` — **182 cases / 176 unique texts**, deterministic offline
  comparison of `EAC_REFERENCE` vs `FINAL_V19` extractors. Summary:
  `evidence/eac_differential_summary.json`.

**Brief budget:** 120–180 live hard pairs (the previous round's 494-case sweep was explicitly
out of scope) and 150–220 discriminating cases. Delivered: 120 live + 182 differential.

**Labels:** `FINAL_V19` and `CODEX_V19_1_IF_AVAILABLE` are the same code
(`app/capabilities.py` byte-identical in Snapshots A and B). `EAC_REFERENCE` is the EAC patch.

---

## 1. Headline numbers

### Live path (120 cases, both snapshots, identical conclusions)

| Measure | Value |
|---|---|
| Cases processed | 120 / 120 OK |
| Cases where the model emitted a capability | ~103 |
| Model capabilities that survived canonicalization | **5** |
| Model capabilities silently dropped | **98** |
| Cases where the server extractor supplied a capability the model missed | **63** |
| Cases ending with at least one capability | 63 |
| Cases ending with a HARD capability | 36 |
| Cases that would block planning | **62 / 120** |
| Merged rows carrying a duplicate code | 4–5 |
| Merged rows carrying one code in two severities | 1 |

### Differential (182 cases, EAC vs FINAL_V19)

| Measure | Value |
|---|---|
| Corpus size | **182** (176 unique texts) |
| Divergent cases | **32** |
| EAC-only (FINAL_V19 missed the need) | **32** |
| FINAL_V19-only (EAC missed the need) | **0** |
| Both empty | 47 |
| HARD needs found — EAC | **71** |
| HARD needs found — FINAL_V19 | **64** |
| Duplicate codes at extractor level — EAC | 0 |
| Duplicate codes at extractor level — FINAL_V19 | 0 |
| Rows scoped `TRAVELER` — EAC | **0** |
| Rows scoped `TRAVELER` — FINAL_V19 | **0** |

EAC is a **strict superset** on this corpus: it never misses a need FINAL_V19 caught, and
recovers 32 that FINAL_V19 lost.

---

## 2. The two failure directions

The same sentence can be wrong in two ways. Both are live.

### 2.1 False erasure — a real need disappears (FINAL_V19 only)

6 of 10 clause-negation pairs erased the live need in `FINAL_V19`; **EAC fixes all 6**:

| Text | FINAL_V19 | EAC |
|---|---|---|
| `轮椅必须全程无障碍，没有例外` | `[]` | `STEP_FREE_REQUIRED` |
| `我以前不用轮椅，但现在必须无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `过去我坐轮椅，现在必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `我没有过敏，但我用轮椅，必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `不需要人扶，但我坐轮椅，必须全程无障碍` | `[]` | `STEP_FREE_REQUIRED` |
| `不是地铁，我需要出租车因为行李很多` | `[]` | `LARGE_LUGGAGE` |

Root cause in `FINAL_V19`: `_NEGATED_MARKERS` is applied **text-globally**, so a trailing
`没有例外`, a historical `以前`, or an unrelated `我没有过敏` suppresses the whole message. EAC
added `_split_clauses()` + `_extract_from_clause()`.

### 2.2 False creation — a need that does not exist (both implementations)

`_NEGATED_MARKERS` is **byte-identical** between EAC and FINAL_V19, so the manufacture
direction is untouched. Cases where **both** emit a HARD accessibility need:

| Bucket | Cases | Both emit HARD | Examples |
|---|---|---|---|
| `denial_vs_need` | 28 | **11** | `I don't need a wheelchair, I can walk fine`, `I don't use a wheelchair`, `I am not a wheelchair user`, `no stairs problem for me, I'm fine` → `AVOID_STAIRS` |
| `hearsay` | 6 | **6** | `my friend needs a wheelchair, not me`, `my mother uses a wheelchair`, `我妈妈坐轮椅`, `同事说我也许需要轮椅` |
| `hypothetical` | 3 | **3** | `if I get tired I might need a wheelchair`, `如果累了可能需要轮椅`, `maybe I should avoid stairs` |
| `provider_evidence` | 5 | **2** | `the station has an accessible toilet`, `车站有无障碍厕所` |

**The brief's two mandated sentences sit in this class:**

| Sentence | FINAL_V19 | EAC | Expected |
|---|---|---|---|
| `I don't need a wheelchair, I can walk` | `STEP_FREE_REQUIRED` HARD | `STEP_FREE_REQUIRED` HARD | no HARD need |
| `朋友说我可能需要轮椅，但我不这么认为` | `STEP_FREE_REQUIRED` HARD | `STEP_FREE_REQUIRED` HARD | no HARD need |

**~20 raw-language cases turn a denial, a third party, a hypothetical, or a description of a
venue into a HARD accessibility need about the traveller.** For this product that is the more
damaging direction: it misrepresents a person as disabled and blocks a journey they never
asked to be blocked.

---

## 3. Numeric and window extraction

| Bucket | Live (`FINAL_V19`) | Differential |
|---|---|---|
| `walking_numeric` | **16 / 20 produced nothing** | EAC recovers **16**; FINAL_V19 recovers 0 |
| `rest_nap_window` | **6 / 10 produced nothing** | EAC recovers **4**; FINAL_V19 recovers 0 |

EAC's numeric recovery is real but **unvalidated and over-extracting** —
`走路不能超过 0 米`, `走路不能超过 -5 米` and `走路不能超过 10000 米` all become HARD
`MAX_WALKING_PER_LEG_M`, and `我每天走路不能超过 3000 米` / `连续走不超过 15 分钟` each
additionally emit a spurious `MAX_WALKING_PER_LEG_M`. Full detail in
`NUMERIC_TIME_BOUNDARY_RESULTS.md` §4 and `EAC_PATCH_VALIDATION.md` §4.

---

## 4. Scope — permanent needs can never be traveller-level

`scope_permanence` bucket, 15 cases, **0 rows with `scope == "TRAVELER"` in either
implementation**:

| Text | EAC | FINAL_V19 |
|---|---|---|
| `我终身不能走楼梯，这是永久性的` | `JOURNEY` | `JOURNEY` |
| `我长期需要无障碍通道` | `JOURNEY` | `JOURNEY` |
| `I permanently need step-free access` | `JOURNEY` | `JOURNEY` |
| `我一直坐轮椅，不是这次才需要` | `JOURNEY` | `[]` |

So `D7` is **STILL_REPRODUCIBLE in both** — EAC did not fix it. The consequence measured in
the previous round stands: a TRAVELER-scoped need (only reachable via the explicit
`/travelers/{id}/capabilities/confirm` endpoint) blocks **every** future journey while
contributing **nothing** to the current journey's constraint list.

---

## 5. Loss of hardness

`hard_vs_soft` bucket: **7 of 10 live pairs lost hardness.** In the differential, EAC recovers
5 of these (`必须全程无障碍，没有例外`, `我最多走 500 米，这是硬性要求`, …) but the reverse
error appears too: `中午能休息一下就更好了` ("it would be nice to rest at noon") and
`我最多走 500 米，尽量吧` ("at most 500 m, if possible") become capabilities in EAC where
FINAL_V19 produced none — a hedged wish promoted to a `CARE_REQUIREMENT`.

---

## 6. A statement about the world becomes a need of the traveller

`无障碍` / "accessible" is a hard marker with no subject check:

| Text | Both |
|---|---|
| `the station has an accessible toilet` | `STEP_FREE_REQUIRED` |
| `车站有无障碍厕所` | `STEP_FREE_REQUIRED` |
| `the venue has a ramp` | `[]` |
| `there is an elevator at the museum` | `[]` |
| `这里有坡道` | `[]` |

Describing a **facility** as accessible is read as the **traveller** requiring step-free
access. Tag: `NEW`, present in both.

---

## 7. Verdict table

| # | Finding | `FINAL_V19` | `EAC_REFERENCE` | Tag |
|---|---|---|---|---|
| 1 | `I don't need a wheelchair, I can walk` must not be HARD | **VIOLATED** | **VIOLATED** | `FINAL_V19`, `EAC_REFERENCE` |
| 2 | `朋友说我可能需要轮椅，但我不这么认为` must not be HARD | **VIOLATED** | **VIOLATED** | `FINAL_V19`, `EAC_REFERENCE` |
| 3 | Clause-local negation must not erase a live need | **VIOLATED** (6/10) | **FIXED** | `FINAL_V19`, `EAC_REFERENCE` |
| 4 | Historical clause must not erase the current need | **VIOLATED** | **FIXED** | `FINAL_V19`, `EAC_REFERENCE` |
| 5 | Denial must not manufacture a need | **VIOLATED** (11/28) | **VIOLATED** (11/28) | `FINAL_V19`, `EAC_REFERENCE` |
| 6 | Third-party need is not the traveller's need | **VIOLATED** (6/6) | **VIOLATED** (6/6) | `FINAL_V19`, `EAC_REFERENCE` |
| 7 | Hypothetical must not become HARD | **VIOLATED** (3/3) | **VIOLATED** (3/3) | `FINAL_V19`, `EAC_REFERENCE` |
| 8 | Facility description ≠ traveller need | **VIOLATED** (2/5) | **VIOLATED** (2/5) | `NEW` |
| 9 | Walking numerics parsed | **VIOLATED** (16/20 lost) | **FIXED** (unvalidated) | `FINAL_V19`, `EAC_REFERENCE` |
| 10 | Rest / nap windows parsed | **VIOLATED** (6/10 lost) | **FIXED** | `FINAL_V19`, `EAC_REFERENCE` |
| 11 | Permanent language yields TRAVELER scope | **VIOLATED** (0/15) | **VIOLATED** (0/15) | `FINAL_V19`, `EAC_REFERENCE` |
| 12 | Model vocabulary survives canonicalization | **VIOLATED** (5/103) | not measured | `FINAL_V19` |
| 13 | Duplicate codes on the live merge path | **VIOLATED** (4–5 rows) | fixed at canonicalize | `FINAL_V19`, `EAC_REFERENCE` |

## 8. Recommendation (not applied)

Add a **subject/polarity guard** before the hard-marker check, applied per clause:

- a clause whose subject is a third party (`朋友`/`我妈妈`/`my friend`/`my mother`) or that is
  explicitly disclaimed (`我不这么认为`/`not me`) must not assert a traveller capability;
- a clause containing a denial of the need itself (`不需要轮椅`/`I don't use a wheelchair`/
  `not a wheelchair user`) must suppress that code rather than trigger it;
- a hypothetical marker (`可能`/`也许`/`if I`/`might`) must set `needs_confirmation` so the
  fact stays `STRONG` until explicitly confirmed;
- a clause whose subject is a facility (`车站有…`/`the station has…`) must not create a
  traveller capability.

Then apply `_bounded_number()` to the walking term and emit only the single most specific code
per clause.
