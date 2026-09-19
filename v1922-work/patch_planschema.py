from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/schemas.py")
s = p.read_text(encoding="utf-8")

old = '''    activities: list[Activity]
    mobility_snapshot_id: str | None = None
    mobility_evidence: dict[str, Any] = Field(default_factory=dict)
    explanation: dict[str, Any] = Field(default_factory=dict)'''

new = '''    activities: list[Activity]
    mobility_snapshot_id: str | None = None
    mobility_evidence: dict[str, Any] = Field(default_factory=dict)
    explanation: dict[str, Any] = Field(default_factory=dict)
    # Stale/recompose-required projection.  A plan whose frozen evidence has
    # expired must not look like an ordinary current recommendation; selection
    # revalidation remains the final guard.
    stale: bool = False
    selectable: bool = True
    stale_reason: str | None = None'''

assert old in s, "PlanVersion schema not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("PlanVersion schema 已扩展")
