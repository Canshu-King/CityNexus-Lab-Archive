from __future__ import annotations

from .contracts import (
    AgentAction,
    AgentMode,
    AuthorizationDecision,
    AuthorizationResult,
    AuthoritativeActionFacts,
    DelegationPolicy,
)


READ_ACTIONS = {
    AgentAction.INSPECT_JOURNEY,
    AgentAction.INSPECT_TWIN,
    AgentAction.LIST_REPLANS,
    AgentAction.SEARCH_CITY_SERVICES,
}


def evaluate_action(
    policy: DelegationPolicy,
    action: AgentAction,
    facts: AuthoritativeActionFacts,
) -> AuthorizationResult:
    reasons: list[str] = []

    if action in READ_ACTIONS:
        return AuthorizationResult(
            AuthorizationDecision.ALLOW_AUTO,
            ("READ_ONLY_TOOL",),
            policy.version,
        )

    if action == AgentAction.REQUEST_REPLAN:
        # Proposal generation is reversible and cannot activate a PlanVersion.
        return AuthorizationResult(
            AuthorizationDecision.ALLOW_AUTO,
            ("PROPOSAL_ONLY", "DOMAIN_TRUTH_NOT_ACTIVATED"),
            policy.version,
        )

    if action == AgentAction.ACCEPT_REPLAN:
        if facts.hard_constraints_passed is not True:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                ("HARD_CONSTRAINTS_NOT_VERIFIED",),
                policy.version,
            )
        if facts.locked_commitments_preserved is not True or facts.c4_affected:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                ("C4_OR_LOCKED_COMMITMENT_NOT_PRESERVED",),
                policy.version,
            )
        if policy.mode == AgentMode.ADVISORY or not policy.auto_accept_replan:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("USER_CONFIRMATION_REQUIRED",),
                policy.version,
            )
        if facts.cost_delta_minor > policy.max_auto_replan_cost_delta_minor:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("AUTO_COST_LIMIT_EXCEEDED",),
                policy.version,
            )
        if facts.provider_degraded and not policy.allow_auto_when_provider_degraded:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("PROVIDER_EVIDENCE_DEGRADED",),
                policy.version,
            )
        if (
            str(facts.event_severity or "").upper() == "CRITICAL"
            and not policy.allow_auto_on_critical_event
        ):
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("CRITICAL_EVENT_REQUIRES_CONFIRMATION",),
                policy.version,
            )
        return AuthorizationResult(
            AuthorizationDecision.ALLOW_AUTO,
            ("DELEGATION_POLICY_MATCHED", "DETERMINISTIC_GATE_VERIFIED"),
            policy.version,
        )

    if action == AgentAction.UPDATE_PREFERENCES:
        if policy.mode == AgentMode.AUTONOMOUS and policy.auto_update_soft_preferences:
            return AuthorizationResult(
                AuthorizationDecision.ALLOW_AUTO,
                ("SOFT_PREFERENCE_DELEGATED",),
                policy.version,
            )
        return AuthorizationResult(
            AuthorizationDecision.REQUIRE_CONFIRMATION,
            ("PREFERENCE_MUTATION_REQUIRES_CONFIRMATION",),
            policy.version,
        )

    if action == AgentAction.CREATE_BOOKING:
        if (
            policy.mode == AgentMode.AUTONOMOUS
            and policy.auto_book_refundable
            and facts.booking_refundable is True
            and facts.booking_amount_minor <= policy.max_auto_booking_minor
        ):
            return AuthorizationResult(
                AuthorizationDecision.ALLOW_AUTO,
                ("REFUNDABLE_BOOKING_WITHIN_DELEGATED_LIMIT",),
                policy.version,
            )
        return AuthorizationResult(
            AuthorizationDecision.REQUIRE_CONFIRMATION,
            ("BOOKING_REQUIRES_CONFIRMATION",),
            policy.version,
        )

    if action == AgentAction.CANCEL_BOOKING:
        return AuthorizationResult(
            AuthorizationDecision.REQUIRE_CONFIRMATION,
            ("BOOKING_CANCELLATION_REQUIRES_CONFIRMATION",),
            policy.version,
        )

    if action in {AgentAction.PAYMENT, AgentAction.REFUND, AgentAction.MODIFY_C4}:
        return AuthorizationResult(
            AuthorizationDecision.REQUIRE_STEP_UP,
            ("PROTECTED_ACTION_REQUIRES_STEP_UP",),
            policy.version,
        )

    return AuthorizationResult(
        AuthorizationDecision.DENY,
        ("ACTION_NOT_ALLOWLISTED",),
        policy.version,
    )
