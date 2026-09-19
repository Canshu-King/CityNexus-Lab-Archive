import json, pathlib, subprocess, sys, shutil
ROOT = pathlib.Path(r"D:\moodle\_qoder_recovery_20260919\verify\wt_tip\backend")
PYEXE = r"D:\moodle\CityNexus\.venv\Scripts\python.exe"
MUTANTS = [
    ("J-ACK-RESOLVED", "app/planning/hard_recovery.py", 'event.status = "ACKNOWLEDGED"', 'event.status = "RESOLVED"'),
    ("J-STALE-CURSOR-FALLBACK", "app/operations/v9.py", "elif stale_cursor:", "elif False:"),
    ("J-PROTECTED-C4-DROPPED", "app/main.py", 'CommitmentModel.level == "C4_Anchored",', 'CommitmentModel.level == "C3_Guaranteed",'),
]
out = []
for mid, rel, old, new in MUTANTS:
    p = ROOT / rel
    original = p.read_text(encoding="utf-8")
    n = original.count(old)
    if n == 0:
        out.append({"id": mid, "verdict": "TARGET_MISSING"}); continue
    p.write_text(original.replace(old, new, 1), encoding="utf-8")
    try:
        r = subprocess.run([PYEXE, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--timeout=120"] if False else
                           [PYEXE, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l or "error" in l]
        failures = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
        out.append({"id": mid, "targets": n, "exit": r.returncode, "summary": tail[-1] if tail else r.stdout[-200:],
                    "first_failures": failures[:6],
                    "verdict": "KILLED" if failures else ("SURVIVED" if r.returncode == 0 else "NOISE")})
    finally:
        p.write_text(original, encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
pathlib.Path(r"D:\moodle\_qoder_recovery_20260919\raw\mutation_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
