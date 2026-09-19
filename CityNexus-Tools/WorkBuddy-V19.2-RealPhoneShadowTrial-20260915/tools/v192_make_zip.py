"""Build the round deliverable zip.

Output: D:\\moodle\\CityNexus-Tools\\CityNexus-V19.2-RealPhone-Trial-Gate-20260915.zip

Included: every report, the evidence tree, this round's patch, the tooling, the
test sources and the road-prep brief.

Excluded on purpose:
  snapshot_a/ snapshot_b/   ~5 MB each, 99% a copy of the main tree; reproducible
                            with tools/snapshot.py, and the parts that matter are
                            shipped as evidence/snapshot_*.json
  _scratch/                 throwaway git repos used only for apply-checks
  _v192_brief/              leftover V19.1 output contract, superseded by the
                            V19.2 brief in _brief/
  evidence/_db/             throwaway SQLite files
  *.log                     runtime logs of the lab servers
  __pycache__/ *.pyc

Usage:  python tools/v192_make_zip.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
OUT = LAB.parent / "CityNexus-V19.2-RealPhone-Trial-Gate-20260915.zip"

EXCLUDE_DIRS = {
    "snapshot_a",
    "snapshot_b",
    "_scratch",
    "_v192_brief",
    "_db",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".db", ".db-journal", ".db-wal", ".db-shm", ".log"}


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

    # Contract checks: one top-level folder named after the zip, and no stale
    # release-status files from an earlier round.
    with zipfile.ZipFile(OUT) as zf:
        names = zf.namelist()
    roots = {n.split("/", 1)[0] for n in names}
    assert roots == {root}, f"expected a single top-level folder {root!r}, got {sorted(roots)}"
    stale = [
        n
        for n in names
        if n.split("/")[-1]
        in {"CURRENT_STATUS.md", "TEST_RESULTS.md", "NEXT_RECOMMENDATION.md", "PACKAGE-MANIFEST.json"}
    ]
    print(f"  top folder : {sorted(roots)[0]}")
    print(f"  stale files: {stale or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
