"""Expire one PlanVersion's frozen mobility evidence in the lab database.

Usage: python expire_evidence.py <plan_version_id>
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent
DB = LAB / "evidence" / "_db" / "web_lab_d.db"
os.environ["CITYNEXUS_DATABASE_URL"] = f"sqlite:///{DB}"
os.environ["CITYNEXUS_AI_ENABLED"] = "false"
sys.path.insert(0, str(LAB / "snapshot_d" / "backend"))

from app.db.models import PlanVersion  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402

plan_id = sys.argv[1]
with SessionLocal() as session:
    plan = session.get(PlanVersion, plan_id)
    if plan is None:
        print("NO_PLAN")
        raise SystemExit(0)
    raw = json.loads(plan.mobility_evidence_json or "{}")
    raw["expires_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    plan.mobility_evidence_json = json.dumps(raw, ensure_ascii=False)
    session.commit()
    print(f"EXPIRED {plan.id}")
