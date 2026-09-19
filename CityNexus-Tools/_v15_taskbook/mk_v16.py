"""Create the V16 Real-User Lab workspace.

V16 builds on V15 rather than on the V14 baseline, deliberately: the V15 work
produced a test suite (semantic contract, authority boundary, cross-city
genericity, minimal-pair contrast) that is exactly the safety net needed before
changing product behaviour. Carrying it forward means every V16 fix lands against
a regression suite instead of against nothing.

What is carried over: the whole V15 workspace.
What is dropped: build outputs, the V15 git repo, the V15 database, the V15
browser-trial evidence (V16 regenerates its own), and anything the V15 run left
as scratch.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

SRC = Path("D:/moodle/CityNexus-Tools/WorkBuddy-V15-NightLab-20260914")
DST = Path("D:/moodle/CityNexus-Tools/WorkBuddy-V16-RealUserLab-20260914")

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".pytest_cache", ".ruff_cache",
    "dist", "dev-dist", ".mypy_cache", ".venv", "venv", "test-results",
    "playwright-report", "_v15_trial",
}
SKIP_FILES = {"citynexus.db", "citynexus.db-journal", "citynexus.db-wal"}
SKIP_SUFFIX = (".pyc", ".pyo")


def main() -> int:
    if not SRC.is_dir():
        print(f"source missing: {SRC}", file=sys.stderr)
        return 1
    if DST.exists():
        print(f"destination already exists: {DST}", file=sys.stderr)
        return 1

    dirs = files = 0
    for root, subdirs, names in os.walk(SRC):
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
        rel = Path(root).relative_to(SRC)
        (DST / rel).mkdir(parents=True, exist_ok=True)
        dirs += 1
        for name in names:
            if name in SKIP_FILES or name.endswith(SKIP_SUFFIX):
                continue
            src_file = Path(root) / name
            if src_file.is_symlink() or not src_file.is_file():
                continue
            try:
                shutil.copy2(src_file, DST / rel / name)
                files += 1
            except OSError as exc:
                print(f"  skipped {src_file}: {exc}", file=sys.stderr)

    # V15 evidence described the V15 run; V16 must not inherit it as if it were
    # its own measurement.
    ev = DST / "evidence"
    if ev.is_dir():
        for name in list(ev.iterdir()):
            if name.is_dir():
                continue
            name.rename(ev / f"_v15_{name.name}")
        print("V15 evidence files renamed with a _v15_ prefix")

    print(f"copied {files} files in {dirs} directories -> {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
