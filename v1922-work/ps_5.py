

sub(
    """    if not created:
        raise ValueError("No feasible plan candidates satisfy the journey constraints")""",
    """    if not created:
        if unresolved_anchors:
            raise ValueError(
                "C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved_anchors)))
            )
        detail = _anchor_block_reason(session, journey)
        raise ValueError(
            "No feasible plan candidates satisfy the journey constraints" + detail
        )""",
    "failure reason",
)


sub(
    """from app.replanning.protected_commitments import active_c4_hard_constraints""",
    """from app.planning.anchor_schedule import (
    CandidateActivity,
    resolve_plan_anchors,
    schedule_template_with_anchors,
)
from app.replanning.protected_commitments import active_c4_hard_constraints""",
    "imports",
)

P.write_text(s, encoding="utf-8", newline="\n")
print("services.py patched")
