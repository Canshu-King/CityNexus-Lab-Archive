from citynexus_agent_ref.contracts import (
    AgentAction,
    AgentMode,
    AuthorizationDecision,
    AuthoritativeActionFacts,
    DelegationPolicy,
)
from citynexus_agent_ref.policy import evaluate_action
from citynexus_agent_ref.tool_catalog import RUNTIME_MCP_ALLOWLIST_V1


def test_read_tools_are_always_safe():
    policy = DelegationPolicy()
    for action in (
        AgentAction.INSPECT_JOURNEY,
        AgentAction.INSPECT_TWIN,
        AgentAction.LIST_REPLANS,
        AgentAction.SEARCH_CITY_SERVICES,
    ):
        assert evaluate_action(policy, action, AuthoritativeActionFacts()).decision == AuthorizationDecision.ALLOW_AUTO


def test_request_replan_is_proposal_only_and_allowed_in_advisory():
    result = evaluate_action(DelegationPolicy(), AgentAction.REQUEST_REPLAN, AuthoritativeActionFacts())
    assert result.decision == AuthorizationDecision.ALLOW_AUTO


def test_advisory_never_auto_accepts_replan():
    facts = AuthoritativeActionFacts(hard_constraints_passed=True, locked_commitments_preserved=True)
    result = evaluate_action(DelegationPolicy(mode=AgentMode.ADVISORY), AgentAction.ACCEPT_REPLAN, facts)
    assert result.decision == AuthorizationDecision.REQUIRE_CONFIRMATION


def test_assisted_can_auto_accept_low_risk_verified_replan():
    policy = DelegationPolicy(
        mode=AgentMode.ASSISTED,
        auto_accept_replan=True,
        max_auto_replan_cost_delta_minor=3000,
    )
    facts = AuthoritativeActionFacts(
        hard_constraints_passed=True,
        locked_commitments_preserved=True,
        cost_delta_minor=1200,
        provider_degraded=False,
        event_severity="MAJOR",
    )
    assert evaluate_action(policy, AgentAction.ACCEPT_REPLAN, facts).decision == AuthorizationDecision.ALLOW_AUTO


def test_agent_can_never_auto_accept_failed_hard_gate():
    policy = DelegationPolicy(mode=AgentMode.AUTONOMOUS, auto_accept_replan=True, max_auto_replan_cost_delta_minor=999999)
    facts = AuthoritativeActionFacts(hard_constraints_passed=False, locked_commitments_preserved=True)
    assert evaluate_action(policy, AgentAction.ACCEPT_REPLAN, facts).decision == AuthorizationDecision.DENY


def test_agent_can_never_auto_accept_c4_damage():
    policy = DelegationPolicy(mode=AgentMode.AUTONOMOUS, auto_accept_replan=True, max_auto_replan_cost_delta_minor=999999)
    facts = AuthoritativeActionFacts(hard_constraints_passed=True, locked_commitments_preserved=False, c4_affected=True)
    assert evaluate_action(policy, AgentAction.ACCEPT_REPLAN, facts).decision == AuthorizationDecision.DENY


def test_cost_limit_forces_confirmation():
    policy = DelegationPolicy(mode=AgentMode.ASSISTED, auto_accept_replan=True, max_auto_replan_cost_delta_minor=1000)
    facts = AuthoritativeActionFacts(hard_constraints_passed=True, locked_commitments_preserved=True, cost_delta_minor=1001)
    assert evaluate_action(policy, AgentAction.ACCEPT_REPLAN, facts).decision == AuthorizationDecision.REQUIRE_CONFIRMATION


def test_degraded_provider_forces_confirmation_by_default():
    policy = DelegationPolicy(mode=AgentMode.AUTONOMOUS, auto_accept_replan=True, max_auto_replan_cost_delta_minor=5000)
    facts = AuthoritativeActionFacts(hard_constraints_passed=True, locked_commitments_preserved=True, provider_degraded=True)
    assert evaluate_action(policy, AgentAction.ACCEPT_REPLAN, facts).decision == AuthorizationDecision.REQUIRE_CONFIRMATION


def test_payment_refund_and_c4_are_step_up_only():
    policy = DelegationPolicy(mode=AgentMode.AUTONOMOUS)
    for action in (AgentAction.PAYMENT, AgentAction.REFUND, AgentAction.MODIFY_C4):
        assert evaluate_action(policy, action, AuthoritativeActionFacts()).decision == AuthorizationDecision.REQUIRE_STEP_UP


def test_runtime_mcp_allowlist_does_not_expose_policy_escalation_or_money_tools():
    assert "inspect_journey" in RUNTIME_MCP_ALLOWLIST_V1
    assert "request_replan" in RUNTIME_MCP_ALLOWLIST_V1
    assert "accept_replan" in RUNTIME_MCP_ALLOWLIST_V1
    assert "set_policy" not in RUNTIME_MCP_ALLOWLIST_V1
    assert "payment" not in RUNTIME_MCP_ALLOWLIST_V1
    assert "refund" not in RUNTIME_MCP_ALLOWLIST_V1
    assert "modify_c4" not in RUNTIME_MCP_ALLOWLIST_V1
    assert "terminal" not in RUNTIME_MCP_ALLOWLIST_V1
    assert "file" not in RUNTIME_MCP_ALLOWLIST_V1
    assert "browser" not in RUNTIME_MCP_ALLOWLIST_V1
