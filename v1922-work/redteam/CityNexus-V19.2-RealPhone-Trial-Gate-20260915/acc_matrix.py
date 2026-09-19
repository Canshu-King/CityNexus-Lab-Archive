"""V19.2.2 acceptance matrix: generate -> select -> start per anchor role."""

import io
import json
import os
import sys
from pathlib import Path

SNAP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("snapshot_d")
sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import v192_harness as H  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

CASES = [
    ("ARRIVAL", "ARRIVAL", None, "2026-10-10T12:30:00+08:00"),
    ("DEPARTURE", "DEPARTURE", None, "2026-10-10T12:30:00+08:00"),
    ("MID_TRIP", "MID_TRIP", "place-old-town", "2026-10-10T12:30:00+08:00"),
    ("CONTROL", None, None, None),
]

rows = []
for label, role, node, arrival in CASES:
    H.reset_demo()
    jid = H.DEMO_JOURNEY_ID
    safe = TestClient(H.app_main().app, raise_server_exceptions=False)
    row = {"case": label}
    if role is not None:
        reservation = H.c4_reservation(
            confirmation_ref=f"ACC-{role}-{node or 'synthetic'}",
            departure_at="2026-10-10T08:00:00+08:00",
            arrival_at=arrival,
            anchor_role=role,
            semantic_node_key=node,
        )
        imported = H.inbox_import(jid, reservation)
        row["import"] = imported.status_code
        confirmed = H.inbox_confirm(jid, imported.json()["id"])
        row["confirm"] = confirmed.status_code
        row["commitments"] = len(H.commitment_rows(jid))
    status, _body = H.generate_plans(jid)
    plans = H.list_plans(jid)
    row["generate"] = status
    row["plans"] = len(plans)
    if plans:
        selected = H.select_plan(jid, plans[0]["id"])
        row["select"] = selected.status_code
        if selected.status_code == 200:
            started = H.start_journey(jid)
            row["start"] = started.status_code
            row["journey_status"] = H.journey(jid).get("status")
    rows.append(row)
    print(json.dumps(row, ensure_ascii=False))

out = Path(os.environ.get("ACC_OUT", "evidence/acceptance_matrix_d.json"))
out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
print("written:", out)
