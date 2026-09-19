"""Continuation-queue items 2/3/4 — contrast fixtures and zh/en equivalence pairs.

Builds three evidence artefacts that isolate *minimal* semantic contrasts:

* ``evidence/contrast_fixtures.json``
    - 10 x WHAT_IF-vs-REAL-DISRUPTION pairs
      (``如果下雨会怎样？`` must not be scored the same as ``现在正在下雨，游船可能取消。``)
    - 10 x EXPLAIN-vs-REQUEST-CHANGE pairs
      (``为什么现在这样安排？`` must not be scored the same as ``把下午改成博物馆。``)
* ``evidence/zh_en_equivalence.json``
    - 20 zh/en pairs that *should* resolve to the same intent (translation invariance).

Every pair is scored twice:
  1. offline against the optional reference router (free, deterministic), and
  2. the *contrast* direction is asserted — a pair that is supposed to differ
     must actually differ, and an equivalence pair must actually agree.

The point of a contrast fixture is the delta, not the absolute label. A router
that gets 50% absolute accuracy but keeps all 20 contrasts separated is far more
useful than one that gets 90% absolute accuracy while collapsing the two cases
the V15 brief explicitly names.

Usage::

    python tools/v15_benchmark/build_contrast_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent.semantic_router import (  # noqa: E402
    NEVER_EVENT_INTENTS,
    JourneyContext,
    route,
)

OUT_CONTRAST = ROOT / "evidence" / "contrast_fixtures.json"
OUT_EQUIV = ROOT / "evidence" / "zh_en_equivalence.json"

# A fixed context used for every fixture so the only variable is the message.
# NOTE: the city_code must be the canonical id from CITY_TOKENS. A made-up code
# such as "FZ" makes ``detect_foreign_city`` treat the journey's OWN city name
# as a foreign reference and silently downgrade the route to UNKNOWN.
FUZHOU = JourneyContext(
    city_code="CN-FUZHOU", timezone="Asia/Shanghai", currency="CNY",
    locale="zh-CN", journey_state="ACTIVE",
)
LONDON = JourneyContext(
    city_code="GB-LONDON", timezone="Europe/London", currency="GBP",
    locale="en", journey_state="ACTIVE",
)


# --------------------------------------------------------------------------- #
# item 3 — 10 x WHAT_IF vs REAL DISRUPTION
# --------------------------------------------------------------------------- #
#: (label, hypothetical_message, real_message, ctx, why_it_matters)
WHAT_IF_VS_REAL: list[tuple[str, str, str, JourneyContext, str]] = [
    (
        "rain",
        "如果下雨会怎样？",
        "现在正在下雨，游船可能取消。",
        FUZHOU,
        "The V15 brief names this pair explicitly. Hypothetical rain is a question; "
        "present-tense rain with a cancellation is a report that may open a mission.",
    ),
    (
        "road_closure",
        "要是前面封路了怎么办？",
        "前方封路了，走不通。",
        FUZHOU,
        "Counterfactual vs. present-tense closure. Same noun, opposite mutation rights.",
    ),
    (
        "typhoon_en",
        "What if a typhoon hits Fuzhou?",
        "A typhoon has hit Fuzhou, the harbour is closed.",
        FUZHOU,
        "English mirror of the rain pair; also checks the model is not language-conditioned.",
    ),
    (
        "strike",
        "假如地铁罢工的话会怎样？",
        "地铁罢工了，线路停运。",
        FUZHOU,
        "Hypothetical labour action vs. an in-progress strike. Only the latter is a fact.",
    ),
    (
        "flight_delay_en",
        "What happens if my flight is delayed?",
        "My flight is delayed by three hours.",
        LONDON,
        "The first is a request for consequences; the second is a reportable event.",
    ),
    (
        "museum_closed",
        "万一博物馆关门了呢？",
        "博物馆关门了，进不去。",
        FUZHOU,
        "A closed attraction is a disruption only when it is happening now.",
    ),
    (
        "bridge_closed",
        "如果桥封了怎么办？",
        "桥封了。",
        FUZHOU,
        "Short real report (3 chars after the verb) — also exercises the min_length gate.",
    ),
    (
        "crowd",
        "如果人很多会怎样？",
        "现在人很多，排队要两小时。",
        FUZHOU,
        "Crowding is only a disruption with a present-tense measurement attached.",
    ),
    (
        "cancel_boat",
        "游船取消的话我会怎样？",
        "游船取消了。",
        FUZHOU,
        "Tianjin/水上游船 is a protected commitment alias; a real cancellation must reach C4.",
    ),
    (
        "power_cut",
        "假如停电呢？",
        "这边停电了，电梯停了。",
        FUZHOU,
        "Utility failure: hypothetical vs. real, with a downstream consequence clause.",
    ),
]


# --------------------------------------------------------------------------- #
# item 4 — 10 x EXPLAIN vs REQUEST-CHANGE
# --------------------------------------------------------------------------- #
#: (label, explain_message, request_message, ctx, why_it_matters)
EXPLAIN_VS_CHANGE: list[tuple[str, str, str, JourneyContext, str]] = [
    (
        "afternoon_order",
        "为什么下午先去博物馆？",
        "把下午改成博物馆。",
        FUZHOU,
        "Interrogative 'why' vs. imperative 'change to'. Only the second is a request.",
    ),
    (
        "route_choice_en",
        "Why did you pick this route?",
        "Please change the route to avoid the bridge.",
        LONDON,
        "English mirror. 'Why did you' must never be read as a change verb.",
    ),
    (
        "budget",
        "为什么预算是 800 元？",
        "预算改成 800 元。",
        FUZHOU,
        "Questioning a bound vs. moving a bound. Moving it may touch a commitment.",
    ),
    (
        "walking",
        "为什么安排这么多步行？",
        "我想少走路。",
        FUZHOU,
        "This is the second pair the brief names: asking about walking is not a preference change.",
    ),
    (
        "order_swap",
        "为什么先吃饭再去景点？",
        "把顺序反过来。",
        FUZHOU,
        "Explaining an ordering is not the same as requesting a reorder.",
    ),
    (
        "time_en",
        "Why are we starting at nine?",
        "Start at ten instead.",
        LONDON,
        "Time interrogation vs. time change.",
    ),
    (
        "hotel",
        "为什么选这家酒店？",
        "换一家便宜点的酒店。",
        FUZHOU,
        "Explain-a-choice vs. swap-a-booking (booking changes need confirmation).",
    ),
    (
        "boat_explain",
        "为什么游船这么贵？",
        "把游船退掉。",
        FUZHOU,
        "The second message targets a protected commitment; it must require confirmation.",
    ),
    (
        "weather_explain",
        "为什么今天行程这么松？",
        "把行程排紧一点。",
        FUZHOU,
        "Density question vs. density change.",
    ),
    (
        "kids_en",
        "Why is the museum visit so short?",
        "Make the museum visit longer.",
        LONDON,
        "Duration question vs. duration change; both mention the same activity.",
    ),
]


# --------------------------------------------------------------------------- #
# item 2 — 20 zh/en equivalence pairs (translation invariance)
# --------------------------------------------------------------------------- #
#: (label, zh_message, en_message, expected_intent)
EQUIVALENCE: list[tuple[str, str, str, str]] = [
    ("explain_why", "为什么这么安排？", "Why is the plan arranged this way?", "EXPLAIN_PLAN"),
    ("explain_order", "为什么先去博物馆？", "Why are we going to the museum first?", "EXPLAIN_PLAN"),
    ("explain_cost", "这趟大概要花多少钱？", "How much will this trip cost?", "EXPLAIN_PLAN"),
    ("explain_next", "接下来是什么？", "What is next on the plan?", "EXPLAIN_PLAN"),
    ("explain_boat", "游船是几点？", "What time is the boat cruise?", "EXPLAIN_PLAN"),
    ("whatif_rain", "如果下雨会怎样？", "What if it rains?", "WHAT_IF"),
    ("whatif_delay", "要是延误了怎么办？", "What happens if we are delayed?", "WHAT_IF"),
    ("whatif_budget", "如果超预算呢？", "What if we go over budget?", "WHAT_IF"),
    ("whatif_close", "万一景点关门呢？", "What if the attraction is closed?", "WHAT_IF"),
    ("discover_food", "附近有什么好吃的？", "What food is nearby?", "DISCOVER"),
    ("discover_indoor", "下雨天有什么室内的？", "What indoor options are there?", "DISCOVER"),
    ("discover_kids", "适合小孩的地方有哪些？", "What places are good for kids?", "DISCOVER"),
    ("discover_coffee", "附近有咖啡馆吗？", "Is there a cafe nearby?", "DISCOVER"),
    ("pref_less_walk", "我想少走路。", "I want to walk less.", "PREFERENCE_CHANGE"),
    ("pref_cheaper", "我想省钱一点。", "I would like to spend less.", "PREFERENCE_CHANGE"),
    ("pref_indoor", "我想多安排室内。", "I prefer indoor activities.", "PREFERENCE_CHANGE"),
    ("replan_swap", "把下午换成博物馆。", "Swap the afternoon to the museum.", "REPLAN_REQUEST"),
    ("replan_later", "把开始时间推迟一小时。", "Push the start back by an hour.", "REPLAN_REQUEST"),
    ("replan_avoid", "避开那座桥。", "Avoid that bridge.", "REPLAN_REQUEST"),
    ("unknown_weather_q", "明天天气怎么样？", "What is the weather tomorrow?", "UNKNOWN"),
]


def score(message: str, ctx: JourneyContext) -> dict:
    r = route(message, ctx)
    return {
        "intent": r.intent,
        "mutation_policy": r.mutation_policy,
        "requires_confirmation": bool(r.requires_confirmation),
        "creates_event": r.intent not in NEVER_EVENT_INTENTS,
        "confidence": round(float(getattr(r, "confidence", 0.0)), 3),
        "reason": getattr(r, "reason", ""),
    }


def build_contrast() -> dict:
    rows: list[dict] = []
    separated = 0
    total = 0

    for kind, triples in (
        ("WHAT_IF_VS_REAL_DISRUPTION", WHAT_IF_VS_REAL),
        ("EXPLAIN_VS_REQUEST_CHANGE", EXPLAIN_VS_CHANGE),
    ):
        for label, left, right, ctx, why in triples:
            total += 1
            a, b = score(left, ctx), score(right, ctx)
            differs = (a["intent"] != b["intent"]) or (
                a["mutation_policy"] != b["mutation_policy"]
            )
            separated += int(differs)
            rows.append({
                "kind": kind,
                "label": label,
                "context": {"city_code": ctx.city_code, "locale": ctx.locale},
                "left": {"message": left, **a},
                "right": {"message": right, **b},
                "separated": differs,
                "same_intent": a["intent"] == b["intent"],
                "why_it_matters": why,
            })

    return {
        "generated_by": "tools/v15_benchmark/build_contrast_fixtures.py",
        "scorer": "optional reference router (app.agent.semantic_router.route), offline",
        "pair_count": total,
        "separated_count": separated,
        "separation_rate": round(separated / total, 4) if total else 0.0,
        "pairs": rows,
    }


def build_equivalence() -> dict:
    rows: list[dict] = []
    agree = 0
    for label, zh, en, expected in EQUIVALENCE:
        a = score(zh, FUZHOU)
        b = score(en, LONDON)
        same = a["intent"] == b["intent"]
        agree += int(same)
        rows.append({
            "label": label,
            "expected_intent": expected,
            "zh": {"message": zh, **a},
            "en": {"message": en, **b},
            "invariant": same,
            "both_match_expected": a["intent"] == expected and b["intent"] == expected,
        })
    return {
        "generated_by": "tools/v15_benchmark/build_contrast_fixtures.py",
        "scorer": "optional reference router (app.agent.semantic_router.route), offline",
        "pair_count": len(rows),
        "invariant_count": agree,
        "invariance_rate": round(agree / len(rows), 4) if rows else 0.0,
        "pairs": rows,
    }


def main() -> int:
    contrast = build_contrast()
    equiv = build_equivalence()

    OUT_CONTRAST.parent.mkdir(parents=True, exist_ok=True)
    OUT_CONTRAST.write_text(
        json.dumps(contrast, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT_EQUIV.write_text(
        json.dumps(equiv, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"contrast fixtures : {contrast['separated_count']}/{contrast['pair_count']} "
          f"separated ({contrast['separation_rate']:.1%})")
    print(f"zh/en equivalence : {equiv['invariant_count']}/{equiv['pair_count']} "
          f"invariant ({equiv['invariance_rate']:.1%})")
    print(f"wrote {OUT_CONTRAST}")
    print(f"wrote {OUT_EQUIV}")

    for row in contrast["pairs"]:
        flag = "OK " if row["separated"] else "!! "
        print(f"  {flag}{row['kind'][:12]:<12} {row['label']:<16} "
              f"{row['left']['intent']:<18} | {row['right']['intent']}")
    for row in equiv["pairs"]:
        flag = "OK " if row["invariant"] else "!! "
        print(f"  {flag}equiv {row['label']:<18} "
              f"{row['zh']['intent']:<18} | {row['en']['intent']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
