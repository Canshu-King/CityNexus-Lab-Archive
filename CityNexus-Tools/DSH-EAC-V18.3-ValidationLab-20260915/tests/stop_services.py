"""Stop only the validation-lab backend/gateway processes recorded in lab-data."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LAB_DATA = Path(__file__).resolve().parents[1] / "lab-data"
PID_FILES = {
    "backend": LAB_DATA / "backend.pid",
    "hermes_gateway": LAB_DATA / "hermes_gateway.pid",
}


def _kill_tree(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
        timeout=30,
    )


def main() -> int:
    result = {}
    for name, pid_file in PID_FILES.items():
        if not pid_file.exists():
            result[name] = "no_pid_file"
            continue
        try:
            pid = int(pid_file.read_text().strip())
        except Exception:
            result[name] = "invalid_pid_file"
            continue
        _kill_tree(pid)
        pid_file.unlink(missing_ok=True)
        result[name] = {"stopped": pid}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
