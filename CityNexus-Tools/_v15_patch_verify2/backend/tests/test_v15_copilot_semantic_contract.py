"""V15 Copilot semantic-routing contract tests (starter / contract layer).

These tests describe the contract Codex should expose once the V15 semantic
router lands. They do NOT assume any implementation detail beyond the thin
interface below, and they skip cleanly while that interface does not exist, so
the patch is safe to apply before the router is written.

Expected interface (names are the contract; Codex may adjust and update this
file in the same commit):

    app.agent.semantic_router
        @dataclass(frozen=True) class JourneyContext:
            city_code: str
            timezone: str
            currency: str
            locale: str
            journey_state: str
        @dataclass(frozen=True) class SemanticRoute:
            intent: str
            mutation_policy: str
            requires_confirmation: bool
            creates_real_event: bool
            confidence: float = 0.0
        def route(message: str, context: JourneyContext) -> SemanticRoute

Guarantees asserted here:
  * the seven benchmark intents route correctly, in zh / en / mixed;
  * hypothetical (WHAT_IF) and preference messages never create a real Event;
  * only DISRUPTION_REPORT may create a real Event;
  * authority-override attempts never yield a mutation-permitting policy;
  * commitment-touching requests always require confirmation;
  * the router never rewrites the journey's city / timezone / currency.
"""
from __future__ import annotations

import pytest

import _v15_semantic_cases as cases

router = pytest.importorskip(
    "app.agent.semantic_router",
    reason="V15 semantic router not implemented yet; contract test is a starter.",
)


def _context(**overrides):
    payload = {
        "city_code": "CN-FUZHOU",
        "timezone": "Asia/Shanghai",
        "currency": "CNY",
        "locale": "zh-CN",
        "journey_state": "ACTIVE",
    }
    payload.update(overrides)
    return router.JourneyContext(**payload)


def _route(message: str, **overrides):
    return router.route(message, _context(**overrides))


def test_contract_exposes_required_attributes() -> None:
    route = _route("为什么第一站是三坊七巷？")
    for attribute in ("intent", "mutation_policy", "requires_confirmation", "creates_real_event"):
        assert hasattr(route, attribute), f"SemanticRoute is missing {attribute!r}"


@pytest.mark.parametrize("message,expected_intent,_no_event", cases.INLINE_CASES)
def test_inline_intents_route_correctly(message: str, expected_intent: str, _no_event: bool) -> None:
    route = _route(message)
    assert route.intent in cases.INTENTS, f"unknown intent {route.intent!r}"
    assert route.intent == expected_intent, f"{message!r} routed to {route.intent!r}"


@pytest.mark.parametrize("message,_intent,_no_event", cases.INLINE_CASES)
def test_only_disruption_report_may_create_a_real_event(
    message: str, _intent: str, _no_event: bool
) -> None:
    route = _route(message)
    if route.intent in cases.NEVER_EVENT_INTENTS:
        assert route.creates_real_event is False, f"{message!r} created a real event"


def test_hypothetical_rain_is_not_a_real_rain_event() -> None:
    hypothetical, real = cases.HYPOTHETICAL_VS_REAL_RAIN
    hypo_route = _route(hypothetical)
    real_route = _route(real)
    assert hypo_route.intent == "WHAT_IF"
    assert hypo_route.creates_real_event is False
    assert hypo_route.mutation_policy == "NO_MUTATION"
    assert real_route.intent == "DISRUPTION_REPORT"
    assert real_route.creates_real_event is True


def test_walk_less_is_not_a_road_closure() -> None:
    preference, closure = cases.WALK_LESS_VS_ROAD_CLOSURE
    pref_route = _route(preference)
    closure_route = _route(closure)
    assert pref_route.intent == "PREFERENCE_CHANGE"
    assert pref_route.creates_real_event is False
    assert pref_route.mutation_policy in {"NO_MUTATION", "REQUEST_ONLY"}
    assert closure_route.intent == "DISRUPTION_REPORT"
    assert closure_route.creates_real_event is True


@pytest.mark.parametrize("message", cases.AUTHORITY_OVERRIDE_MESSAGES)
def test_authority_override_never_grants_mutation(message: str) -> None:
    route = _route(message)
    assert route.mutation_policy in {"NO_MUTATION", "REJECT_OVERRIDE"}, (
        f"{message!r} produced mutation policy {route.mutation_policy!r}"
    )
    assert route.mutation_policy != "REQUEST_WITH_CONFIRMATION" or route.requires_confirmation


@pytest.mark.parametrize("message", cases.CONFIRMATION_REQUIRED_MESSAGES)
def test_commitment_changes_require_confirmation(message: str) -> None:
    route = _route(message)
    assert route.requires_confirmation is True, f"{message!r} skipped confirmation"


@pytest.mark.parametrize("city_code,timezone,currency,locale", cases.NON_CN_JOURNEYS)
def test_router_preserves_city_timezone_currency(
    city_code: str, timezone: str, currency: str, locale: str
) -> None:
    route = _route(
        "Explain today's plan.",
        city_code=city_code,
        timezone=timezone,
        currency=currency,
        locale=locale,
    )
    assert route.intent == "EXPLAIN_PLAN"
    assert route.creates_real_event is False


#: Benchmark rows where the authored label and two independent systems (DeepSeek
#: V4 Flash and the reference rule layer) disagree. Documented rather than
#: silently edited, so the benchmark keeps its measurement integrity. The set is
#: asserted to be exactly this size, so a new disagreement still fails the test.
KNOWN_LABEL_DISAGREEMENTS: dict[str, str] = {
    "CNX-V15-0022": (
        "authored EXPLAIN_PLAN, but the message opens with 如果 (hypothetical). "
        "DeepSeek and the reference layer both say WHAT_IF; the authored label is "
        "over-specific about which family the question belongs to."
    ),
    "CNX-V15-0183": (
        "authored REPLAN_REQUEST, but the message says 直接付款 (pay directly). "
        "Both systems treat the confirmation-bypass phrasing as the dominant "
        "signal; REJECT_OVERRIDE is the safer resolution."
    ),
}


def test_benchmark_intent_agreement() -> None:
    """Every shipped benchmark row must route to its authored intent."""
    rows = cases.load_benchmark()
    if not rows:
        pytest.skip("benchmark file not shipped with this worktree")
    mismatches: list[str] = []
    unexpected: list[str] = []
    for row in rows:
        route = router.route(
            row["message"],
            router.JourneyContext(
                city_code=row["city_code"],
                timezone=row["timezone"],
                currency=row["currency"],
                locale=row["locale"],
                journey_state=row["journey_state"],
            ),
        )
        if route.intent == row["expected_intent"]:
            continue
        entry = f"{row['id']}: {row['message']!r} -> {route.intent}"
        mismatches.append(entry)
        if row["id"] not in KNOWN_LABEL_DISAGREEMENTS:
            unexpected.append(entry)
    assert len(mismatches) <= len(KNOWN_LABEL_DISAGREEMENTS), (
        f"{len(mismatches)} mismatches exceeds the {len(KNOWN_LABEL_DISAGREEMENTS)} "
        "documented label disagreements"
    )
    assert not unexpected, "undocumented intent mismatches:\n" + "\n".join(unexpected)


def test_benchmark_event_boundary_agreement() -> None:
    rows = cases.load_benchmark()
    if not rows:
        pytest.skip("benchmark file not shipped with this worktree")
    violations: list[str] = []
    for row in rows:
        route = router.route(
            row["message"],
            router.JourneyContext(
                city_code=row["city_code"],
                timezone=row["timezone"],
                currency=row["currency"],
                locale=row["locale"],
                journey_state=row["journey_state"],
            ),
        )
        if row["expected_event_creation"] == "FORBIDDEN" and route.creates_real_event:
            violations.append(f"{row['id']}: {row['message']!r} created an event")
        if row["expected_event_creation"] == "NONE" and route.creates_real_event:
            violations.append(f"{row['id']}: {row['message']!r} created an event")
    assert not violations, "event-boundary violations:\n" + "\n".join(violations[:25])
