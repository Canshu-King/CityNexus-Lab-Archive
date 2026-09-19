import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
chain = json.loads(open("D:/moodle/_v1922_work/rc_evidence/be_chain.json","rb").read().decode("utf-8"))
print("journey_id", chain["journey_id"])
print("proposal_id", chain.get("proposal_id"), "status", chain.get("proposal_status"))
print("final_plan_id", chain.get("final_plan_id"), "stops", chain.get("final_stops"))
print("diff removed", chain.get("diff_removed"))
print("diff added", chain.get("diff_added"))
