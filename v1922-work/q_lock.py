import sys, os, json, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/moodle/CityNexus/backend")
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///D:/moodle/_v1922_work/fc_evidence/_db/live.db"
from app.db.session import SessionLocal
from app.db.models import Journey, Commitment, PlanVersion, Activity
from sqlalchemy import select
from app.replanning.protected_commitments import active_c4_hard_constraints
from app.replanning.feasibility import _locked_commitment_specs, _minutes_from_start
from datetime import datetime

J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
with SessionLocal() as s:
    j = s.get(Journey, J)
    rows = s.scalars(select(Commitment).where(Commitment.journey_id == J, Commitment.status=="ACTIVE")).all()
    cons = active_c4_hard_constraints(rows)
    print("constraints:", len(cons))
    for c in cons:
        print("  ", c["rule_code"], json.dumps(c["params"], ensure_ascii=False)[:220])
    hs = [(c["kind"], c["category"], c["rule_code"], c["params"]) for c in cons]
    specs = _locked_commitment_specs(hs, journey_start=datetime.fromisoformat(j.start_at))
    print("--- specs ---")
    for commitment, role in specs:
        print("  role=", role, "| key=", str(commitment.activity_key)[-28:], "| start_min=", commitment.start_min, "| boundary=", commitment.time_boundary)
