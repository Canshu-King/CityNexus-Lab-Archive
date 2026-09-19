"""resolve_plan_anchors must only handle reservation anchors."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/planning/anchor_schedule.py")
s = P.read_text(encoding="utf-8")

old = '''        policy = _load(commitment.policy_json, {})
        role = normalise_role(policy.get("anchor_role"))
        raw_key = str(policy.get("semantic_key") or "").strip()'''
new = '''        policy = _load(commitment.policy_json, {})
        role = normalise_role(policy.get("anchor_role"))
        if not role:
            # A booking/order C4 anchor binds a concrete Activity, not a
            # planner node; it is protected through activity_id instead.
            continue
        raw_key = str(policy.get("semantic_key") or "").strip()'''
assert old in s, "resolve loop not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
