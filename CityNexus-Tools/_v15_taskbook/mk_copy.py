"""Create isolated V15 baseline copy without polluting the Codex main worktree."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

SRC = Path(r"D:\moodle\_v14_trial_release_stage_20260914_012126\CityNexus")
DST = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V15-NightLab-20260914")

SKIP_DIRS = {
    "node_modules", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    "dev-dist", "dist", "egg-info", ".git", "review", "visio", "visio-renderer",
    "visio-spec", "_incoming_post_goal_vertical_slice_prep_20260910",
}
# Only skip the big replay/junk dirs at any level
SKIP_PREFIX = ("_fresh_", "_incoming_", "_package_", "_v5_", "_v6_", "_implementation_blueprint")
SKIP_SUFFIX = (".pyc", ".pyo")


def skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or name.startswith(SKIP_PREFIX)


def main() -> int:
    if DST.exists():
        # clear only our own target
        for child in DST.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    DST.mkdir(parents=True, exist_ok=True)
    n_files = 0
    n_bytes = 0
    for src_dir, dirnames, filenames in __import__("os").walk(SRC):
        rel = Path(src_dir).relative_to(SRC)
        dirnames[:] = [d for d in dirnames if not skip_dir(d)]
        out_dir = DST / rel
        out_dir.mkdir(parents=True, exist_ok=True)
        for fn in filenames:
            if fn.endswith(SKIP_SUFFIX):
                continue
            s = Path(src_dir) / fn
            d = out_dir / fn
            try:
                shutil.copy2(s, d)
                n_files += 1
                n_bytes += s.stat().st_size
            except OSError as exc:
                print("skip", s, exc, file=sys.stderr)
    print(f"copied {n_files} files, {n_bytes/1e6:.1f} MB -> {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
