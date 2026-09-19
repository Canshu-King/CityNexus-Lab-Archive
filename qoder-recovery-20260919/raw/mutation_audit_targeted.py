"""定向突变审计：把 Codex 记成 KILLED 但证据里"0 个测试跑到"的变异体重测。

判定规则修正（Codex 的 mutation_runner.py 把非零退出码一律当成杀掉，而 pytest
"没收集到测试" 的退出码正是 5，于是把"没测"读成"测过且杀掉了"）：

  collected == 0            -> NOT_RUN（未证明）
  有 FAILED                 -> KILLED
  退出 0 且 collected > 0   -> SURVIVED
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(sys.argv[1])
PY = pathlib.Path(sys.argv[2])
OUT = pathlib.Path(sys.argv[3])

GATE_FILES = [
    "tests/test_v1924_final_truth_gate.py",
    "tests/test_v1923_final_code_gate.py",
    "tests/test_v13_integrity.py",
    "tests/test_wp06_postgate_hardening_next.py",
    "tests/test_v12_authoritative_trip_execution.py",
    "tests/test_backend_connected_golden_contract.py",
    "tests/test_agent_runtime_gate.py",
    "tests/test_qoder_ack_resolution.py",
]

MUTANTS = [
    {
        "id": "J-ACK-RESOLVED",
        "path": "app/planning/hard_recovery.py",
        "old": 'event.status = "ACKNOWLEDGED"',
        "new": 'event.status = "RESOLVED"',
        "codex_claim": "KILLED (exit 5, 21 deselected -> 0 跑到)",
    },
    {
        "id": "J-PROTECTED-C4-DROPPED",
        "path": "app/main.py",
        "old": 'CommitmentModel.level == "C4_Anchored",',
        "new": 'CommitmentModel.level == "C3_Guaranteed",',
        "codex_claim": "KILLED (exit 4, gate 文件路径不存在 -> 从未运行)",
    },
]


def run(files: list[str]) -> dict:
    proc = subprocess.run(
        [str(PY), "-m", "pytest", "-q", "-p", "no:cacheprovider", *files],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = proc.stdout.splitlines()
    summary = next((l for l in reversed(lines) if "passed" in l or "failed" in l or "error" in l), "")
    import re

    nums = re.findall(r"(\d+) (?:passed|failed|skipped|error)", summary)
    total = sum(int(n) for n in nums)
    return {
        "exit": proc.returncode,
        "summary": summary[:160],
        "ran_anything": total > 0,
        "failures": [l for l in lines if l.startswith("FAILED")],
    }


existing = [f for f in GATE_FILES if (ROOT / "backend" / f).exists()]
report = {"gate_files_used": existing, "results": []}
for spec in MUTANTS:
    target = ROOT / "backend" / spec["path"]
    original = target.read_text(encoding="utf-8")
    hits = original.count(spec["old"])
    entry = {"id": spec["id"], "codex_claim": spec["codex_claim"], "mutation_sites": hits}
    try:
        baseline = run(existing)
        entry["clean_baseline"] = {
            k: baseline[k] for k in ("exit", "summary", "ran_anything")
        }
        if hits == 0:
            entry["verdict"] = "TARGET_MISSING"
        else:
            target.write_text(original.replace(spec["old"], spec["new"], 1), encoding="utf-8")
            mutated = run(existing)
            entry["mutated"] = {k: mutated[k] for k in ("exit", "summary", "ran_anything")}
            entry["mutated"]["first_failures"] = mutated["failures"][:8]
            if not mutated["ran_anything"]:
                entry["verdict"] = "NOT_RUN"
            elif mutated["failures"]:
                entry["verdict"] = "KILLED"
            elif mutated["exit"] == 0:
                entry["verdict"] = "SURVIVED"
            else:
                entry["verdict"] = "ERROR_ONLY"
    finally:
        target.write_text(original, encoding="utf-8")
    report["results"].append(entry)

OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=1))
