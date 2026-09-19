"""V19.1 semantic corpus: 120-180 HIGHEST-VALUE raw-language hard pairs.

Deliberately narrow.  The previous round ran 494 cases; this round selects only the
pairs that discriminate the seven verified delta targets plus the lifecycle items,
because those are the cases where a wrong answer changes what the product does.

Every case is raw natural language.  No pre-built SemanticEnvelope is ever supplied.

Buckets (all paired where a pair is meaningful):
  clause_negation      - the live need must survive negation elsewhere in the sentence
  denial_vs_need       - denial / hearsay / hypothetical must not manufacture a HARD need
  hard_vs_soft         - identical need, MUST phrasing vs WOULD-LIKE phrasing
  walking_numeric      - numeric walking budgets in zh / en / mixed forms
  rest_nap_window      - rest and nap windows, zh / en / mixed
  scope_permanence     - permanent (TRAVELER) vs this-trip (JOURNEY)
  duplicate_multi      - the same need stated twice, plus genuinely distinct needs
  stroller_luggage     - stroller / large luggage
  mixed_language       - one sentence, two languages

Output: evidence/semantic_cases.jsonl  (one JSON object per line)

Usage:  python tools/v191_semantic_corpus.py
"""

from __future__ import annotations

import json
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
OUT = LAB / "evidence" / "semantic_cases.jsonl"

CASES: list[dict] = []


def add(
    bucket: str,
    role: str,
    text: str,
    *,
    pair_id: str | None = None,
    topic: str | None = None,
    lang: str = "zh",
    persona: str | None = None,
    expected: str | None = None,
    why: str | None = None,
) -> None:
    CASES.append(
        {
            "id": f"{bucket}-{len(CASES) + 1:04d}",
            "bucket": bucket,
            "role": role,
            "pair_id": pair_id,
            "topic": topic,
            "lang": lang,
            "persona": persona,
            "text": text,
            "expected": expected,
            "why": why,
        }
    )


def pair(
    bucket: str,
    topic: str,
    a: tuple[str, str, str],
    b: tuple[str, str, str],
    *,
    lang: str = "zh",
    persona: str | None = None,
    why: str | None = None,
) -> None:
    """a / b = (role, text, expected)"""
    pid = f"{bucket}:{topic}"
    for role, text, expected in (a, b):
        add(
            bucket,
            role,
            text,
            pair_id=pid,
            topic=topic,
            lang=lang,
            persona=persona,
            expected=expected,
            why=why,
        )


# ===========================================================================
# 1. clause-local negation — the live need must survive a negation elsewhere
# ===========================================================================
pair(
    "clause_negation", "no_exception",
    ("live_need", "轮椅必须全程无障碍，没有例外", "STEP_FREE_REQUIRED HARD"),
    ("control", "轮椅必须全程无障碍", "STEP_FREE_REQUIRED HARD"),
    why="a trailing 没有例外 must not erase the need",
)
pair(
    "clause_negation", "no_exception_en",
    ("live_need", "wheelchair, must be step-free, no exceptions", "STEP_FREE_REQUIRED HARD"),
    ("control", "wheelchair, must be step-free", "STEP_FREE_REQUIRED HARD"),
    lang="en",
    why="English trailing negation must not erase the need",
)
pair(
    "clause_negation", "used_to_now_must",
    ("live_need", "我以前不用轮椅，但现在必须无障碍", "STEP_FREE_REQUIRED HARD"),
    ("control", "我现在必须无障碍", "STEP_FREE_REQUIRED HARD"),
    why="history clause must not suppress the present need",
)
pair(
    "clause_negation", "past_wheelchair_now_must",
    ("live_need", "过去我坐轮椅，现在必须全程无障碍", "STEP_FREE_REQUIRED HARD"),
    ("control", "现在必须全程无障碍", "STEP_FREE_REQUIRED HARD"),
    why="past-tense clause must not suppress the present need",
)
pair(
    "clause_negation", "no_allergy_but_wheelchair",
    ("live_need", "我没有过敏，但我用轮椅，必须全程无障碍", "STEP_FREE_REQUIRED HARD"),
    ("control", "我用轮椅，必须全程无障碍", "STEP_FREE_REQUIRED HARD"),
    why="an unrelated negation must not erase the accessibility need",
)
pair(
    "clause_negation", "not_metro_but_luggage",
    ("live_need", "不是地铁，我需要出租车因为行李很多", "LARGE_LUGGAGE"),
    ("control", "我需要出租车因为行李很多", "LARGE_LUGGAGE"),
    why="negating the transport mode must not drop the luggage need",
)
pair(
    "clause_negation", "dont_like_heat_but_stroller",
    ("live_need", "我不怕晒，但推着婴儿车，需要无障碍通道", "STROLLER"),
    ("control", "推着婴儿车，需要无障碍通道", "STROLLER"),
    why="unrelated negation must not drop the stroller need",
)
pair(
    "clause_negation", "no_meat_but_nap",
    ("live_need", "我们不吃肉，但宝宝下午一点必须睡午觉", "INFANT_NAP_WINDOW"),
    ("control", "宝宝下午一点必须睡午觉", "INFANT_NAP_WINDOW"),
    why="dietary negation must not drop the nap window",
)
pair(
    "clause_negation", "never_used_lift_but_stairs",
    ("live_need", "我从来不坐电梯，只能走楼梯，但其实我走不了楼梯", "AVOID_STAIRS"),
    ("control", "我走不了楼梯", "AVOID_STAIRS"),
    why="a double negative about lifts must not cancel the stair avoidance",
)
pair(
    "clause_negation", "no_help_needed_but_wheelchair",
    ("live_need", "不需要人扶，但我坐轮椅，必须全程无障碍", "STEP_FREE_REQUIRED HARD"),
    ("control", "我坐轮椅，必须全程无障碍", "STEP_FREE_REQUIRED HARD"),
    why="negating assistance must not erase the wheelchair need",
)

# ===========================================================================
# 2. denial / hearsay / hypothetical must NOT manufacture a HARD need
# ===========================================================================
pair(
    "denial_vs_need", "dont_need_wheelchair",
    ("must_not_create", "I don't need a wheelchair, I can walk fine", "no HARD capability"),
    ("control", "I need a wheelchair, I cannot walk", "STEP_FREE_REQUIRED HARD"),
    lang="en",
    why="explicit denial must not create a HARD accessibility need",
)
pair(
    "denial_vs_need", "friend_said_maybe",
    ("must_not_create", "朋友说我可能需要轮椅，但我不这么认为", "no HARD capability"),
    ("control", "我需要轮椅", "STEP_FREE_REQUIRED HARD"),
    why="hearsay must not create a HARD need",
)
pair(
    "denial_vs_need", "maybe_wheelchair",
    ("must_not_create", "说不定到时候我需要轮椅", "no HARD capability"),
    ("control", "我需要轮椅", "STEP_FREE_REQUIRED HARD"),
    why="speculation must not create a HARD need",
)
pair(
    "denial_vs_need", "if_wheelchair_then_tell",
    ("must_not_create", "if I end up in a wheelchair I'll tell you", "no HARD capability"),
    ("control", "I am in a wheelchair", "STEP_FREE_REQUIRED HARD"),
    lang="en",
    why="conditional future must not create a HARD need",
)
pair(
    "denial_vs_need", "no_stroller_this_time",
    ("must_not_create", "no stroller this time, ignore that", "no HARD capability"),
    ("control", "we have a stroller this time", "STROLLER"),
    lang="en",
    why="explicit cancellation must not leave a live stroller need",
)
pair(
    "denial_vs_need", "not_pregnant",
    ("must_not_create", "我没有怀孕，只是有点累", "no HARD capability"),
    ("control", "我怀孕了，需要多休息", "rest need"),
    why="denial must not create a medical need",
)
pair(
    "denial_vs_need", "no_luggage",
    ("must_not_create", "这次没带大箱子，轻装", "no LARGE_LUGGAGE"),
    ("control", "带了一个大箱子", "LARGE_LUGGAGE"),
    why="denial of luggage must not create a luggage need",
)
pair(
    "denial_vs_need", "cant_walk_long_but_fine",
    ("must_not_create", "I can't walk long distances, but honestly I'm fine", "ambiguous, must not silently HARD"),
    ("control", "I can't walk long distances", "walking limit"),
    lang="en",
    why="self-contradiction must surface, not silently pick HARD",
)
pair(
    "denial_vs_need", "grandma_hypothetical",
    ("must_not_create", "如果我奶奶来，她可能走不了路", "no HARD capability for this traveller"),
    ("control", "我奶奶走不了路", "walking limit for companion"),
    why="hypothetical companion must not create a live need",
)
pair(
    "denial_vs_need", "doctor_didnt_say",
    ("must_not_create", "医生没说我不能走路", "no HARD capability"),
    ("control", "医生说我不能走路", "HARD walking limit"),
    why="negated medical authority must not create a HARD need",
)

# ===========================================================================
# 3. hard vs soft phrasing — identical need, different modality
# ===========================================================================
pair(
    "hard_vs_soft", "wheelchair",
    ("hard", "我坐轮椅，必须全程无障碍", "HARD"),
    ("soft", "我坐轮椅，最好全程无障碍", "SOFT/STRONG, never HARD"),
    why="only the MUST form may become HARD",
)
pair(
    "hard_vs_soft", "walking",
    ("hard", "我最多走 500 米，这是硬性要求", "HARD walking limit"),
    ("soft", "我最多走 500 米，尽量吧", "SOFT walking limit"),
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "stairs",
    ("hard", "绝对不能走楼梯", "AVOID_STAIRS HARD"),
    ("soft", "尽量少走楼梯", "AVOID_STAIRS SOFT"),
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "rest",
    ("hard", "中午 12 点到 14 点必须回酒店休息", "HARD rest window"),
    ("soft", "中午能休息一下就更好了", "SOFT rest window"),
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "nap",
    ("hard", "宝宝下午 1 点到 3 点必须睡午觉", "HARD nap window"),
    ("soft", "宝宝下午要是能睡一会儿就好了", "SOFT nap window"),
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "stroller",
    ("hard", "必须能推婴儿车，不然不行", "STROLLER HARD"),
    ("soft", "如果能推婴儿车就方便多了", "STROLLER SOFT"),
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "luggage_en",
    ("hard", "we must avoid stairs, we have two large suitcases", "LARGE_LUGGAGE + AVOID_STAIRS"),
    ("soft", "it would be nice to avoid stairs with our suitcases", "SOFT only"),
    lang="en",
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "toilet",
    ("hard", "每小时必须上一次厕所", "TOILET_BREAK_EVERY_MIN HARD"),
    ("soft", "希望每小时能上个厕所", "SOFT"),
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "sensory",
    ("hard", "必须有安静的空间，我不能待在嘈杂的地方", "HARD quiet/sensory"),
    ("soft", "安静一点会更好", "SOFT"),
    why="modality must decide severity",
)
pair(
    "hard_vs_soft", "elderly",
    ("hard", "我父亲 80 岁，走不了远路，必须少走路", "HARD walking limit"),
    ("soft", "我父亲 80 岁，走远路会累", "SOFT walking limit"),
    why="modality must decide severity",
)

# ===========================================================================
# 4. walking numeric forms
# ===========================================================================
for text, expected in [
    ("走路不能超过 500 米", "max_m=500 HARD"),
    ("走路不能超过 0 米", "max_m=0 or rejected, never silent"),
    ("走路不能超过 1 米", "max_m=1"),
    ("走路不能超过 499 米", "max_m=499"),
    ("走路不能超过 501 米", "max_m=501"),
    ("走路不能超过 1000 米", "max_m=1000"),
    ("走路不能超过 10000 米", "max_m=10000"),
    ("走路不能超过 -5 米", "rejected, not silently accepted"),
    ("我最多走 500 米", "max_m=500"),
    ("走路不能超过 500m，这是硬性要求", "max_m=500 HARD"),
    ("每段不超过 500 米", "max_m=500 per leg"),
    ("I cannot walk more than 500 metres per leg", "max_m=500"),
    ("avoid long walks, under 400 m per leg", "max_m=400"),
    ("我每天走路不能超过 3000 米", "max_m=3000 daily"),
    ("走 0.5 公里就不行了", "max_m=500"),
    ("走 1 公里就不行了", "max_m=1000"),
    ("连续走不能超过 20 分钟", "max_min=20 continuous"),
    ("我走五分钟就得歇一下", "max_min=5 continuous"),
    ("walking limit 500 m, no negotiation", "max_m=500 HARD"),
    ("我走路不能超过 五百 米", "Chinese numeral 500"),
]:
    add(
        "walking_numeric",
        "single",
        text,
        topic="walking",
        lang="en" if text.isascii() else "zh",
        expected=expected,
        why="numeric walking budget must reach the gate as a number",
    )

# ===========================================================================
# 5. rest / nap windows
# ===========================================================================
for text, expected in [
    ("中午 12 点到 14 点必须回酒店休息", "MIDDAY_REST_WINDOW 12:00-14:00 HARD"),
    ("中午 12:00-14:00 必须回酒店休息", "MIDDAY_REST_WINDOW 12:00-14:00 HARD"),
    ("宝宝下午 1 点到 3 点必须睡午觉", "INFANT_NAP_WINDOW 13:00-15:00"),
    ("I must rest at the hotel between 12:00 and 14:00", "MIDDAY_REST_WINDOW 12:00-14:00"),
    ("rest from 1pm to 3pm", "window 13:00-15:00"),
    ("the baby needs naptime at 13:00-15:00", "INFANT_NAP_WINDOW 13:00-15:00"),
    ("老人中午必须休息两小时", "rest window, duration 120 min"),
    ("午休从 13 点开始", "window with only a start"),
    ("我中午要午睡", "MIDDAY_REST_WINDOW default"),
    ("nap time is 2pm", "nap window default/2pm"),
]:
    add(
        "rest_nap_window",
        "single",
        text,
        topic="rest",
        lang="en" if text.isascii() else "zh",
        expected=expected,
        why="time windows must reach the gate as start/end",
    )

# ===========================================================================
# 6. scope / permanence
# ===========================================================================
pair(
    "scope_permanence", "wheelchair",
    ("traveler", "我终身不能走楼梯，这是永久性的", "TRAVELER scope"),
    ("journey", "这次旅行我走不了太多路", "JOURNEY scope"),
    why="permanent needs belong to the traveller, not one trip",
)
pair(
    "scope_permanence", "allergy",
    ("traveler", "我对花生过敏，一辈子都是", "TRAVELER scope"),
    ("journey", "这次行程中我尽量不吃花生", "JOURNEY scope"),
    why="permanent needs belong to the traveller",
)
pair(
    "scope_permanence", "injury",
    ("traveler", "我的腿伤是长期的", "TRAVELER scope"),
    ("journey", "我上周崴了脚，这趟先少走路", "JOURNEY scope"),
    why="temporary injuries belong to one trip",
)
pair(
    "scope_permanence", "luggage",
    ("traveler", "我每次出行都带大箱子", "TRAVELER habit"),
    ("journey", "这次我带了一个大箱子", "JOURNEY scope"),
    why="a habit is traveller-level, an instance is journey-level",
)
pair(
    "scope_permanence", "pregnancy",
    ("traveler", "我怀孕 7 个月了", "TRAVELER scope"),
    ("journey", "这趟旅行我容易累", "JOURNEY scope"),
    why="a body state outlives one trip",
)

# ===========================================================================
# 7. duplicates and genuinely distinct needs
# ===========================================================================
pair(
    "duplicate_multi", "same_twice",
    ("duplicate", "我坐轮椅，必须无障碍。再说一次，我需要无障碍通道", "one code, strongest severity"),
    ("control", "我坐轮椅，必须无障碍", "one code"),
    why="the same need twice must not create two rows",
)
pair(
    "duplicate_multi", "mixed_severity",
    ("duplicate", "必须无障碍，其实无障碍就好", "one code, HARD wins, never both"),
    ("control", "必须无障碍", "one code HARD"),
    why="one need cannot be both HARD and SOFT",
)
pair(
    "duplicate_multi", "distinct",
    ("multi", "我坐轮椅，而且不能走楼梯，还要每小时上厕所", "three distinct codes"),
    ("control", "我坐轮椅", "one code"),
    why="genuinely distinct needs must all survive",
)
pair(
    "duplicate_multi", "multi_elderly",
    ("multi", "我父亲走不了远路，我妈妈要午休，宝宝要睡午觉", "three distinct codes"),
    ("control", "我父亲走不了远路", "one code"),
    why="a family's distinct needs must all survive",
)

# ===========================================================================
# 8. stroller / luggage
# ===========================================================================
for text, expected in [
    ("我推着婴儿车，需要无障碍通道", "STROLLER"),
    ("stroller, need lifts everywhere", "STROLLER"),
    ("带两个大箱子，不能走楼梯", "LARGE_LUGGAGE + AVOID_STAIRS"),
    ("two large suitcases, need luggage storage", "LARGE_LUGGAGE"),
    ("婴儿车 + 大箱子，都要能放", "STROLLER + LARGE_LUGGAGE"),
    ("we have a buggy and a suitcase", "STROLLER + LARGE_LUGGAGE"),
]:
    add(
        "stroller_luggage",
        "single",
        text,
        topic="gear",
        lang="en" if text.isascii() else "zh",
        expected=expected,
        why="gear needs must be extracted and must not silently pass the gate",
    )

# ===========================================================================
# 9. mixed language in one sentence
# ===========================================================================
for text, expected in [
    ("我妈妈 wheelchair，必须 step-free", "STEP_FREE_REQUIRED HARD"),
    ("宝宝需要 nap，下午 1 点到 3 点", "INFANT_NAP_WINDOW"),
    ("my 爸爸 cannot walk 太久", "walking limit"),
    ("轮椅 wheelchair 全程 accessible", "STEP_FREE_REQUIRED"),
    ("大箱子 large luggage 不能走楼梯", "LARGE_LUGGAGE + AVOID_STAIRS"),
    ("stroller 婴儿车 需要 elevator", "STROLLER"),
]:
    add(
        "mixed_language",
        "single",
        text,
        topic="mixed",
        lang="mixed",
        expected=expected,
        why="code-switching must not defeat extraction",
    )


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        for case in CASES:
            handle.write(json.dumps(case, ensure_ascii=False) + "\n")

    buckets: dict[str, int] = {}
    pairs: dict[str, int] = {}
    for case in CASES:
        buckets[case["bucket"]] = buckets.get(case["bucket"], 0) + 1
        if case["pair_id"]:
            pairs[case["pair_id"]] = pairs.get(case["pair_id"], 0) + 1

    print(f"cases={len(CASES)}  unique_text={len({c['text'] for c in CASES})}")
    print(f"pairs={len(pairs)}  langs={ {c['lang'] for c in CASES} }")
    for name, count in sorted(buckets.items()):
        print(f"  {name:<20} {count}")
    print(f"written -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
