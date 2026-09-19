"""P1 provider evidence scope: top-level keys and gate-level accessibility state."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/replanning/feasibility.py")
s = P.read_text(encoding="utf-8")

old = '''    keys = {
        "evidence_status",
        "status",
        "step_free",
        "wheelchair_access",
        "stairs",
        "stroller_accessible",
        "luggage_accessible",
    }
    result = {key: metadata[key] for key in keys if key in metadata}
    raw_tags = metadata.get("osm_tags") or metadata.get("tags")
    tags = normalize_osm_tags(raw_tags)
    if tags:
        result["osm_tags"] = tags
    return result or None'''

new = '''    # Top-level and nested forms must reach the evaluator identically.  The
    # whitelist previously dropped ``step_free_verified`` (so the same
    # assertion was honoured under ``tags`` but silently ignored at the top
    # level) and never projected route/highway/step-count evidence at all.
    keys = {
        "evidence_status",
        "status",
        "subject",
        "scope",
        "step_free",
        "step_free_verified",
        "route_step_free",
        "route_step_free_verified",
        "step_free_route",
        "wheelchair_access",
        "wheelchair",
        "stairs",
        "has_stairs",
        "steps",
        "step_count",
        "highway",
        "stroller_accessible",
        "luggage_accessible",
    }
    result = {key: metadata[key] for key in keys if key in metadata}
    raw_tags = metadata.get("osm_tags") or metadata.get("tags")
    tags = normalize_osm_tags(raw_tags)
    if tags:
        result["osm_tags"] = tags
    return result or None'''
assert old in s, "metadata whitelist not found"
s = s.replace(old, new, 1)

old2 = '''    metadata = _accessibility_metadata(record)
    state = evaluate_accessibility_requirement(code, metadata or {})
    if code in {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}:
        if state == "ACCESSIBILITY_VERIFIED":
            return []
        if state == "ACCESSIBILITY_CONFLICT":
            return [f"ACCESSIBILITY_CONFLICT:{location}"]
        return [
            f"ACCESSIBILITY_UNVERIFIED:{location}",
            f"NEEDS_LIVE_EVIDENCE:{location}",
        ]'''
new2 = '''    metadata = _accessibility_metadata(record)
    state = evaluate_accessibility_requirement(code, metadata or {})
    if code in {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}:
        if state == "ACCESSIBILITY_VERIFIED":
            return []
        if state == "ACCESSIBILITY_CONFLICT":
            return [f"ACCESSIBILITY_CONFLICT:{location}"]
        # Requirement-scoped evidence is authoritative; the legacy whole-record
        # view is consulted only as a second, never-lenient opinion.  Both must
        # agree that the place is verified before the gate accepts it.
        if accessibility_state(metadata or {}) == "ACCESSIBILITY_VERIFIED":
            return []
        return [
            f"ACCESSIBILITY_UNVERIFIED:{location}",
            f"NEEDS_LIVE_EVIDENCE:{location}",
        ]'''
assert old2 in s, "capability failure block not found"
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("feasibility metadata patched")
