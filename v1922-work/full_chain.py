"""Full same-journey Xiamen acceptance chain (backend half).

No /demo/reset anywhere.  One journey_id from create to accepted replan.
"""
import json, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
CHAIN = "D:/moodle/_v1922_work/rc_evidence/be_chain.json"
DB = "D:/moodle/_v1922_work/rc_evidence/_db/live.db"
T = []


def call(method, path, body=None, timeout=300, hdrs=()):
    a = ["curl", "-s", "-X", method, B + path, "-H", "Content-Type: application/json"]
    for h in hdrs:
        a += ["-H", h]
    if body is not None:
        a += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:300]}


def rec(step, route, resp, note=""):
    st = (resp.get("error") or {}).get("code") if isinstance(resp, dict) and "error" in resp else "OK"
    T.append({"step": step, "route": route, "status": st, "note": str(note)[:140]})


tv = call("POST", "/travelers", {"display_name": "厦门旅客", "timezone": "Asia/Shanghai", "locale": "zh-CN"})
journey = call("POST", "/journeys", {
    "traveler_id": tv["id"], "title": "厦门三天", "city_code": "CN-XIAMEN",
    "timezone": "Asia/Shanghai",
    "start_at": "2026-11-06T10:00:00+08:00", "end_at": "2026-11-08T20:00:00+08:00",
    "budget": {"amount_minor": 300000, "currency": "CNY"},
    "stay_budget": {"amount_minor": 100000, "currency": "CNY"},
    "party_size": 2, "occupancy": {"adults": 2, "rooms": 1},
    "arrival_anchor": {"at": "2026-11-06T10:00:00+08:00", "location": "厦门高崎国际机场"},
    "departure_anchor": {"at": "2026-11-08T20:00:00+08:00", "location": "厦门北站"}})
JID = journey["id"]
rec("create", "/journeys", journey, f"city={journey.get('city_code')} status={journey.get('status')}")
print("JID", JID, flush=True)

import sqlite3
def poi_ids():
    con = sqlite3.connect(DB)
    return [r[0] for r in con.execute(
        "select id from places where id like 'real-place-%' and city_code='CN-XIAMEN' order by id limit 6")]

for q in ["tourist attraction", "restaurant", "cafe", "museum", "park", "bar"]:
    if len(poi_ids()) >= 6:
        break
    for attempt in range(2):
        r = call("POST", f"/journeys/{JID}/real-city/discover",
                 {"query": q, "mode": "live", "limit": 6, "radius_m": 5000})
        n = len(r.get("candidates") or []) if isinstance(r, dict) else 0
        rec("discover", f"discover[{q}]", r, f"candidates={n} try={attempt+1}")
        print(f"  {q} -> {n}", flush=True)
        if n:
            break

ids = poi_ids()
rec("pois", "places", {"count": len(ids)}, f"{len(ids)} xiamen POIs")
print("POIs", len(ids), flush=True)
if len(ids) < 2:
    print("BLOCKED: not enough Xiamen POIs")
    json.dump({"journey_id": JID, "trace": T}, open(CHAIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    raise SystemExit(2)

gen = call("POST", f"/journeys/{JID}/plans/generate", {"place_ids": ids, "candidate_count": 3})
plans = gen if isinstance(gen, list) else []
rec("generate", "/plans/generate", gen, f"plans={len(plans)} stops={[len(p.get('activities') or []) for p in plans]}")
print("plans", len(plans), flush=True)
if not plans:
    print("BLOCKED: no plans", json.dumps(gen, ensure_ascii=False)[:200])
    json.dump({"journey_id": JID, "trace": T}, open(CHAIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    raise SystemExit(2)

sel = call("POST", f"/journeys/{JID}/plans/{plans[0]['id']}/select")
rec("select", f"/plans/{plans[0]['id'][:8]}/select", sel)
print("selected", plans[0]["id"][:8], flush=True)

st = call("POST", f"/journeys/{JID}/start")
rec("start", "/start", st, f"status={st.get('status') if isinstance(st, dict) else ''}")
print("start", st.get("status") if isinstance(st, dict) else st, flush=True)

# hotel capture + options
call("POST", f"/journeys/{JID}/stays/offers/capture")
stay = call("POST", f"/journeys/{JID}/stay-options/generate")
top = (stay.get("top_k") or []) if isinstance(stay, dict) else []
rec("stay", "/stay-options/generate", stay, f"options={len(top)}")
print("stay options", len(top), flush=True)
if top:
    hs = call("POST", f"/journeys/{JID}/stay-options/{top[0]['id']}/select")
    rec("stay-select", "/stay-options/{id}/select", hs)
    print("stay selected", (top[0].get("stay") or {}).get("property_name"), flush=True)

# disruption -> governed replan -> accept
exp = call("GET", f"/journeys/{JID}/experience")
acts = (exp.get("active_plan") or {}).get("activities") or []
interior = [a for a in acts if a.get("type") not in {"arrival", "departure"}]
if interior:
    ev = call("POST", f"/journeys/{JID}/events", {
        "event_type": "CLOSURE", "severity": "MAJOR",
        "affected_activity_id": interior[0]["id"], "provenance": "USER_REPORTED"})
    rec("event", "/events", ev, f"type=CLOSURE target={interior[0].get('title')}")
    prop = call("POST", f"/journeys/{JID}/replans", {"trigger_event_id": ev["id"]})
    rec("replan", "/replans", prop, f"status={prop.get('status')} preserved={prop.get('locked_commitments_preserved')}")
    print("proposal", (prop.get("id") or "ERR")[:8], prop.get("status"), flush=True)
    if prop.get("id"):
        vid = call("GET", f"/replans/{prop['id']}")
        diff = vid.get("diff") or {}
        rec("proposal-view", f"/replans/{prop['id'][:8]}", vid,
            f"removed={len(diff.get('removed') or [])} added={len(diff.get('added') or [])}")
        acc = call("POST", f"/replans/{prop['id']}/accept", None,
                   hdrs=(f"Idempotency-Key: acc-{prop['id'][:8]}",))
        rec("accept", f"/replans/{prop['id'][:8]}/accept", acc,
            f"status={(acc.get('proposal') or {}).get('status')}")
        print("accepted", (acc.get("proposal") or {}).get("status"), flush=True)

final = call("GET", f"/journeys/{JID}/experience")
fp = final.get("active_plan") or {}
rec("final", "/experience", final,
    f"plan={fp.get('id','')[:8]} stops={len(fp.get('activities') or [])} recovery={(final.get('recovery') or {}).get('state')}")
print("final plan", (fp.get("id") or "")[:8], "stops", len(fp.get("activities") or []), flush=True)

json.dump({
    "journey_id": JID, "city_code": journey.get("city_code"),
    "plan_ids": [p["id"] for p in plans],
    "selected_plan_id": plans[0]["id"],
    "plan_stops": [len(p.get("activities") or []) for p in plans],
    "stay_selected": (top[0].get("stay") or {}).get("property_name") if top else None,
    "final_plan_id": fp.get("id"),
    "final_stops": len(fp.get("activities") or []),
    "trace": T,
}, open(CHAIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
