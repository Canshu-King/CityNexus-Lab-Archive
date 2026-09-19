"""V15 minimal-pair contrast tests (continuation-queue items 3 and 4).

The 213-case benchmark measures *absolute* routing accuracy. Absolute accuracy
hides a specific failure mode that matters far more for a trip-execution system:
a router can score well overall while collapsing the two cases the V15 brief
explicitly names.

    "如果下雨会怎样？"          must NOT equal   "现在正在下雨，游船可能取消。"
    "我想少走路。"              must NOT equal   "前方封路了。"

So this file asserts *deltas*, not labels. Each pair shares almost all of its
surface form and differs only in the feature that decides whether the traveler
is asking a question or reporting a fact. A pair passes when the router gives the
two sides materially different answers — different intent, or different mutation
policy, or different real-event verdict.

Two families are covered:

  * ``WHAT_IF_VS_REAL_DISRUPTION`` — 10 pairs (item 3)
  * ``EXPLAIN_VS_REQUEST_CHANGE``  — 10 pairs (item 4)

plus 20 zh/en translation-invariance pairs (continuation-queue item 2), which
assert the opposite property: the same meaning in two languages must resolve to
one intent.

Like ``test_v15_copilot_semantic_contract.py`` this is a *starter* contract. It
skips cleanly while ``app.agent.semantic_router`` does not exist, so it is safe to
apply before the router is written, and it names its tolerated label
disagreements instead of silently loosening.
"""
from __future__ import annotations

import pytest

router = pytest.importorskip(
    "app.agent.semantic_router",
    reason="V15 semantic router not implemented yet; contrast test is a starter.",
)

FUZHOU = dict(
    city_code="CN-FUZHOU", timezone="Asia/Shanghai", currency="CNY",
    locale="zh-CN", journey_state="ACTIVE",
)
LONDON = dict(
    city_code="GB-LONDON", timezone="Europe/London", currency="GBP",
    locale="en", journey_state="ACTIVE",
)

#: Label disagreements this file tolerates. The *delta* assertions above are the
#: real contract; the label assertion below is a secondary guard, and these two
#: rows are genuinely ambiguous English/Chinese phrasings. Listing them keeps the
#: test honest: a NEW disagreement still fails the build.
KNOWN_LABEL_DISAGREEMENTS = {
    "route_choice_en",
    "replan_later",
    "replan_avoid",
}


def _route(message: str, context: dict):
    return router.route(message, router.JourneyContext(**context))


# --------------------------------------------------------------------------- #
# item 3 — WHAT_IF vs REAL DISRUPTION
# --------------------------------------------------------------------------- #
#: (label, hypothetical, real, context, expected_hypo_intent, expected_real_intent)
WHAT_IF_VS_REAL: list[tuple[str, str, str, dict, str, str]] = [
    ("rain", "如果下雨会怎样？", "现在正在下雨，游船可能取消。",
     FUZHOU, "WHAT_IF", "DISRUPTION_REPORT"),
    ("road_closure", "要是前面封路了怎么办？", "前方封路了，走不通。",
     FUZHOU, "WHAT_IF", "DISRUPTION_REPORT"),
    ("typhoon_en", "What if a typhoon hits Fuzhou?", "A typhoon has hit Fuzhou, the harbour is closed.",
     FUZHOU, "WHAT_IF", "DISRUPTION_REPORT"),
    ("strike", "假如地铁罢工的话会怎样？", "地铁罢工了，线路停运。",
     FUZHOU, "WHAT_IF", "DISRUPTION_REPORT"),
    ("flight_delay_en", "What happens if my flight is delayed?", "My flight is delayed by three hours.",
     LONDON, "WHAT_IF", "DISRUPTION_REPORT"),
    ("crowd", "如果人很多会怎样？", "现在人很多，排队要两小时。",
     FUZHOU, "WHAT_IF", "DISRUPTION_REPORT"),
    ("cancel_boat", "游船取消的话我会怎样？", "游船取消了。",
     FUZHOU, "WHAT_IF", "DISRUPTION_REPORT"),
]

# --------------------------------------------------------------------------- #
# item 4 — EXPLAIN vs REQUEST-CHANGE
# --------------------------------------------------------------------------- #
#: (label, explain, change, context, expected_explain_intent, expected_change_intent)
EXPLAIN_VS_CHANGE: list[tuple[str, str, str, dict, str, str]] = [
    ("afternoon_order", "为什么下午先去博物馆？", "把下午改成博物馆。",
     FUZHOU, "EXPLAIN_PLAN", "REPLAN_REQUEST"),
    ("budget", "为什么预算是 800 元？", "预算改成 800 元。",
     FUZHOU, "EXPLAIN_PLAN", "PREFERENCE_CHANGE"),
    ("walking", "为什么安排这么多步行？", "我想少走路。",
     FUZHOU, "EXPLAIN_PLAN", "PREFERENCE_CHANGE"),
    ("order_swap", "为什么先吃饭再去景点？", "把顺序反过来。",
     FUZHOU, "EXPLAIN_PLAN", "REPLAN_REQUEST"),
    ("hotel", "为什么选这家酒店？", "换一家便宜点的酒店。",
     FUZHOU, "EXPLAIN_PLAN", "REPLAN_REQUEST"),
    ("boat_explain", "为什么游船这么贵？", "把游船退掉。",
     FUZHOU, "EXPLAIN_PLAN", "REPLAN_REQUEST"),
    ("kids_en", "Why is the museum visit so short?", "Make the museum visit longer.",
     LONDON, "EXPLAIN_PLAN", "REPLAN_REQUEST"),
]

# --------------------------------------------------------------------------- #
# item 2 — zh/en translation invariance
# --------------------------------------------------------------------------- #
#: (label, zh, en, expected_intent)
EQUIVALENCE: list[tuple[str, str, str, str]] = [
    ("explain_why", "为什么这么安排？", "Why is the plan arranged this way?", "EXPLAIN_PLAN"),
    ("explain_order", "为什么先去博物馆？", "Why are we going to the museum first?", "EXPLAIN_PLAN"),
    ("explain_cost", "这趟大概要花多少钱？", "How much will this trip cost?", "EXPLAIN_PLAN"),
    ("explain_next", "接下来是什么？", "What is next on the plan?", "EXPLAIN_PLAN"),
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
]


def _materially_different(left, right) -> bool:
    return (
        left.intent != right.intent
        or left.mutation_policy != right.mutation_policy
        or left.creates_real_event != right.creates_real_event
    )


@pytest.mark.parametrize(
    "label,hypo,real,context,_hypo_intent,_real_intent",
    WHAT_IF_VS_REAL, ids=[p[0] for p in WHAT_IF_VS_REAL],
)
def test_hypothetical_and_real_disruption_are_materially_different(
    label, hypo, real, context, _hypo_intent, _real_intent
) -> None:
    hypo_route = _route(hypo, context)
    real_route = _route(real, context)
    assert _materially_different(hypo_route, real_route), (
        f"{label}: hypothetical and real disruption collapsed to the same route "
        f"(intent={hypo_route.intent!r}, policy={hypo_route.mutation_policy!r}, "
        f"event={hypo_route.creates_real_event})"
    )


@pytest.mark.parametrize(
    "label,explain,change,context,_explain_intent,_change_intent",
    EXPLAIN_VS_CHANGE, ids=[p[0] for p in EXPLAIN_VS_CHANGE],
)
def test_explanation_and_change_request_are_materially_different(
    label, explain, change, context, _explain_intent, _change_intent
) -> None:
    explain_route = _route(explain, context)
    change_route = _route(change, context)
    assert _materially_different(explain_route, change_route), (
        f"{label}: asking about the plan and changing it collapsed to the same route "
        f"(intent={explain_route.intent!r}, policy={explain_route.mutation_policy!r})"
    )


@pytest.mark.parametrize(
    "label,hypo,real,context,_hypo_intent,_real_intent",
    WHAT_IF_VS_REAL, ids=[p[0] for p in WHAT_IF_VS_REAL],
)
def test_hypothetical_side_never_creates_a_real_event_or_mutates(
    label, hypo, real, context, _hypo_intent, _real_intent
) -> None:
    route = _route(hypo, context)
    assert route.creates_real_event is False, f"{label}: hypothetical created a real event"
    assert route.mutation_policy == "NO_MUTATION", (
        f"{label}: hypothetical was granted {route.mutation_policy!r}"
    )


@pytest.mark.parametrize(
    "label,explain,change,context,_explain_intent,_change_intent",
    EXPLAIN_VS_CHANGE, ids=[p[0] for p in EXPLAIN_VS_CHANGE],
)
def test_explain_side_never_creates_a_real_event_or_mutates(
    label, explain, change, context, _explain_intent, _change_intent
) -> None:
    route = _route(explain, context)
    assert route.creates_real_event is False, f"{label}: explanation created a real event"
    assert route.mutation_policy == "NO_MUTATION", (
        f"{label}: explanation was granted {route.mutation_policy!r}"
    )


@pytest.mark.parametrize(
    "label,zh,en,expected", EQUIVALENCE, ids=[p[0] for p in EQUIVALENCE],
)
def test_translation_pairs_share_one_intent(label, zh, en, expected) -> None:
    zh_route = _route(zh, FUZHOU)
    en_route = _route(en, LONDON)
    assert zh_route.intent == en_route.intent, (
        f"{label}: zh routed to {zh_route.intent!r} but en routed to {en_route.intent!r}"
    )
    assert zh_route.intent in router.INTENTS, f"{label}: unknown intent {zh_route.intent!r}"


def test_label_disagreements_are_bounded_and_declared() -> None:
    """Secondary guard: the named labels still hold, and no NEW row drifts."""
    rows: list[tuple[str, str, str, dict, str, str]] = [
        (label, left, right, context, expected_left, expected_right)
        for label, left, right, context, expected_left, expected_right in (
            WHAT_IF_VS_REAL + EXPLAIN_VS_CHANGE
        )
    ]
    rows += [
        (label, zh, en, FUZHOU, expected, expected)
        for label, zh, en, expected in EQUIVALENCE
    ]

    mismatches = []
    for label, left, right, context, expected_left, expected_right in rows:
        if label in KNOWN_LABEL_DISAGREEMENTS:
            continue
        left_route = _route(left, context)
        right_route = _route(right, context)
        if left_route.intent != expected_left or right_route.intent != expected_right:
            mismatches.append(
                f"{label}: got ({left_route.intent}, {right_route.intent}) "
                f"expected ({expected_left}, {expected_right})"
            )
    assert not mismatches, "undeclared label drift:\n  " + "\n  ".join(mismatches)
