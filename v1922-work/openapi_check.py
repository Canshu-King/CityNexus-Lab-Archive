"""OpenAPI path/schema guard against the checked-in contract."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("D:/moodle/CityNexus")
BACKEND = REPO / "backend"
PY = r"D:\moodle\CityNexus\.venv\Scripts\python.exe"
TMP = Path(tempfile.gettempdir())
DB = TMP / "v1922_openapi.db"
if DB.exists():
    DB.unlink()

CHILD = r'''
import json, os, sys
os.environ["CITYNEXUS_AI_ENABLED"] = "false"
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///" + sys.argv[1]
sys.path.insert(0, sys.argv[2])
from app.main import app
METHODS = {"get","post","put","patch","delete","options","head"}
runtime = set()
for route in app.routes:
    path = getattr(route, "path", "")
    if not (path.startswith("/api/v1/") or path == "/api/v1"):
        continue
    for method in getattr(route, "methods", set()) or set():
        runtime.add((path, method.upper()))
schema = None
for candidate in ("openapi.json", "contracts/openapi.json", "backend/openapi.json"):
    p = os.path.join(sys.argv[3], candidate)
    if os.path.exists(p):
        schema = json.load(open(p, encoding="utf-8"))
        break
print(json.dumps({
    "runtime_pairs": sorted(f"{m} {p}" for p, m in runtime),
    "schema": schema,
}))
'''

result = subprocess.run(
    [PY, "-c", CHILD, str(DB), str(BACKEND), str(REPO)],
    capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
)
if result.returncode != 0:
    print("CHILD FAILED", result.stderr[-2000:])
    raise SystemExit(1)
payload = json.loads(result.stdout.strip().splitlines()[-1])
runtime = payload["runtime_pairs"]
schema = payload["schema"]
print(f"runtime pairs = {len(runtime)}")
if schema is None:
    print("contract schema: NOT FOUND")
else:
    declared = set()
    for path, methods in (schema.get("paths") or {}).items():
        for method in methods:
            if method.lower() in {"get","post","put","patch","delete","options","head"}:
                declared.add((path, method.upper()))
    declared_pairs = sorted(f"{m} {p}" for p, m in declared)
    print(f"contract pairs = {len(declared_pairs)}")
    rset, dset = set(runtime), set(declared_pairs)
    missing = sorted(dset - rset)
    extra = sorted(rset - dset)
    print(f"missing = {len(missing)}")
    print(f"extra = {len(extra)}")
    for item in missing[:15]:
        print("  MISSING", item)
    for item in extra[:15]:
        print("  EXTRA", item)
    print("parity_ok =", not missing and not extra)
    for key in ("capabilit", "accessib", "evidence", "recovery", "replan"):
        hits = [p for p in (schema.get("paths") or {}) if key in p.lower()]
        if hits:
            print(f"paths containing {key!r}: {hits}")
