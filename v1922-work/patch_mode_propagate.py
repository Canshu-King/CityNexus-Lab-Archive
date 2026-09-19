"""Propagate travel mode into frozen facts at every capture site."""

from pathlib import Path

# snapshot_capture.py: the provider pair loop knows the requested pair but not
# the mode; capture the provider's own declared mode when it is single-mode.
P = Path("D:/moodle/CityNexus/backend/app/integrations/mobility/snapshot_capture.py")
s = P.read_text(encoding="utf-8")
old = '''            route_provenance=route_provenance,
            cost_provenance="CITYNEXUS_COST_ESTIMATE",
            time_basis=time_basis,
        )'''
new = '''            route_provenance=route_provenance,
            cost_provenance="CITYNEXUS_COST_ESTIMATE",
            time_basis=time_basis,
            mode=str(
                getattr(primary, "mode", None)
                or getattr(fallback, "mode", None)
                or ""
            ).upper()
            or None,
        )'''
assert old in s, "snapshot_capture fact not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")

# main.py: the replay matrix knows the chosen leg mode exactly.
P2 = Path("D:/moodle/CityNexus/backend/app/main.py")
s2 = P2.read_text(encoding="utf-8")
old2 = '''            time_basis=str(chosen.get("time_basis") or "VALHALLA_SOURCES_TO_TARGETS_CAPTURED_AT"),
            distance_m=(
                round(float(chosen["distance_km"]) * 1000)
                if chosen.get("distance_km") is not None
                else None
            ),
        )'''
new2 = '''            time_basis=str(chosen.get("time_basis") or "VALHALLA_SOURCES_TO_TARGETS_CAPTURED_AT"),
            distance_m=(
                round(float(chosen["distance_km"]) * 1000)
                if chosen.get("distance_km") is not None
                else None
            ),
            mode=str(chosen.get("mode") or "").upper() or None,
            walking_distance_m=(
                int(chosen["walking_distance_m"])
                if chosen.get("walking_distance_m") is not None
                else None
            ),
            walking_min=(
                int(chosen["walking_min"]) if chosen.get("walking_min") is not None else None
            ),
        )'''
assert old2 in s2, "main fact not found"
s2 = s2.replace(old2, new2, 1)
P2.write_text(s2, encoding="utf-8", newline="\n")
print("mode propagation patched")
