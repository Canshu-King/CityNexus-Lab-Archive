"""Build the V19 deliverable zip deterministically.

Includes only what a reader needs: reports, patches, tests, tools and evidence.
Excludes the two repo snapshots, scratch git repos, throwaway SQLite files,
node_modules, server logs and internal scratch notes.

Usage:
    python tools/package_deliverable.py
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
OUT = LAB.parent / "CityNexus-WorkBuddy-V19-CapabilityRedTeam-20260915.zip"

ROOT_FILES = [
    "WORKBUDDY_V19_CAPABILITY_REDTEAM_REPORT.md",
    "ACCESSIBILITY_TRUTH_FINDINGS.md",
    "SEMANTIC_CAPABILITY_RESULTS.md",
    "PLANNER_REPLAN_CAPABILITY_RESULTS.md",
    "CAPABILITY_COMMITMENT_CONFLICTS.md",
    "CROSS_JOURNEY_SCOPE_RESULTS.md",
    "HERMES_CAPABILITY_AUTHORITY.md",
    "WEB_MOBILE_CAPABILITY_RESULTS.md",
    "CODEX_HANDOFF_AFTER_V19.md",
    "V19_FIX_DELTA.md",
    "BASELINE_SOURCE.txt",
    "BASELINE_SOURCE_CURRENT.txt",
]

DIRS = ["patches", "tests", "tools", "evidence"]

SKIP_NAMES = {"_delta_run.log", "_tiny.py"}
SKIP_SUFFIXES = (".db", ".pyc", ".log")


def wanted(rel: Path) -> bool:
    if rel.name in SKIP_NAMES:
        return False
    if rel.suffix in SKIP_SUFFIXES:
        return False
    if rel.parts and rel.parts[0] == "evidence" and rel.parts[1:2] in (
        ("screenshots",),
        ("screenshots_superseded",),
    ):
        return True
    return True


def main() -> int:
    members: list[tuple[Path, str]] = []
    for name in ROOT_FILES:
        p = LAB / name
        if p.exists():
            members.append((p, name))

    for d in DIRS:
        for p in sorted((LAB / d).rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(LAB)
            if not wanted(rel):
                continue
            members.append((p, str(rel).replace("\\", "/")))

    members.sort(key=lambda item: item[1])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path, arcname in members:
            zf.write(path, arcname)

    data = OUT.read_bytes()
    with zipfile.ZipFile(OUT) as zf:
        names = zf.namelist()
    banned = [
        n for n in names
        if n.endswith((".db", ".pyc")) or "node_modules" in n or n.endswith(".log")
    ]
    screenshots = [n for n in names if n.startswith("evidence/screenshots/")]

    # Credential scan over every text member (the scanner itself is excluded,
    # since it necessarily contains the patterns it searches for).
    hits = []
    patterns = ("sk-", "DEEPSEEK_API_KEY=", "CITYNEXUS_AI_API_KEY=", "Bearer ")
    for path, arcname in members:
        if arcname == "tools/package_deliverable.py":
            continue
        if path.suffix not in {".md", ".py", ".json", ".txt", ".jsonl", ".mjs", ".patch", ".yaml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in patterns:
            if pat in text:
                hits.append({"member": arcname, "pattern": pat})

    summary = {
        "zip": str(OUT),
        "members": len(names),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "screenshots": len(screenshots),
        "banned_members": banned,
        "credential_pattern_hits": hits,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
