import sys
sys.path.insert(0, "D:/moodle/CityNexus/backend")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import app.stay_mobility as sm
orig = sm._reschedule_with_carried
def traced(anchors, carried, arrival_at, departure_at, *, journey=None):
    print("=== CARRIED ===")
    for n in carried:
        print(f"  {n.role:12s} {n.start_at[5:16]}-{n.end_at[11:16]} locked={int(bool(n.locked))} key={n.key[:38]}")
    print("=== ANCHORS ===")
    for n in anchors:
        print(f"  {n.role:12s} {n.start_at[5:16]}-{n.end_at[11:16]} key={n.key[:38]}")
    print("--- travel between consecutive pinned ---")
    prev=None
    for n in sorted(anchors, key=lambda x: x.start_at):
        if prev is not None:
            try:
                m = sm._travel_minutes(prev, n, journey=journey)
            except Exception as e:
                m = f"ERR {e}"
            print(f"  {prev.role:12s} -> {n.role:12s} = {m} min")
        prev = n
    return orig(anchors, carried, arrival_at, departure_at, journey=journey)
sm._reschedule_with_carried = traced
import pytest
sys.exit(pytest.main(["tests/test_v9_real_trip_operations.py::test_v9_flagship_real_world_trip_operations_e2e","-q","-p","no:cacheprovider","-s"]))
