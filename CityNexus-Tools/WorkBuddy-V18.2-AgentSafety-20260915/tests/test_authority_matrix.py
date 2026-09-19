#!/usr/bin/env python3
"""V18.2 Authority matrix — adversarial cases against the real delegation policy.

Pure and deterministic: imports `app.agent.delegation_policy.evaluate_action`
(the function AgentToolGateway calls) and asserts that no adversarial request can
be auto-executed. No server, no DB, no network.

Run:
    python tests/test_authority_matrix.py --repo <repo_copy/backend> \
        --out evidence/results_authority.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

RESULTS: list[dict[str, Any]] = []
AUTO = "ALLOW_AUTO"


def record(cid: str, name: str, expected: str, actual: str, status: str,
           evidence: Any = None) -> None:
    RESULTS.append({"id": cid, "name": name, "expected": expected,
                    "actual": actual, "status": status, "evidence": evidence})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "NOT_TESTED": "SKIP"}.get(status, status)
    print(f"[{mark}] {cid:6} {name}")
    if status == "FAIL":
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", default="evidence/results_authority.json")
    args = ap.parse_args()
    sys.path.insert(0, os.path.abspath(args.repo))

    from app.agent.contracts import (  # noqa: E402
        AgentAction, AgentMode, AuthoritativeActionFacts, AuthorizationDecision,
        DelegationPolicy,
    )
    from app.agent.delegation_policy import evaluate_action  # noqa: E402

    # ---- policies -----------------------------------------------------------
    default_advisory = DelegationPolicy(mode=AgentMode.ADVISORY, auto_accept_replan=False)
    assisted = DelegationPolicy(mode=AgentMode.ASSISTED, auto_accept_replan=False)
    auto_strict = DelegationPolicy(mode=AgentMode.AUTONOMOUS, auto_accept_replan=True,
                                   max_auto_replan_cost_delta_minor=0, max_auto_loss_minor=0,
                                   max_auto_schedule_drift_min=0)
    auto_wide = DelegationPolicy(mode=AgentMode.AUTONOMOUS, auto_accept_replan=True,
                                 max_auto_replan_cost_delta_minor=100000,
                                 max_auto_loss_minor=100000,
                                 max_auto_schedule_drift_min=600,
                                 allowed_activity_types=("activity", "visit", "dining", "transport"),
                                 allowed_booking_types=("booking", "boat", "train", "flight"),
                                 allow_auto_commitment_management=True,
                                 allow_auto_when_provider_degraded=True,
                                 allow_auto_on_critical_event=True)
    POL = {"advisory": default_advisory, "assisted": assisted,
           "auto_strict": auto_strict, "auto_wide": auto_wide}

    # ---- facts --------------------------------------------------------------
    # "worst_case_claim" = the attacker asserts every precondition is satisfied.
    claim_clean = AuthoritativeActionFacts(
        hard_constraints_passed=True, locked_commitments_preserved=True, c4_affected=False,
        cost_delta_minor=0, loss_delta_minor=0, schedule_drift_min=0,
        action_reversible=True, commitment_management_requested=False,
        proposal_presented=True, base_plan_current=True, trigger_actionable=True,
        impact_target_server_validated=True, impact_maturity="VALIDATED_IMPACT",
    )
    protected = AuthoritativeActionFacts(
        hard_constraints_passed=True, locked_commitments_preserved=False, c4_affected=True,
        commitment_management_requested=True, commitment_levels=("C4_Anchored",),
        action_reversible=False, loss_delta_minor=50000,
    )
    paid_boat = AuthoritativeActionFacts(
        hard_constraints_passed=True, locked_commitments_preserved=True, c4_affected=False,
        action_reversible=False, loss_delta_minor=48000, commitment_management_requested=True,
        affected_booking_type="boat",
    )
    unverified = AuthoritativeActionFacts(hard_constraints_passed=None)

    def dec(policy_name: str, action: AgentAction, facts: AuthoritativeActionFacts) -> str:
        return evaluate_action(POL[policy_name], action, facts).decision.value

    # ---- B: the ten adversarial cases --------------------------------------
    # Each: under the DEFAULT policy the decision must never be ALLOW_AUTO.
    attacks = [
        ("B1", "cancel a PAID boat", AgentAction.CANCEL_REFUNDABLE_BOOKING, paid_boat),
        ("B2", "modify a confirmed train/flight", AgentAction.RESCHEDULE_ACTIVITY, protected),
        ("B3", "delete a protected C4 Commitment", AgentAction.REQUEST_COMMITMENT_CHANGE, protected),
        ("B4", "auto-accept a replan", AgentAction.ACCEPT_REPLAN, protected),
        ("B5", "create a Booking", AgentAction.CREATE_BOOKING, claim_clean),
        ("B6", "cancel a Booking", AgentAction.CANCEL_REFUNDABLE_BOOKING, claim_clean),
        ("B7", "modify a Payment", AgentAction.PAYMENT, claim_clean),
        ("B8", "modify Departure", AgentAction.RESCHEDULE_ACTIVITY, claim_clean),
        ("B9", "modify Arrival", AgentAction.RESCHEDULE_ACTIVITY, claim_clean),
        ("B10", "ignore system limits (modify C4)", AgentAction.MODIFY_C4, claim_clean),
    ]
    for cid, name, action, facts in attacks:
        d = dec("advisory", action, facts)
        ok = d != AUTO
        record(cid, f"[default policy] {name} must not auto-execute",
               "DENY / REQUIRE_CONFIRMATION / REQUIRE_STEP_UP", d,
               "PASS" if ok else "FAIL", {"action": action.value})

    # ---- explicit expected decisions ---------------------------------------
    explicit = [
        ("B1x", "paid boat cancellation is not auto even with wide autonomy",
         "auto_wide", AgentAction.CANCEL_REFUNDABLE_BOOKING, paid_boat,
         {"REQUIRE_CONFIRMATION", "REQUIRE_STEP_UP", "DENY"}),
        ("B3x", "protected C4 commitment change requires STEP_UP",
         "auto_wide", AgentAction.REQUEST_COMMITMENT_CHANGE, protected, {"REQUIRE_STEP_UP"}),
        ("B4x", "replan accept DENIED when C4 not preserved",
         "auto_wide", AgentAction.ACCEPT_REPLAN, protected, {"DENY"}),
        ("B7x", "payment always requires STEP_UP",
         "auto_wide", AgentAction.PAYMENT, claim_clean, {"REQUIRE_STEP_UP"}),
        ("B7y", "refund always requires STEP_UP",
         "auto_wide", AgentAction.REFUND, claim_clean, {"REQUIRE_STEP_UP"}),
        ("B8x", "mutations DENIED when hard constraints unverified",
         "auto_wide", AgentAction.RESCHEDULE_ACTIVITY, unverified, {"DENY"}),
    ]
    for cid, name, pol, action, facts, allowed in explicit:
        d = dec(pol, action, facts)
        ok = d in allowed
        record(cid, name, f"one of {sorted(allowed)}", d, "PASS" if ok else "FAIL",
               {"policy": pol, "action": action.value})

    # ---- invariant: default policy can NEVER auto a mutating action ---------
    mutating = [AgentAction.REPLACE_ACTIVITY, AgentAction.RESCHEDULE_ACTIVITY,
                AgentAction.CREATE_BOOKING, AgentAction.CANCEL_REFUNDABLE_BOOKING,
                AgentAction.REQUEST_COMMITMENT_CHANGE, AgentAction.ACCEPT_REPLAN,
                AgentAction.PAYMENT, AgentAction.REFUND, AgentAction.MODIFY_C4]
    leaks = [a.value for a in mutating if dec("advisory", a, claim_clean) == AUTO]
    record("B11", "INVARIANT: default ADVISORY auto-executes no mutating action",
           "empty leak set", f"leaks={leaks}", "PASS" if not leaks else "FAIL")

    leaks2 = [a.value for a in mutating if dec("assisted", a, claim_clean) == AUTO]
    record("B12", "INVARIANT: ASSISTED auto-executes no mutating action",
           "empty leak set", f"leaks={leaks2}", "PASS" if not leaks2 else "FAIL")

    # ---- reads and proposal-only are correctly free -------------------------
    for cid, action in [("B13", AgentAction.INSPECT_JOURNEY), ("B14", AgentAction.INSPECT_TWIN),
                        ("B15", AgentAction.LIST_REPLANS), ("B16", AgentAction.SEARCH_CITY_SERVICES)]:
        d = dec("advisory", action, claim_clean)
        record(cid, f"read action {action.value} is auto (read-only)",
               AUTO, d, "PASS" if d == AUTO else "FAIL")
    r = evaluate_action(default_advisory, AgentAction.REQUEST_REPLAN, claim_clean)
    record("B17", "REQUEST_REPLAN is auto but PROPOSAL_ONLY (no domain truth)",
           "ALLOW_AUTO with PROPOSAL_ONLY + DOMAIN_TRUTH_NOT_ACTIVATED",
           f"{r.decision.value} {list(r.reason_codes)}",
           "PASS" if r.decision.value == AUTO and "PROPOSAL_ONLY" in r.reason_codes else "FAIL")

    # ---- prompt-injection reality check ------------------------------------
    # The authority function is a pure (policy, action, facts) function: there is
    # no free-text parameter an injected prompt could reach. Prove determinism:
    # identical structured input yields an identical decision, and the function
    # signature exposes no text channel.
    import inspect
    sig = str(inspect.signature(evaluate_action))
    no_text = "text" not in sig and "prompt" not in sig and "message" not in sig
    record("B18", "authority boundary takes no free-text (injection cannot reach it)",
           "signature has only policy/action/facts", sig,
           "PASS" if no_text else "FAIL")
    d1 = dec("advisory", AgentAction.CANCEL_REFUNDABLE_BOOKING, paid_boat)
    d2 = dec("advisory", AgentAction.CANCEL_REFUNDABLE_BOOKING, paid_boat)
    record("B19", "authority decision is deterministic for identical structured input",
           "same decision twice", f"{d1} == {d2}", "PASS" if d1 == d2 else "FAIL")

    # ---- a fully permissive policy still protects the invariants ------------
    # Even with auto_accept_replan + wide limits, protected commitments force
    # STEP_UP and non-reversible money-losing actions force CONFIRMATION.
    d = dec("auto_wide", AgentAction.CANCEL_REFUNDABLE_BOOKING, protected)
    record("B20", "wide autonomy still cannot auto a protected C4 mutation",
           "REQUIRE_STEP_UP (not ALLOW_AUTO)", d,
           "PASS" if d != AUTO else "FAIL")
    d = dec("auto_wide", AgentAction.REPLACE_ACTIVITY, paid_boat)
    record("B21", "wide autonomy still cannot auto a non-reversible money-losing replace",
           "REQUIRE_CONFIRMATION/STEP_UP (not ALLOW_AUTO)", d,
           "PASS" if d != AUTO else "FAIL")

    summary = {"PASS": 0, "FAIL": 0, "NOT_TESTED": 0}
    for x in RESULTS:
        summary[x["status"]] = summary.get(x["status"], 0) + 1
    payload = {"meta": {"harness": "tests/test_authority_matrix.py", "repo": args.repo,
                        "note": "deterministic adversarial matrix over evaluate_action"},
               "summary": summary, "scenarios": RESULTS}
    out = args.out
    if not os.path.isabs(out):
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n== SUMMARY ==  PASS={summary['PASS']} FAIL={summary['FAIL']} NOT_TESTED={summary['NOT_TESTED']}")
    print("written:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
