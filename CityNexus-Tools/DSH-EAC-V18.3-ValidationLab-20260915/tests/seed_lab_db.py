"""Create and seed the isolated SQLite database used by the validation lab."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SNAPSHOT = WORKSPACE / "source-snapshot"
sys.path[:0] = [str(SNAPSHOT / "backend"), str(SNAPSHOT / "agent-mcp")]

DB_PATH = WORKSPACE / "lab-data" / "citynexus_lab.db"
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///" + str(DB_PATH).replace("\\", "/")
os.environ.setdefault("CITYNEXUS_ENV", "validation-lab")
os.environ.setdefault("CITYNEXUS_AI_ENABLED", "false")

for suffix in ("", "-shm", "-wal"):
    candidate = Path(str(DB_PATH) + suffix)
    if candidate.exists():
        candidate.unlink()

from app.db.session import SessionLocal, ensure_schema  # noqa: E402
from app.services import seed_demo  # noqa: E402

ensure_schema()
with SessionLocal() as session:
    result = seed_demo(session)
print(json.dumps({"seeded": result, "db": str(DB_PATH)}, ensure_ascii=False, sort_keys=True))
