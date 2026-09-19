import sys
sys.path.insert(0, "D:/moodle/CityNexus/backend")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import app.stay_mobility as sm
orig = sm._reschedule_with_carried
def traced(anchors, carried, arrival_at, departure_at, *, journey=None):
    print("=== ANCHORS ===")
    for n in anchors:
        print(f"  {n.role:12s} {n.start_at[5:16]}-{n.end_at[11:16]} key={n.key[:40]}")
    print("=== CARRIED ===")
    for n in carried:
        print(f"  {n.role:12s} {n.start_at[5:16]}-{n.end_at[11:16]} locked={int(bool(n.locked))} key={n.key[:40]}")
    return orig(anchors, carried, arrival_at, departure_at, journey=journey)
sm._reschedule_with_carried = traced
import pytest
sys.exit(pytest.main(["tests/test_snapshot_j_backend_truth_gaps.py::test_b1_luggage_drop_survives_when_required","-q","-p","no:cacheprovider","-s"]))
