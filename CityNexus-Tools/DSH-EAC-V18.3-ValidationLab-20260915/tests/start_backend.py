"""Start the isolated CityNexus backend on 127.0.0.1:8022.

The DeepSeek key, when present, is copied into the child process environment
only. It is never printed or written to disk by this launcher.
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
    BACKEND,
    BACKEND_PORT,
    LAB_DATA,
    LOGS,
    MAIN_PY,
    backend_env,
    primary_deepseek_key,
)

PID_FILE = LAB_DATA / "backend.pid"


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


def _health() -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{BACKEND_PORT}/api/v1/health", timeout=2
        ) as response:
            return response.status == 200
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
    env = backend_env(deepseek_key=key, ai_enabled=bool(key))
    out = open(LOGS / "backend.out.log", "ab", buffering=0)
    err = open(LOGS / "backend.err.log", "ab", buffering=0)
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
        subprocess, "DETACHED_PROCESS", 0
    )
    process = subprocess.Popen(
        [
            str(MAIN_PY),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BACKEND_PORT),
            "--log-level",
            "warning",
        ],
        cwd=str(BACKEND),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=err,
        creationflags=creationflags,
    )
    PID_FILE.write_text(str(process.pid), encoding="utf-8")
    deadline = time.time() + 40
    while time.time() < deadline:
        if _health():
            print(
                json.dumps(
                    {
                        "status": "started",
                        "pid": process.pid,
                        "port": BACKEND_PORT,
                        "deepseek_credential_process_scope": bool(key),
                    }
                )
            )
            return 0
        if process.poll() is not None:
            print(json.dumps({"status": "exited", "code": process.returncode}))
            return 1
        time.sleep(0.5)
    print(json.dumps({"status": "timeout", "pid": process.pid}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
