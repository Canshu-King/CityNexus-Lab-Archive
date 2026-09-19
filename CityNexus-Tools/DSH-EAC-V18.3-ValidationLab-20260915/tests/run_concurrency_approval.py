"""DSH-EAC V18.3 — concurrency / idempotency / approval matrix (P0, section 3).

Live against the isolated backend (:8022). Exercises:
  A. concurrent runs on the SAME journey (distinct run_ids, no cross-contamination)
  B. run on a DIFFERENT (non-existent) journey (isolation / 404 behaviour)
  C. approval replay (same approval_id twice -> conflict) -- the idempotency guarantee
  D. cross-journey approval misuse -> 404
Never modifies the main tree.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_common import client, get_scenario, EVIDENCE, record_jsonl  # noqa: E402

SC = get_scenario()
JID = SC["journey_id"]
import httpx  # noqa: E402

MSG = "地铁延误了，帮我检查行程并给出重规划建议。"


def copilot(c, jid, msg="地铁延误了，帮我检查行程并给出重规划建议。"):
    r = c.post(f"/api/v1/journeys/{jid}/copilot/messages", json={"message": msg, "locale": "zh"})
    return r.status_code, (r.json() if r.content else {})


def find_approval_id(events):
    for _, payload in events:
        if isinstance(payload, dict):
            aid = payload.get("approval_id") or payload.get("action_approval_id")
            if aid:
                return aid
            # some envelopes nest it
            data = payload.get("data") or payload.get("result") or {}
            if isinstance(data, dict):
                aid = data.get("approval_id") or data.get("action_approval_id")
                if aid:
                    return aid
    return None


def collect_events(c, jid, run_id, timeout=25.0):
    events = []
    try:
        with c.stream("GET", f"/api/v1/journeys/{jid}/agent/hermes/runs/{run_id}/events") as s:
            deadline = time.time() + timeout
            for line in s.iter_lines():
                if line.startswith("event:"):
                    pass
                elif line.startswith("data:"):
                    try:
                        events.append(("evt", json.loads(line[5:].strip())))
                    except Exception:
                        pass
                if time.time() > deadline:
                    break
    except Exception:
        pass
    return events


def main() -> int:
    c = client()
    results = []

    # A. concurrent same-journey runs
    runs = []
    errs = []
    lock = threading.Lock()

    def worker(i):
        try:
            st, body = copilot(c, JID, f"测试并发请求 {i}：{MSG}")
            with lock:
                ar = body.get("agent_run") or {}
                runs.append({"i": i, "status": st, "run_id": ar.get("run_id"),
                             "identity": ar.get("runtime_identity")})
        except Exception as e:  # noqa: BLE001
            with lock:
                errs.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    distinct = len({r.get("run_id") for r in runs if r.get("run_id")})
    results.append({"case": "CN-A_concurrent_same_journey", "requests": len(runs), "distinct_run_ids": distinct,
                   "ok": distinct == len(runs) and len(runs) == 3, "detail": runs, "errors": errs})

    # B. run on a non-existent (different) journey -> isolation
    fake_jid = str(uuid.uuid4())
    st, body = copilot(c, fake_jid, MSG)
    results.append({"case": "CN-B_different_journey_isolation", "status": st,
                   "ok": st in (404, 422), "note": "non-existent journey must not create a run"})

    # C/D. approval replay + cross-journey misuse
    # Drive a mutation-requesting message that should require an ActionApproval.
    st, body = copilot(c, JID, "帮我把行程里第一个活动直接取消，并改到下午3点开始。")
    run_id = (body.get("agent_run") or {}).get("run_id")
    approval_id = None
    if run_id:
        evs = collect_events(c, JID, run_id)
        approval_id = find_approval_id(evs)
        results.append({"case": "CN-C_approval_discovery", "run_id": run_id,
                       "events": len(evs), "approval_id_found": approval_id is not None})

    if approval_id:
        # C1 approve once
        r1 = c.post(f"/api/v1/journeys/{JID}/agent/approvals/{approval_id}/approve",
                    json={"approval_method": "USER_CONFIRMATION"})
        # C2 replay same approval_id (idempotency / already-consumed)
        r2 = c.post(f"/api/v1/journeys/{JID}/agent/approvals/{approval_id}/approve",
                    json={"approval_method": "USER_CONFIRMATION"})
        # D1 cross-journey misuse
        r3 = c.post(f"/api/v1/journeys/{fake_jid}/agent/approvals/{approval_id}/approve",
                    json={"approval_method": "USER_CONFIRMATION"})
        results.append({"case": "CN-C_approve_once", "status": r1.status_code,
                       "ok": r1.status_code in (200, 201, 202)})
        results.append({"case": "CN-C_approve_replay_same_id", "status": r2.status_code,
                       "ok": r2.status_code in (409, 404, 422),
                       "note": "replay of consumed approval must be rejected, not re-executed"})
        results.append({"case": "CN-D_cross_journey_misuse", "status": r3.status_code,
                       "ok": r3.status_code == 404, "note": "approval scoped to its journey"})
    else:
        results.append({"case": "CN-C_approval_discovery", "ok": False,
                       "note": "could not trigger an ActionApproval in test window; "
                               "see report for source-level guarantee + recipe"})

    passed = sum(1 for x in results if x.get("ok"))
    summary = {"passed": passed, "total": len(results), "results": results}
    (EVIDENCE / "concurrency_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    for line in results:
        record_jsonl("concurrency_results.jsonl", line)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
