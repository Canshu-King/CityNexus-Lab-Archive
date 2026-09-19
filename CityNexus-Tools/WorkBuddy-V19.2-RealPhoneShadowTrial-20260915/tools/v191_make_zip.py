"""Build the round deliverable zip.

Output: D:\\moodle\\CityNexus-Tools\\CityNexus-WorkBuddy-V19.1-ConvergenceRedTeam-20260915.zip

Included: every report, the evidence tree, both patches, the tooling, the test
sources, the two briefs, and the fixed-file scratch used to generate the
low-conflict patch.

Excluded on purpose:
  snapshot_a/ snapshot_b/ snapshot_c/   ~5 MB each, 99% a copy of the main tree;
                                        reproducible with tools/snapshot.py, and
                                        the parts that matter are shipped as
                                        evidence/snapshot_watched/ + the three
                                        evidence/snapshot_*.json manifests
  _fixescratch/snapshot_fix/            scratch copy used only to run the fixed
                                        module once
  evidence/_db/                         throwaway SQLite files
  __pycache__/ *.pyc

Usage:  python tools/v191_make_zip.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
OUT = LAB.parent / "CityNexus-WorkBuddy-V19.1-ConvergenceRedTeam-20260915.zip"

EXCLUDE_DIRS = {
    "snapshot_a", "snapshot_b", "snapshot_c",
    "_db", "__pycache__", ".pytest_cache", "node_modules", "snapshot_fix",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".db", ".db-journal", ".db-wal", ".db-shm"}


def wanted(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return path.is_file()


def main() -> int:
    files = sorted(p for p in LAB.rglob("*") if wanted(p, LAB))
    if OUT.exists():
        OUT.unlink()
    # The archive's single top-level folder carries the zip's own name, so an
    # unpacked tree and the zip are recognisably the same artefact.
    root = OUT.stem
    total = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            arc = Path(root) / path.relative_to(LAB)
            zf.write(path, arc.as_posix())
            total += path.stat().st_size

    size = OUT.stat().st_size
    print(f"wrote {OUT}")
    print(f"  files      : {len(files)}")
    print(f"  raw bytes  : {total:,}")
    print(f"  zip bytes  : {size:,}  ({size / 1_048_576:.1f} MiB)")

    top: dict[str, int] = {}
    for path in files:
        rel = path.relative_to(LAB)
        key = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        top[key] = top.get(key, 0) + 1
    print("  contents   :")
    for key, count in sorted(top.items()):
        print(f"    {key:<28} {count:>4} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
