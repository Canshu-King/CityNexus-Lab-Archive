from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    journey = require(session, Journey, str(journey_id), "Journey")
    request = payload or GeneratePlansRequest()
    planning_mode = request.planning_mode or journey.planning_mode
    try:
        plans = generate_plans(
            session,
            journey,
            planning_mode,
            request.candidate_count,
            place_ids=request.place_ids,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return [plan_schema(session, plan) for plan in plans]'''

new = '''    journey = require(session, Journey, str(journey_id), "Journey")
    request = payload or GeneratePlansRequest()
    planning_mode = request.planning_mode or journey.planning_mode
    try:
        plans = generate_plans(
            session,
            journey,
            planning_mode,
            request.candidate_count,
            place_ids=request.place_ids,
        )
    except ValueError as exc:
        # A recovery replan that yields nothing is a *durable fact*, not just a
        # failed request.  Persist it so the no-alternative state is real and
        # survives a reload.
        record_replan_outcome(
            session,
            journey,
            feasible_candidate_ids=[],
            failures=[str(exc)],
        )
        session.commit()
        raise HTTPException(422, str(exc)) from exc
    # Candidates that survived the deterministic gate are the only ones exposed.
    feasible_ids = [plan.id for plan in plans]
    record_replan_outcome(
        session,
        journey,
        feasible_candidate_ids=feasible_ids,
    )
    session.commit()
    return [plan_schema(session, plan) for plan in plans]'''
assert old in s, "generate endpoint not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("generate 端点已持久化 replan 结果")
