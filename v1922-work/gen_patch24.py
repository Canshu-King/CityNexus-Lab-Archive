"""Generate the truthful V19.2.4 changed-file list and portable patch.

Comparison is content-based (CR-insensitive): a file whose only difference is
line endings is NOT a change.  Both sides of the diff are emitted as LF so the
patch applies to the explicitly LF-normalised declared baseline.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

BASE = Path("D:/moodle/_v1922_work/baseline_norm")   # declared baseline (V19.2.1, LF)
HEAD = Path("D:/moodle/CityNexus")

SKIP_DIRS = {"__pycache__", ".pytest_cache", "node_modules", ".venv", "dist",
             "dist-v19", "test-results", "playwright-report", ".ruff_cache",
             "storybook-static", "dev-dist"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".db", ".log", ".err", ".db-wal", ".db-shm"}
ROOTS = ["backend/app", "backend/tests", "backend/db", "contracts", "frontend/src"]


def walk(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for rel in ROOTS:
        base = root / rel
        if base.is_file():
            found[rel] = base
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
            found[p.relative_to(root).as_posix()] = p
    return found


def content(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


base_files = walk(BASE)
head_files = walk(HEAD)

added, modified, removed = [], [], []
for rel, p in sorted(head_files.items()):
    if rel not in base_files:
        added.append(rel)
    elif content(p) != content(base_files[rel]):
        modified.append(rel)
for rel in sorted(base_files):
    if rel not in head_files:
        removed.append(rel)

lines = [
    "# V19.2.4 changed files — generated from the real content diff against the",
    "# declared baseline (V19.2.1, explicitly normalised to LF).",
    "# Line-ending-only differences are NOT counted as changes.",
    "",
    f"## Added ({len(added)})",
]
lines += [f"A  {r}" for r in added]
lines += ["", f"## Modified ({len(modified)})"]
lines += [f"M  {r}" for r in modified]
lines += ["", f"## Removed ({len(removed)})"]
lines += [f"D  {r}" for r in removed]
Path("D:/moodle/_v1922_work/CHANGED_FILES.txt").write_text(
    "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
)

with tempfile.TemporaryDirectory() as tmp:
    tmpdir = Path(tmp)
    chunks = []
    for rel in added + modified:
        src = HEAD / rel
        base = BASE / rel
        normalized = tmpdir / rel.replace("/", "__")
        normalized.write_bytes(content(src))
        if rel in modified:
            base_norm = tmpdir / ("base__" + rel.replace("/", "__"))
            base_norm.write_bytes(content(base))
            proc = subprocess.run(
                ["diff", "-u", "--label", f"a/{rel}", "--label", f"b/{rel}",
                 str(base_norm), str(normalized)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        else:
            proc = subprocess.run(
                ["diff", "-u", "--label", "/dev/null", "--label", f"b/{rel}",
                 "/dev/null", str(normalized)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        chunks.append(proc.stdout)

patch = Path("D:/moodle/_v1922_work/V19_2_4_CODE.patch")
patch.write_text("".join(chunks), encoding="utf-8", newline="\n")

print(f"added={len(added)} modified={len(modified)} removed={len(removed)}")
print(f"patch={patch.stat().st_size} bytes")
for r in added:
    print("  A ", r)
for r in modified:
    print("  M ", r)
