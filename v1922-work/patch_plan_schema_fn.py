from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/services.py")
s = p.read_text(encoding="utf-8")

old = '''    breakdown = _plan_score_breakdown(item)
    return PlanSchema('''
new = '''    breakdown = _plan_score_breakdown(item)
    # Stale/recompose-required projection: an expired or evidence-less plan is
    # flagged so the API and UI never present it as a current recommendation.
    stale, stale_reason = _plan_staleness(item)
    return PlanSchema('''
assert old in s, "plan_schema return not found"
s = s.replace(old, new, 1)

old2 = '''        mobility_evidence=json.loads(item.mobility_evidence_json or "{}"),
        explanation=json.loads(item.explanation_json or "{}"),
    )'''
new2 = '''        mobility_evidence=json.loads(item.mobility_evidence_json or "{}"),
        explanation=json.loads(item.explanation_json or "{}"),
        stale=stale,
        selectable=not stale,
        stale_reason=stale_reason,
    )'''
assert old2 in s, "plan_schema tail not found"
s = s.replace(old2, new2, 1)

helper = '''def _plan_staleness(item: PlanVersion) -> tuple[bool, str | None]:
    """Whether a plan's frozen provider evidence makes it unusable as-is.

    This is a *projection* only; ``select`` revalidation remains the authority.
    """

    try:
        evidence = json.loads(item.mobility_evidence_json or "{}")
    except json.JSONDecodeError:
        return True, "STALE_RECOMPOSE_REQUIRED: mobility evidence is not readable"
    if not isinstance(evidence, dict) or not evidence.get("snapshot_id"):
        return True, "STALE_RECOMPOSE_REQUIRED: no frozen provider evidence"
    expires_at = evidence.get("expires_at")
    if expires_at:
        try:
            if datetime.fromisoformat(str(expires_at)) <= datetime.now(timezone.utc):
                return True, "STALE_RECOMPOSE_REQUIRED: frozen provider evidence expired"
        except ValueError:
            return True, "STALE_RECOMPOSE_REQUIRED: evidence timestamp invalid"
    return False, None


def plan_schema(session: Session, item: PlanVersion) -> PlanSchema:'''
s = s.replace("def plan_schema(session: Session, item: PlanVersion) -> PlanSchema:", helper, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("plan_schema 已加入陈旧投影")
