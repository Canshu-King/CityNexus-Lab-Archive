"""Copy the capability-relevant files from each snapshot into evidence/.

The snapshot trees themselves are deliberately NOT shipped in the deliverable
zip -- they are ~5 MB each and are 99% the main tree's own source, which the
reviewer already has.  What cannot be reconstructed from the main tree is the
*state at each timestamp*, so this script extracts the small set of files that
every finding in the round actually rests on:

    evidence/snapshot_watched/a/...
    evidence/snapshot_watched/b/...
    evidence/snapshot_watched/c/...

Together with evidence/snapshot_{a,b,c}.json (full per-file hashes) this is
enough to re-verify any claim without the bulk.

Usage:  python tools/v191_export_watched.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
EVID = LAB / "evidence"
OUT = EVID / "snapshot_watched"

# The files every capability finding in this round depends on, plus the two
# files that changed mid-round.
WATCHED = [
    "backend/app/capabilities.py",
    "backend/app/replanning/feasibility.py",
    "backend/app/main.py",
    "backend/app/services.py",
    "backend/app/stay_mobility.py",
    "backend/app/execution/traveler_twin.py",
    "backend/app/integrations/ai/semantic_compiler.py",
    "backend/app/replanning/protected_commitments.py",
    "backend/app/db/models.py",
    "backend/app/agent/mission.py",
    "contracts/openapi.yaml",
]


def sha256_16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> int:
    manifest: dict[str, dict] = {}
    for label in ("a", "b", "c"):
        snap = LAB / f"snapshot_{label}"
        rows: dict[str, dict] = {}
        for rel in WATCHED:
            src = snap / rel
            if not src.exists():
                rows[rel] = {"present": False}
                continue
            dest = OUT / label / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            rows[rel] = {
                "present": True,
                "bytes": src.stat().st_size,
                "sha256_16": sha256_16(src),
            }
        manifest[label] = rows
        present = sum(1 for r in rows.values() if r["present"])
        print(f"  {label}: {present}/{len(WATCHED)} files")

    # Cross-snapshot change table -- the compact form of "what moved when".
    changes: dict[str, dict] = {}
    for rel in WATCHED:
        hashes = {lbl: manifest[lbl][rel].get("sha256_16")
                  for lbl in ("a", "b", "c")}
        changes[rel] = {
            "a": hashes["a"], "b": hashes["b"], "c": hashes["c"],
            "a_to_b": "same" if hashes["a"] == hashes["b"] else "CHANGED",
            "b_to_c": "same" if hashes["b"] == hashes["c"] else "CHANGED",
        }

    (OUT / "MANIFEST.json").write_text(
        json.dumps({"watched": manifest, "changes": changes},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nwrote {OUT}")
    print("--- change table ---")
    for rel, row in changes.items():
        flag = "  " if row["a_to_b"] == row["b_to_c"] == "same" else "**"
        print(f"  {flag} {rel:<58} a->b {row['a_to_b']:<8} b->c {row['b_to_c']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
