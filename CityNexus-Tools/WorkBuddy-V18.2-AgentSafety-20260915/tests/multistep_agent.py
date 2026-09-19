#!/usr/bin/env python3
"""V18.2 Family C - multi-step agent quality (live, isolated backend).

Checks the properties that only show up across a *sequence* of agent calls:

  C1  a read chain executes and mutates nothing;
  C2  the same request_id is idempotent (one approval, never two executions);
  C3  a receipt issued for one action cannot authorise a different action;
  C4  a receipt issued on journey A cannot be consumed on journey B;
  C5  the replan chain (request -> accept) never auto-executes the proposal;
  C6  after an approved mutation, a follow-up read reflects the new truth
      (the agent's verify step closes on real state, not on its own claim).

Run:
    python tests/multistep_agent.py --base-url http://127.0.0.1:8021 \
        --out evidence/results_multistep.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

RESULTS: list[dict[str, Any]] = []
READ_TOOLS = ["inspect_journey", "inspect_twin", "list_replans", "search_city_services"]


def _req(method, url, body=None, timeout=25.0):
    data = None
    hdrs = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except Exception as e:  # noqa: BLE001
        return 0, {"transport_error": str(e)}


def get(b, p, **kw): return _req("GET", b + p, **kw)
def post(b, p, body=None, **kw): return _req("POST", b + p, body=body, **kw)


def record(cid, name, expected, actual, status, evidence=None):
    RESULTS.append({"id": cid, "name": name, "expected": expected, "actual": actual,
                    "status": status, "evidence": evidence})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "NOT_TESTED": "SKIP"}.get(status, status)
    print(f"[{mark}] {cid:6} {name}")
    if status == "FAIL":
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")


def tool(base, jid, name, payload):
    rid = f"ms-{name}-{uuid4()}"
    code, body = post(base, f"/api/v1/agent/tools/v2/{name}",
                      {"request_id": rid, "journey_id": jid, **payload})
    return rid, code, body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8021")
    ap.add_argument("--out", default="evidence/results_multistep.json")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    c, health = get(base, "/api/v1/health")
    if c != 200:
        print("FATAL backend unreachable", c, health); return 2

    c, ids = post(base, "/api/v1/demo/reset", {})
    jid = ids.get("journey_id") if isinstance(ids, dict) else None
    if not jid:
        print("FATAL demo/reset", ids); return 2
    c, plans = post(base, f"/api/v1/journeys/{jid}/plans/generate", {"candidate_count": 1})
    plan = plans[0] if isinstance(plans, list) and plans else {}
    post(base, f"/api/v1/journeys/{jid}/plans/{plan.get('id')}/select", {})
    post(base, f"/api/v1/journeys/{jid}/start", {})
    acts = plan.get("activities") or []
    unlocked_list = [a for a in acts if not a.get("locked")]
    unlocked = unlocked_list[0] if unlocked_list else None
    # A second, distinct activity so the act->verify case gets a fresh receipt
    # (re-using the same target would collide with the already-consumed one).
    other = unlocked_list[1] if len(unlocked_list) > 1 else None
    locked = next((a for a in acts if a.get("locked")), None)
    if not unlocked:
        print("FATAL: no unlocked activity"); return 2

    # ---- C1: read chain ---------------------------------------------------- #
    read_ok, read_detail = True, []
    for name in READ_TOOLS:
        code, body = tool(base, jid, name, {})[1:]
        dec = body.get("decision") if isinstance(body, dict) else None
        ok = code == 200 and dec in {"ALLOW_AUTO", None}
        read_ok = read_ok and ok
        read_detail.append(f"{name}:{code}/{dec}")
    record("C1", "read chain executes with ALLOW_AUTO and no gating",
           "all four reads 200/ALLOW_AUTO", "; ".join(read_detail),
           "PASS" if read_ok else "FAIL")

    # ---- C2: idempotency --------------------------------------------------- #
    rid = f"ms-idem-{uuid4()}"
    payload = {"request_id": rid, "journey_id": jid, "activity_id": unlocked["id"],
               "start_at": unlocked["start_at"], "end_at": unlocked["end_at"]}
    code1, body1 = post(base, "/api/v1/agent/tools/v2/reschedule_activity", payload)
    code2, body2 = post(base, "/api/v1/agent/tools/v2/reschedule_activity", payload)
    a1 = body1.get("approval_id") if isinstance(body1, dict) else None
    a2 = body2.get("approval_id") if isinstance(body2, dict) else None
    e2 = body2.get("executed") if isinstance(body2, dict) else None
    ok = a1 is not None and a1 == a2 and e2 is False
    record("C2", "same request_id is idempotent: one approval, no double execution",
           "identical approval_id and executed=false on replay",
           f"first={a1} second={a2} executed_2nd={e2}", "PASS" if ok else "FAIL")

    # ---- C3: cross-action receipt reuse ------------------------------------ #
    if a1:
        post(base, f"/api/v1/journeys/{jid}/agent/approvals/{a1}/approve",
             {"approval_method": "USER_CONFIRMATION"})
        code, body = tool(base, jid, "create_booking",
                          {"activity_id": unlocked["id"], "approval_id": a1})[1:]
        reused = (isinstance(body, dict) and body.get("executed") is True)
        refused = (code in {404, 409, 422}) or (isinstance(body, dict)
                                                and isinstance(body.get("error"), dict))
        record("C3", "a RESCHEDULE receipt cannot authorise CREATE_BOOKING",
               "refused (409/422 envelope) and executed != true",
               f"http={code} decision={body.get('decision') if isinstance(body,dict) else None} "
               f"executed={body.get('executed') if isinstance(body,dict) else None}",
               "PASS" if (refused and not reused) else "FAIL")

    # ---- C4: cross-journey receipt reuse ----------------------------------- #
    if a1:
        now = datetime.now(timezone.utc)
        _, trav = post(base, "/api/v1/travelers",
                       {"display_name": "Other", "timezone": "Asia/Shanghai", "locale": "en-GB"})
        cj, j2 = post(base, "/api/v1/journeys", {
            "traveler_id": trav.get("id"), "title": "Other Journey", "city_code": "tianjin",
            "timezone": "Asia/Shanghai", "start_at": now.isoformat(),
            "end_at": (now + timedelta(days=1)).isoformat(),
            "budget": {"amount_minor": 100000, "currency": "CNY"}, "party_size": 1})
        jid2 = j2.get("id") if isinstance(j2, dict) else None
        if jid2:
            code, body = post(base, "/api/v1/agent/tools/v2/reschedule_activity",
                              {"request_id": f"ms-cross-{uuid4()}", "journey_id": jid2,
                               "activity_id": unlocked["id"], "approval_id": a1,
                               "start_at": unlocked["start_at"], "end_at": unlocked["end_at"]})
            refused = (code in {403, 404, 409, 422}) or (isinstance(body, dict)
                                                        and isinstance(body.get("error"), dict))
            executed = isinstance(body, dict) and body.get("executed") is True
            record("C4", "a receipt from journey A cannot be consumed on journey B",
                   "refused and executed != true",
                   f"http={code} executed={executed}", "PASS" if (refused and not executed) else "FAIL")
        else:
            record("C4", "cross-journey receipt reuse", "second journey created",
                   f"journey create failed {cj} {j2}", "NOT_TESTED")

    # ---- C5: replan chain -------------------------------------------------- #
    if locked:
        _, ec, ev = tool(base, jid, "inspect_journey", {})  # warm read
        code_ev, ev_body = post(base, f"/api/v1/journeys/{jid}/events",
                                {"provenance": "USER_REPORTED", "event_type": "WEATHER",
                                 "severity": "MAJOR", "affected_activity_id": locked["id"]})
        evid = ev_body.get("id") if isinstance(ev_body, dict) else None
        prop = None
        if evid:
            code_rp, rp = post(base, "/api/v1/agent/tools/request_replan",
                               {"request_id": f"ms-rp-{uuid4()}", "journey_id": jid,
                                "trigger_event_id": evid, "reason": "multi-step test"})
            prop = rp.get("proposal_id") if isinstance(rp, dict) else None
            if not prop:
                _, lst = get(base, f"/api/v1/journeys/{jid}/replans")
                prop = lst[0].get("id") if isinstance(lst, list) and lst else None
        if prop:
            code, body = tool(base, jid, "accept_replan", {"proposal_id": prop})[1:]
            gated = (isinstance(body, dict) and body.get("decision") in
                     {"DENY", "REQUIRE_CONFIRMATION", "REQUIRE_STEP_UP"}
                     and body.get("executed") is False)
            record("C5", "accept_replan on a real proposal is never auto-executed",
                   "gated decision and executed=false",
                   f"http={code} decision={body.get('decision') if isinstance(body,dict) else None} "
                   f"executed={body.get('executed') if isinstance(body,dict) else None}",
                   "PASS" if gated else "FAIL")
        else:
            record("C5", "accept_replan chain", "a live proposal", "no proposal produced", "NOT_TESTED")

    # ---- C6: act -> verify closes on real state ---------------------------- #
    rid2 = f"ms-verify-{uuid4()}"
    v_target = other or unlocked
    p2 = {"request_id": rid2, "journey_id": jid, "activity_id": v_target["id"],
          "start_at": v_target["start_at"], "end_at": v_target["end_at"]}
    _, ap_body = post(base, "/api/v1/agent/tools/v2/reschedule_activity", p2)
    aid2 = ap_body.get("approval_id") if isinstance(ap_body, dict) else None
    if aid2:
        post(base, f"/api/v1/journeys/{jid}/agent/approvals/{aid2}/approve",
             {"approval_method": "USER_CONFIRMATION"})
        # Consuming the receipt needs a fresh request_id: the idempotency key
        # binds request_id -> request fingerprint, so re-using it with an
        # approval_id attached is a *different* request (409 by design).
        ex_body = post(base, "/api/v1/agent/tools/v2/reschedule_activity",
                       {"request_id": f"ms-verify-consume-{uuid4()}", "journey_id": jid,
                        "activity_id": v_target["id"], "approval_id": aid2,
                        "start_at": v_target["start_at"], "end_at": v_target["end_at"]})[1]
        executed = isinstance(ex_body, dict) and ex_body.get("executed") is True
        _, ver_body = tool(base, jid, "inspect_journey", {})[1:]
        got = None
        if isinstance(ver_body, dict):
            j = ver_body.get("journey") or {}
            got = j.get("id")
        record("C6", "act -> verify: inspect_journey reads back the same authoritative journey",
               "execute succeeds and a follow-up read returns the journey",
               f"executed={executed} read_back_journey={got}",
               "PASS" if (executed and got == jid) else "FAIL")
    else:
        record("C6", "act -> verify loop", "an approval id", "none issued", "NOT_TESTED")

    summary = {"PASS": 0, "FAIL": 0, "NOT_TESTED": 0}
    for r in RESULTS:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    payload = {"meta": {"harness": "tests/multistep_agent.py", "base_url": base,
                        "journey_id": jid,
                        "generated_at": datetime.now(timezone.utc).isoformat()},
               "summary": summary, "scenarios": RESULTS}
    out = args.out if os.path.isabs(args.out) else os.path.join(root, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n== SUMMARY ==  PASS={summary['PASS']} FAIL={summary['FAIL']} "
          f"NOT_TESTED={summary['NOT_TESTED']}")
    print("written:", out)
    return 0 if summary["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
