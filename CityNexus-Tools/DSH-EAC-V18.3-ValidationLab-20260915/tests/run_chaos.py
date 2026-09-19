"""DSH-EAC V18.3 — Hermes chaos / recovery matrix (P0, section 2).

Live against the isolated backend (:8022). Covers the safely-injectable chaos
cases; gateway-kill / backend-kill / DeepSeek-kill cases that would destabilise
the shared harness are recorded as recipes (see report). Never modifies main tree.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_common import client, get_scenario, EVIDENCE, record_jsonl  # noqa: E402

SC = get_scenario()
JID = SC["journey_id"]
UNK = str(uuid.uuid4())


def sse_events(c, path):
    events = []
    try:
        with c.stream("GET", path) as s:
            buf = ""
            for line in s.iter_lines():
                if line.startswith("event:"):
                    buf = line[6:].strip()
                elif line.startswith("data:"):
                    try:
                        payload = json.loads(line[5:].strip())
                        events.append((buf, payload))
                    except Exception:
                        pass
        return s.status_code, events, None
    except Exception as e:  # noqa: BLE001
        return None, events, f"{type(e).__name__}: {e}"


def main() -> int:
    c = client()
    results = []

    # CH1 — unknown native run (global) must NOT fake a completed run
    r = c.get(f"/api/v1/agent/hermes/runs/{UNK}")
    results.append({"case": "CH1_unknown_run_get", "status": r.status_code,
                   "ok": r.status_code == 502, "note": "want 502, never 200 fake"})

    # CH2 — stop unknown run must NOT 500/200
    r = c.post(f"/api/v1/journeys/{JID}/agent/hermes/runs/{UNK}/stop", json={})
    results.append({"case": "CH2_stop_unknown_run", "status": r.status_code,
                   "ok": r.status_code == 502, "note": "want 502"})

    # CH3 — SSE for unknown run must not emit a fake terminal event
    st, evs, err = sse_events(c, f"/api/v1/agent/hermes/runs/{UNK}/events")
    terminal = [e for e in evs if e[0] in ("run.completed", "run.failed", "run.stopped")]
    results.append({"case": "CH3_sse_unknown_run", "status": st, "events": len(evs),
                   "fake_terminal": bool(terminal), "ok": (not terminal) and st != 200,
                   "err": err})

    # CH4 — SSE for unknown run (journey-scoped)
    st, evs, err = sse_events(c, f"/api/v1/journeys/{JID}/agent/hermes/runs/{UNK}/events")
    terminal = [e for e in evs if e[0] in ("run.completed", "run.failed", "run.stopped")]
    results.append({"case": "CH4_sse_unknown_run_journey", "status": st, "events": len(evs),
                   "fake_terminal": bool(terminal), "ok": (not terminal) and st != 200, "err": err})

    # CH5 — reconnect / dedup stability on the real completed run from prior evidence
    try:
        prior = json.loads((EVIDENCE / "native_e2e_run.json").read_text(encoding="utf-8"))
        real_run = prior.get("run_id")
    except Exception:
        real_run = None
    if real_run:
        st1, evs1, _ = sse_events(c, f"/api/v1/journeys/{JID}/agent/hermes/runs/{real_run}/events")
        st2, evs2, _ = sse_events(c, f"/api/v1/journeys/{JID}/agent/hermes/runs/{real_run}/events")
        keys1 = [(e[0], json.dumps(e[1], sort_keys=True)) for e in evs1]
        keys2 = [(e[0], json.dumps(e[1], sort_keys=True)) for e in evs2]
        results.append({"case": "CH5_reconnect_dedup", "status1": st1, "status2": st2,
                       "count1": len(keys1), "count2": len(keys2),
                       "stable": keys1 == keys2,
                       "ok": keys1 == keys2 and len(keys1) > 0})
        # CH6 — stop an already-completed run must not create a late mutation / 500
        r = c.post(f"/api/v1/journeys/{JID}/agent/hermes/runs/{real_run}/stop", json={})
        results.append({"case": "CH6_stop_completed_run", "status": r.status_code,
                       "ok": r.status_code in (200, 409, 422),
                       "note": "want terminal/conflict, never 500 fake"})
    else:
        results.append({"case": "CH5_reconnect_dedup", "ok": False, "note": "no prior real run id"})

    passed = sum(1 for x in results if x.get("ok"))
    summary = {"passed": passed, "total": len(results), "results": results}
    (EVIDENCE / "chaos_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    for line in results:
        record_jsonl("chaos_results.jsonl", line)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
