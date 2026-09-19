"""V19.1 OpenAPI drift check: runtime vs checked-in contract.

Uses the project's own parity definition (see tools/verify_openapi_parity.py):
compare ``(path, method)`` pairs, adding the ``/api/v1`` prefix to the formal
document's path keys.  Runs against the EAC reference lab, both snapshots and
the live main tree, each in a fresh interpreter so no module state leaks.

Read-only: the child never writes into any tree (PYTHONDONTWRITEBYTECODE=1) and
points CITYNEXUS_DATABASE_URL at a throwaway file in %TEMP%.

Output: evidence/openapi_drift.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
LAB = HERE.parents[1]
EAC = Path(r"D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915")
V191_LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
PY = r"D:\moodle\CityNexus\backend\.venv\Scripts\python.exe"
OUT = LAB / "evidence" / "openapi_drift.json"

TARGETS = {
    "eac_lab": EAC / "lab" / "runtime" / "backend",
    "snapshot_v192": LAB / "snapshot_a" / "backend",
    "snapshot_v191": V191_LAB / "snapshot_c" / "backend",
    "main_tree": Path(r"D:\moodle\CityNexus\backend"),
}

RELEVANT_KEYS = ("capabilit", "accessib", "evidence")

CHILD = r'''
import json, os, sys
backend, db = sys.argv[1], sys.argv[2]
os.environ["CITYNEXUS_AI_ENABLED"] = "false"
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///" + db
sys.path.insert(0, backend)
out = {"backend": backend}
try:
    from app.main import app
except Exception as exc:
    print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}))
    raise SystemExit(0)

METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
runtime = set()
for route in app.routes:
    path = getattr(route, "path", "")
    if not (path.startswith("/api/v1/") or path == "/api/v1"):
        continue
    for method in getattr(route, "methods", set()) or set():
        runtime.add((path, method.upper()))
out["runtime_pairs"] = sorted(f"{m} {p}" for p, m in runtime)
out["runtime_count"] = len(runtime)

# also expose the generated schema for the servers/prefix question
try:
    spec = app.openapi()
    out["schema_path_count"] = len(spec.get("paths") or {})
    out["schema_servers"] = spec.get("servers")
    out["schema_openapi"] = spec.get("openapi")
except Exception as exc:
    out["schema_error"] = f"{type(exc).__name__}: {exc}"

root = os.path.dirname(os.path.abspath(backend))
out["tree_root"] = root
contract = os.path.join(root, "contracts", "openapi.yaml")
out["contract_path"] = contract
out["contract_exists"] = os.path.exists(contract)
if out["contract_exists"]:
    try:
        import yaml
        doc = yaml.safe_load(open(contract, encoding="utf-8"))
    except Exception as exc:
        out["contract_error"] = f"{type(exc).__name__}: {exc}"
        doc = None
    if doc:
        out["contract_openapi"] = doc.get("openapi")
        out["contract_servers"] = doc.get("servers")
        formal = set()
        for path, item in (doc.get("paths") or {}).items():
            runtime_path = "/api/v1" + (path if path != "/" else "")
            for method in item:
                if str(method).lower() in METHODS:
                    formal.add((runtime_path, str(method).upper()))
        out["formal_pairs"] = sorted(f"{m} {p}" for p, m in formal)
        out["formal_count"] = len(formal)
        missing = sorted(f"{m} {p}" for p, m in (runtime - formal))
        extra = sorted(f"{m} {p}" for p, m in (formal - runtime))
        out["missing"] = missing
        out["extra"] = extra
        out["missing_count"] = len(missing)
        out["extra_count"] = len(extra)
        out["parity_ok"] = not missing and not extra
print(json.dumps(out))
'''


def run_target(name: str, backend: Path) -> dict:
    if not (backend / "app" / "main.py").exists():
        return {"error": "backend/app/main.py not found"}
    db = Path(tempfile.gettempdir()) / f"v191_openapi_{name}.db"
    env = dict(os.environ)
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "CITYNEXUS_AI_ENABLED": "false",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    })
    proc = subprocess.run(
        [PY, "-c", CHILD, str(backend), db.as_posix()],
        capture_output=True, cwd=str(LAB), env=env, timeout=420,
    )
    lines = proc.stdout.decode("utf-8", errors="replace").strip().splitlines()
    if not lines:
        return {"error": "no output",
                "stderr": proc.stderr.decode("utf-8", errors="replace")[-800:]}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        return {"error": f"bad json: {exc}", "raw": lines[-1][:400]}


def relevant(pairs: list[str]) -> list[str]:
    return sorted(p for p in pairs if any(k in p for k in RELEVANT_KEYS))


def main() -> int:
    result: dict = {"targets": {}}
    for name, backend in TARGETS.items():
        entry = run_target(name, backend)
        if "runtime_pairs" in entry:
            entry["runtime_relevant"] = relevant(entry["runtime_pairs"])
            entry["formal_relevant"] = relevant(entry.get("formal_pairs") or [])
            entry["relevant_missing"] = relevant(entry.get("missing") or [])
            entry["relevant_extra"] = relevant(entry.get("extra") or [])
        result["targets"][name] = entry

    # cross-target comparison of capability/accessibility surfaces
    rt = {n: set(e.get("runtime_relevant") or [])
          for n, e in result["targets"].items()}
    base = rt.get("main_tree", set())
    result["eac_only_relevant"] = sorted(rt.get("eac_lab", set()) - base)
    result["main_only_relevant"] = sorted(base - rt.get("eac_lab", set()))
    result["snapshot_vs_main_relevant_delta"] = sorted(
        rt.get("snapshot_b", set()) ^ base)

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"wrote {OUT}")
    for name, e in result["targets"].items():
        print(f"\n=== {name} ===")
        if e.get("error"):
            print(f"  ERROR {e['error']}")
            continue
        print(f"  runtime pairs: {e.get('runtime_count')} "
              f"(schema paths {e.get('schema_path_count')}, "
              f"schema servers {e.get('schema_servers')})")
        print(f"  contract: {e.get('contract_path')} exists={e.get('contract_exists')}")
        if e.get("contract_exists"):
            print(f"    contract servers: {e.get('contract_servers')}")
            print(f"    formal pairs: {e.get('formal_count')} "
                  f"missing={e.get('missing_count')} extra={e.get('extra_count')} "
                  f"parity_ok={e.get('parity_ok')}")
            print(f"    capability/accessibility missing from contract: "
                  f"{e.get('relevant_missing')}")
            if e.get("relevant_extra"):
                print(f"    capability/accessibility extra in contract: "
                      f"{e.get('relevant_extra')}")
    print("\n=== EAC-only capability/accessibility routes ===")
    print(json.dumps(result["eac_only_relevant"], ensure_ascii=False, indent=1))
    print("\n=== snapshot_b vs main_tree delta ===")
    print(json.dumps(result["snapshot_vs_main_relevant_delta"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
