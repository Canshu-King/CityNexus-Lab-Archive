"""V19 red-team isolated workspace setup.

Copies a READ-ONLY snapshot of the main CityNexus worktree into the isolated
lab directory.  The main tree D:\\moodle\\CityNexus is never written to.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

MAIN = Path(r"D:\moodle\CityNexus")
LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
REPO = LAB / "repo_copy"

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".playwright-cli", "dist", "build", "egg-info",
    ".mypy_cache", "coverage", "htmlcov",
}
EXCLUDE_SUFFIX = {".zip", ".db", ".db-wal", ".db-shm", ".pyc", ".pyo", ".7z", ".rar"}
EXCLUDE_NAMES = {"citynexus.db", "citynexus.db-wal", "citynexus.db-shm"}

TOP_LEVEL = [
    "backend/app",
    "backend/db",
    "backend/tests",
    "backend/pyproject.toml",
    "backend/requirements.txt",
    "backend/pytest.ini",
    "backend/conftest.py",
    "agent-mcp",
    "contracts",
    "evals",
    "frontend/src",
    "frontend/public",
    "frontend/index.html",
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
    "frontend/eslint.config.js",
    "scripts",
    "tools",
    "requirements",
    "domain-model",
    "use-cases",
    "docs",
    "data",
    "db",
]


def _skip(path: Path) -> bool:
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIX:
        return True
    if path.name in EXCLUDE_DIRS:
        return True
    if path.name.endswith(".egg-info"):
        return True
    return False


def copy_tree(src: Path, dst: Path, stats: dict) -> None:
    for root, dirs, files in os.walk(src):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not _skip(root_path / d)]
        rel = root_path.relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            source = root_path / name
            if _skip(source):
                continue
            target = target_dir / name
            try:
                shutil.copy2(source, target)
                stats["files"] += 1
                stats["bytes"] += source.stat().st_size
            except (OSError, PermissionError) as exc:
                stats["errors"].append(f"{source}: {exc}")


def main() -> int:
    if not MAIN.is_dir():
        print("MAIN worktree missing", file=sys.stderr)
        return 2
    started = time.time()
    stats = {"files": 0, "bytes": 0, "errors": []}
    if REPO.exists():
        shutil.rmtree(REPO, ignore_errors=True)
    REPO.mkdir(parents=True, exist_ok=True)

    for rel in TOP_LEVEL:
        source = MAIN / rel
        if not source.exists():
            stats["errors"].append(f"MISSING_SOURCE {rel}")
            continue
        if source.is_dir():
            copy_tree(source, REPO / rel, stats)
        else:
            target = REPO / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            stats["files"] += 1
            stats["bytes"] += source.stat().st_size

    # record the exact baseline revision for provenance
    head = ""
    try:
        head = (MAIN / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        head = "UNKNOWN"
    (LAB / "BASELINE_SOURCE.txt").write_text(
        f"source={MAIN}\nhead={head}\ncopied_at={time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
        f"files={stats['files']}\nbytes={stats['bytes']}\n",
        encoding="utf-8",
    )
    print(f"files={stats['files']} bytes={stats['bytes']} "
          f"mb={stats['bytes']/1048576:.1f} secs={time.time()-started:.1f}")
    for err in stats["errors"][:30]:
        print("ERR", err)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
