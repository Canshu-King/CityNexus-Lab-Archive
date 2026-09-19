"""Start the isolated native Hermes gateway on 127.0.0.1:8653.

The credential is inherited only by this child process. The launcher never
prints it and never writes it into the lab workspace.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab_common import (  # noqa: E402
    HERMES_AGENT,
    HERMES_HOME,
    HERMES_PORT,
    HERMES_RUNTIME_PY,
    LAB_DATA,
    LOGS,
    get_lab_api_key,
    hermes_env,
    primary_deepseek_key,
)

PID_FILE = LAB_DATA / "hermes_gateway.pid"
RUNNER = Path(__file__).resolve().with_name("hermes_runner.py")


def _alive(pid: int) -> bool:
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
        return str(pid) in out
    except Exception:
        return False


def _probe() -> bool:
    key = get_lab_api_key()
    request = urllib.request.Request(
        f"http://127.0.0.1:{HERMES_PORT}/v1/capabilities",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            data = response.read()
            return response.status == 200 and b"capabilities" in data.lower()
    except Exception:
        return False


def main() -> int:
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if _alive(pid):
                print(json.dumps({"status": "already_running", "pid": pid}))
                return 0
        except Exception:
            pass
    LOGS.mkdir(parents=True, exist_ok=True)
    key = primary_deepseek_key()
    env = hermes_env(deepseek_key=key)
    env["PYTHONPATH"] = str(HERMES_AGENT)
    out = open(LOGS / "hermes.out.log", "ab", buffering=0)
    err = open(LOGS / "hermes.err.log", "ab", buffering=0)
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
        subprocess, "DETACHED_PROCESS", 0
    )
    process = subprocess.Popen(
        [
            str(HERMES_RUNTIME_PY),
            str(RUNNER),
            "gateway",
            "run",
        ],
        cwd=str(HERMES_AGENT),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=err,
        creationflags=creationflags,
    )
    PID_FILE.write_text(str(process.pid), encoding="utf-8")
    deadline = time.time() + 90
    while time.time() < deadline:
        if _probe():
            print(
                json.dumps(
                    {
                        "status": "started",
                        "pid": process.pid,
                        "port": HERMES_PORT,
                        "profile": str(HERMES_HOME),
                        "deepseek_credential_process_scope": bool(key),
                    }
                )
            )
            return 0
        if process.poll() is not None:
            print(json.dumps({"status": "exited", "code": process.returncode}))
            return 1
        time.sleep(1.0)
    print(json.dumps({"status": "timeout", "pid": process.pid}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
