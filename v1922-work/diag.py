import sys, json
sys.path.insert(0, "D:/moodle/CityNexus/backend")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import app.stay_mobility as sm
orig = sm._reschedule_with_carried

def traced(anchors, carried, arrival_at, departure_at, *, journey=None):
    print("=== ANCHORS ===")
    for n in anchors:
        print(f"  {n.role:12s} {n.start_at[5:16]} -> {n.end_at[5:16]} key={n.key[:44]} title={n.title[:26]}")
    print("=== CARRIED ===")
    for n in carried:
        print(f"  {n.role:12s} {n.start_at[5:16]} -> {n.end_at[5:16]} locked={int(bool(n.locked))} key={n.key[:44]} title={n.title[:26]}")
    return orig(anchors, carried, arrival_at, departure_at, journey=journey)

sm._reschedule_with_carried = traced
import pytest
sys.exit(pytest.main(["tests/test_v9_real_trip_operations.py::test_v9_flagship_real_world_trip_operations_e2e", "-q", "-p", "no:cacheprovider", "-s"]))
