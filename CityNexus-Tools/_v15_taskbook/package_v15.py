"""Package the V15 Night Lab workspace.

Excludes anything that is build output, someone else's working state, or scratch:

  * ``node_modules``      — 407 MB of borrowed dependencies, reproducible
  * ``.git``              — the isolated repo I initialised; not part of the deliverable
  * ``__pycache__``/``.pytest_cache``/``.ruff_cache`` — regenerated on every run
  * ``dist``/``dev-dist`` — build output
  * ``.playwright-cli``   — local browser session state
  * ``_v15_*``            — verification scratch trees and borrowed caches

The zip is written next to the workspace, not inside it, so a re-run never
packages its own output.
"""
from __future__ import annotations

import fnmatch
import os
import sys
import zipfile
from pathlib import Path

WORKSPACE = Path(
    "D:/moodle/CityNexus-Tools/WorkBuddy-V15-NightLab-20260914"
)
OUT = Path(
    "D:/moodle/CityNexus-Tools/CityNexus-WorkBuddy-V15-NightLab-20260914.zip"
)

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".pytest_cache", ".ruff_cache",
    "dist", "dev-dist", ".playwright-cli", ".mypy_cache", ".venv", "venv",
    "storybook-static", "test-results", "playwright-report",
}
SKIP_DIR_PREFIXES = (
    # Verification scratch trees and borrowed caches. `_v15_patch_verify*` holds
    # a throwaway copy of backend/; `_v15_partial_node_modules` is a stalled
    # dependency install that the sandbox delete-quota refuses to remove.
    "_v15_patch_verify",
    "_v15_partial_node_modules",
)
SKIP_PATTERNS = (
    "*.pyc", "*.pyo", "*.log.tmp", "*.orig", "*.rej",
)


def should_skip_dir(name: str) -> bool:
    if name in SKIP_DIRS:
        return True
    return any(name.startswith(prefix) for prefix in SKIP_DIR_PREFIXES)


def should_skip_file(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in SKIP_PATTERNS)


def main() -> int:
    if not WORKSPACE.is_dir():
        print(f"workspace missing: {WORKSPACE}", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    files = 0
    total_bytes = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, names in os.walk(WORKSPACE):
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]
            root_path = Path(root)
            for name in names:
                if should_skip_file(name):
                    continue
                path = root_path / name
                try:
                    if path.is_symlink() or not path.is_file():
                        continue
                    rel = path.relative_to(WORKSPACE).as_posix()
                    zf.write(path, rel)
                    files += 1
                    total_bytes += path.stat().st_size
                except OSError as exc:  # locked or vanished mid-walk
                    print(f"  skipped {path}: {exc}", file=sys.stderr)

    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"packaged {files} files ({total_bytes / 1024 / 1024:.1f} MB raw) "
          f"-> {OUT.name} ({size_mb:.1f} MB)")

    # Print the top-level inventory so the report can quote it.
    with zipfile.ZipFile(OUT) as zf:
        tops = sorted({n.split("/")[0] for n in zf.namelist()})
    print(f"top-level entries: {len(tops)}")
    for top in tops:
        print(f"  {top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
