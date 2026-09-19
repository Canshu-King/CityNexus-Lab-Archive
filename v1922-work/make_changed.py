"""从真实 diff 生成 CHANGED_FILES.txt（对比 V19.2.1 基线）。"""

from pathlib import Path

BASE = Path("D:/moodle/_v1922_work/baseline")   # 纯净 V19.2.1
HEAD = Path("D:/moodle/CityNexus")              # 当前工作树

SKIP_DIRS = {"__pycache__", ".pytest_cache", "node_modules", ".venv", "dist",
             "dist-v19", "test-results", "playwright-report", ".ruff_cache",
             "storybook-static", "dev-dist", "reports"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".db", ".log", ".err", ".db-wal", ".db-shm"}

# 只关心这些子树
ROOTS = ["backend/app", "backend/tests", "backend/db", "contracts", "frontend/src",
         "frontend/package.json", "frontend/vite.config.ts", "tools", "data"]

def walk(root: Path):
    for rel in ROOTS:
        base = root / rel
        if base.is_file():
            yield base, rel
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
            yield p, p.relative_to(root).as_posix()

base_files = {rel: p for p, rel in walk(BASE)}
head_files = {rel: p for p, rel in walk(HEAD)}

added, modified, removed = [], [], []
for rel, p in sorted(head_files.items()):
    if rel not in base_files:
        added.append(rel)
    elif p.read_bytes() != base_files[rel].read_bytes():
        modified.append(rel)
for rel in sorted(base_files):
    if rel not in head_files:
        removed.append(rel)

lines = ["# V19.2.2 changed files (generated from the real working-tree diff vs V19.2.1)", ""]
lines.append(f"## Added ({len(added)})")
lines += [f"A  {r}" for r in added]
lines.append("")
lines.append(f"## Modified ({len(modified)})")
lines += [f"M  {r}" for r in modified]
lines.append("")
lines.append(f"## Removed ({len(removed)})")
lines += [f"D  {r}" for r in removed]
out = Path("D:/moodle/_v1922_work/CHANGED_FILES.txt")
out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines[:8]))
print(f"... added={len(added)} modified={len(modified)} removed={len(removed)}")
