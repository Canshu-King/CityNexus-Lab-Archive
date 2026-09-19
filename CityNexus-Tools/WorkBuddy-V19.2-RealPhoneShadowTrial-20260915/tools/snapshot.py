"""Take a read-only snapshot of the CityNexus main worktree.

Records the timestamp, per-file hashes/mtimes for the relevant subtrees, the
backend import status, the capability API symbol set, and the tests present.

Never writes to the main worktree.

Usage:
    python tools/snapshot.py A
    python tools/snapshot.py B
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Derive the lab root from this file's location (tools/ lives directly under it)
# so the same tool works for every round without hand-editing.
LAB = Path(__file__).resolve().parent.parent
MAIN = Path(r"D:\moodle\CityNexus")
VENV_PY = MAIN / "backend" / ".venv" / "Scripts" / "python.exe"
EVID = LAB / "evidence"

# Relative paths copied into the snapshot. Deliberately narrow: enough to run
# module-level and in-process contract tests, not a full mirror.
INCLUDE = [
    "backend/app",
    "backend/tests",
    "backend/db",
    "backend/data",
    "backend/pyproject.toml",
    "backend/uv.lock",
    "data",
    "frontend/src",
    "frontend/public",
    "frontend/package.json",
    "frontend/playwright.config.ts",
    "frontend/vite.config.ts",
    "frontend/index.html",
    "agent-mcp",
    "requirements",
    "contracts",
]

SKIP_DIRS = {"__pycache__", ".pytest_cache", "node_modules", ".venv", "dist", "dist-v19"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".db", ".log"}

# Files whose mtime we always record, whether or not they are copied.
WATCH = [
    "backend/app/capabilities.py",
    "backend/app/main.py",
    "backend/app/replanning/feasibility.py",
    "backend/app/replanning/mock_replan_engine.py",
    "backend/app/replanning/provider_snapshots.py",
    "backend/app/integrations/ai/semantic_compiler.py",
    "backend/app/integrations/ai/copilot_contract.py",
    "backend/app/execution/traveler_twin.py",
    "backend/app/agent/mission.py",
    "backend/app/agent/mission_plan.py",
    "backend/app/services.py",
    "backend/app/operations/v9.py",
    "backend/app/operations/__init__.py",
    "backend/app/replanning/protected_commitments.py",
    "backend/app/integrations/mobility/snapshot_capture.py",
    "backend/app/integrations/mobility/runtime.py",
    "backend/app/integrations/mock/providers.py",
    "backend/app/schemas.py",
    "backend/app/db/models.py",
    "backend/app/db/session.py",
    "backend/app/stay_mobility.py",
    "backend/db/schema.sql",
    "frontend/src/styles.css",
    "frontend/src/api/citynexus.ts",
    "frontend/src/app/v8Types.ts",
    "frontend/src/features/traveler-twin/TwinPanel.tsx",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_included(root: Path):
    for rel in INCLUDE:
        base = root / rel
        if base.is_file():
            yield base
            continue
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.suffix in SKIP_SUFFIXES:
                continue
            yield p


def copy_tree(dest: Path) -> tuple[int, int]:
    copied = 0
    total = 0
    for src in iter_included(MAIN):
        rel = src.relative_to(MAIN)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        out.write_bytes(data)
        copied += 1
        total += len(data)
    return copied, total


def import_status(backend: Path) -> dict:
    """Import app.main inside the snapshot, with bytecode writing disabled."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [str(VENV_PY), "-c", "import app.main; print('IMPORT_OK')"],
        cwd=str(backend),
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    tail = (proc.stderr or "").strip().splitlines()
    return {
        "ok": proc.returncode == 0 and "IMPORT_OK" in (proc.stdout or ""),
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "").strip()[:400],
        "stderr_tail": "\n".join(tail[-12:]),
    }


def capability_symbols(backend: Path) -> dict:
    """Defined vs imported-from names for app.capabilities across the backend."""
    mod = backend / "app" / "capabilities.py"
    if not mod.exists():
        return {"present": False}
    tree = ast.parse(mod.read_text(encoding="utf-8"))
    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)

    imported: dict[str, list[str]] = {}
    for p in backend.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            t = ast.parse(p.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(t):
            if isinstance(node, ast.ImportFrom) and node.module == "app.capabilities":
                for alias in node.names:
                    imported.setdefault(alias.name, []).append(
                        f"{p.relative_to(backend).as_posix()}:{node.lineno}"
                    )
    missing = {k: v for k, v in imported.items() if k not in defined}
    return {
        "present": True,
        "defined": sorted(defined),
        "imported_from_elsewhere": sorted(imported),
        "missing_symbols": missing,
        "bytes": mod.stat().st_size,
        "mtime": datetime.fromtimestamp(mod.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "sha256_16": sha256(mod)[:16],
    }


def main() -> int:
    label = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
    started = datetime.now()
    dest = LAB / f"snapshot_{label.lower()}"

    copied, total = copy_tree(dest)

    files = {}
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            files[p.relative_to(dest).as_posix()] = {
                "sha256_16": sha256(p)[:16],
                "bytes": p.stat().st_size,
            }

    watch = {}
    for rel in WATCH:
        p = MAIN / rel
        if p.exists():
            st = p.stat()
            watch[rel] = {
                "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "bytes": st.st_size,
                "sha256_16": sha256(p)[:16],
                "in_snapshot": (dest / rel).exists(),
            }

    tests_present = sorted(
        p.relative_to(dest / "backend").as_posix()
        for p in (dest / "backend" / "tests").glob("test_*.py")
    ) if (dest / "backend" / "tests").exists() else []

    record = {
        "label": f"Snapshot {label}",
        "taken_at": started.strftime("%Y-%m-%d %H:%M:%S"),
        "main_worktree": str(MAIN),
        "snapshot_dir": str(dest),
        "files_copied": copied,
        "bytes_copied": total,
        "file_index": files,
        "watched_files": watch,
        "import_status": import_status(dest / "backend"),
        "capability_symbols": capability_symbols(dest / "backend"),
        "backend_tests_present": tests_present,
        "include_list": INCLUDE,
        "took_seconds": round((datetime.now() - started).total_seconds(), 1),
    }

    EVID.mkdir(parents=True, exist_ok=True)
    out = EVID / f"snapshot_{label.lower()}.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({
        "label": record["label"],
        "taken_at": record["taken_at"],
        "files_copied": copied,
        "bytes_copied": total,
        "took_seconds": record["took_seconds"],
        "import_ok": record["import_status"]["ok"],
        "import_stderr_tail": record["import_status"]["stderr_tail"][-300:],
        "capabilities_present": record["capability_symbols"]["present"],
        "capabilities_bytes": record["capability_symbols"].get("bytes"),
        "capabilities_sha16": record["capability_symbols"].get("sha256_16"),
        "missing_symbols": record["capability_symbols"].get("missing_symbols"),
        "tests_present": len(tests_present),
        "written": str(out),
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
