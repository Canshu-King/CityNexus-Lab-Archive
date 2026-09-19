from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone

TREE = os.environ.get("CITYNEXUS_TREE")
if not TREE:
    raise SystemExit("CITYNEXUS_TREE must point to backend")
sys.path.insert(0, TREE)

from app.replanning.feasibility import FeasibilityActivity, FeasibilityContext, evaluate_feasibility
from app.replanning.provider_snapshots import MobilitySnapshot

TZ = timezone.utc
DAY = datetime(2026, 9, 16, tzinfo=TZ)
def at(h, m=0): return DAY.replace(hour=h, minute=m)
OPEN = json.dumps({"status":"NORMALIZED","open":"00:00","close":"23:59"})
def place(pid):
    return {"id":pid,"city_code":"CITY-DELTA","status":"available",
            "metadata_json":json.dumps({"available":True}),"opening_hours_json":OPEN}
def lock(pid, when, boundary, role):
    p={"place_id":pid,"start_at":when.isoformat(),"time_boundary":boundary}
    if role is not None: p["anchor_role"]=role
    return {"kind":"HARD","category":"commitment","rule_code":"LOCKED_COMMITMENT",
            "active":True,"params_json":json.dumps(p)}
def act(pid, start, end):
    return FeasibilityActivity(key=pid,place_id=pid,start_at=start,end_at=end,
        cost_minor=0,currency="EUR",metadata={"semantic_key":pid})
def ctx(constraints, ids):
    snap=MobilitySnapshot.from_minutes(
        source_provider_key="v1925-probe",
        minutes={(a,b):0 for a in ids for b in ids if a!=b},
        captured_at="2026-09-15T00:00:00+00:00")
    return FeasibilityContext(journey_id="J",city_code="CITY-DELTA",
        journey_start=at(9),journey_end=at(19),budget_amount_minor=1000000,
        budget_currency="EUR",constraints=tuple(constraints),
        places={i:place(i) for i in ids},services={},mobility_provider=snap,
        plan_currency="EUR")

A,M,D,B="arrival","mid","departure","booking"
cases=[]
def run(name,constraints,acts,expected):
    ids=sorted({x.place_id for x in acts if x.place_id})
    r=evaluate_feasibility(ctx(constraints,ids),acts)
    cases.append({"case":name,"passed":r.passed,"expected":expected,
                  "failures":list(r.failures),"verdict":"PASS" if r.passed==expected else "FAIL"})

run("mid_before_arrival",
    [lock(A,at(12,30),"START","ARRIVAL"),lock(M,at(10),"START","MID_TRIP")],
    [act(M,at(10),at(11)),act(A,at(12,30),at(12,50))],False)
run("mid_after_departure",
    [lock(D,at(15,30),"END","DEPARTURE"),lock(M,at(17),"START","MID_TRIP")],
    [act(D,at(15,10),at(15,30)),act(M,at(17),at(18))],False)
run("roleless_before_arrival",
    [lock(A,at(12,30),"START","ARRIVAL"),lock(B,at(10),"START",None)],
    [act(B,at(10),at(11)),act(A,at(12,30),at(12,50))],False)
run("mid_inside",
    [lock(A,at(10),"START","ARRIVAL"),lock(M,at(13),"START","MID_TRIP"),lock(D,at(17),"END","DEPARTURE")],
    [act(A,at(10),at(10,20)),act(M,at(13),at(14)),act(D,at(16,40),at(17))],True)
run("roleless_inside",
    [lock(A,at(10),"START","ARRIVAL"),lock(B,at(13),"START",None),lock(D,at(17),"END","DEPARTURE")],
    [act(A,at(10),at(10,20)),act(B,at(13),at(14)),act(D,at(16,40),at(17))],True)

print(json.dumps(cases, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(x["verdict"]=="PASS" for x in cases) else 2)
