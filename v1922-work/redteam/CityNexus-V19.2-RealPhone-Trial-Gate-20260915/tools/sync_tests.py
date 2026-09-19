"""Copy the lab's test/probe sources into a snapshot so the SAME file runs on A and B.

    python tools/sync_tests.py A
    python tools/sync_tests.py B

The harness self-locates (HERE.parents[2] == snapshot root), so an identical byte
stream behaves identically in every snapshot.  Nothing outside the snapshot is written.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
TESTS = LAB / "tests"


def main() -> int:
    label = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
    dest = LAB / f"snapshot_{label.lower()}" / "backend" / "tests"
    if not dest.is_dir():
        print(f"no such snapshot test dir: {dest}")
        return 1
    rows = []
    for src in sorted(TESTS.glob("*.py")):
        target = dest / src.name
        shutil.copy2(src, target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()[:12]
        rows.append((src.name, digest))
    print(f"synced {len(rows)} file(s) -> {dest}")
    for name, digest in rows:
        print(f"  {name:<48} {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
