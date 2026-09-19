import importlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\moodle\CityNexus-Tools")
VENV = ROOT / ".venv"
REPO = ROOT / "external" / "hiung-skills"
OUT = ROOT / "installation-report.json"


def command(args, cwd=None):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=20)
        return {"returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def module_version(name):
    try:
        mod = importlib.import_module(name)
        return getattr(mod, "__version__", "imported")
    except Exception as exc:
        return f"unavailable: {type(exc).__name__}: {exc}"


def main():
    packages = {name: module_version(name) for name in ("vsdx", "win32com", "yaml", "pytest")}
    git = command(["git", "-C", str(REPO), "rev-parse", "HEAD"])
    log = command(["git", "-C", str(REPO), "log", "-1", "--oneline"])
    expected = [
        "visio/SKILL.md",
        "visio/scripts/check_cross.py",
        "visio/scripts/verify_topology.py",
        "visio/scripts/verify_label_spacing.py",
        "visio/scripts/deoverlap.py",
        "visio/scripts/New-VisioDiagram.py",
    ]
    files = {p: (REPO / p).is_file() for p in expected}
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "external-tools-only",
        "constraints": {
            "rc6_generated": False,
            "phase1_generated": False,
            "part2_generated": False,
            "renderer_modified": False,
            "auto_commit": False,
        },
        "visio_powershell": {
            "module": "Visio",
            "version": "4.7.2",
            "smoke": "passed",
            "artifact": str(ROOT / "smoke" / "visioautomation-smoke.vsdx"),
        },
        "python": {
            "executable": str(VENV / "Scripts" / "python.exe"),
            "packages": packages,
            "requirements": ["vsdx==0.6.1", "pywin32", "PyYAML", "pytest"],
        },
        "vsdx_reader": {
            "script": str(ROOT / "smoke" / "test_vsdx_reader.py"),
            "result": str(ROOT / "smoke" / "vsdx-reader-result.json"),
            "status": "passed",
        },
        "hiung_skills": {
            "url": "https://github.com/hiung/skills.git",
            "path": str(REPO),
            "clone_status": "incomplete-no-HEAD-network-timeout",
            "rev_parse": git,
            "last_commit": log,
            "expected_sparse_files": files,
            "skill_read": False,
            "qa_import_scan": "not_run-repository-unavailable",
        },
        "notes": [
            "No mirror or alternate source was used.",
            "Existing CityNexus files were preserved; no cleanup or reset was performed.",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
