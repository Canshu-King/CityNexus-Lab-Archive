"""Restart the isolated V19 lab servers (backend 8040, frontend 4193).

Never touches the main worktree.  Logs go to dedicated files that are never
deleted while the process is alive (a deleted stdout handle kills uvicorn on
Windows).

Usage:
    python tools/start_lab_servers.py            # start both, report readiness
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
REPO = LAB / "repo_copy"
VENV_PY = Path(r"D:\moodle\CityNexus\backend\.venv\Scripts\python.exe")
NODE = Path(r"C:\Users\仓鼠王\.workbuddy-ai\binaries\node\versions\22.22.2-2\node.exe")
VITE_JS = REPO / "frontend" / "node_modules" / "vite" / "bin" / "vite.js"

BACKEND_PORT = 8040
FRONTEND_PORT = 4193
DB_PATH = LAB / "v19_redteam.db"

BACKEND_LOG = LAB / "_v19_backend_server.log"
FRONTEND_LOG = LAB / "_v19_frontend_server.log"


def _port_open(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _http_ok(url: str) -> int:
    # Bypass any system proxy: the lab is loopback-only.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url, timeout=3) as response:
            return response.status
    except urllib.error.HTTPError as exc:  # noqa: PERF203
        return exc.code
    except Exception:
        return 0


def start_backend() -> subprocess.Popen:
    env = dict(os.environ)
    env.update(
        {
            "CITYNEXUS_DATABASE_URL": f"sqlite:///{DB_PATH}",
            "CITYNEXUS_ENV": "test",
            "CITYNEXUS_AI_ENABLED": "false",
            "CITYNEXUS_GUARDIAN_AUTORUN": "false",
            "PYTHONPATH": str(REPO / "backend"),
        }
    )
    handle = open(BACKEND_LOG, "a", encoding="utf-8", buffering=1)
    handle.write(f"\n=== restart {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    return subprocess.Popen(
        [
            str(VENV_PY),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BACKEND_PORT),
            "--log-level",
            "info",
        ],
        cwd=str(REPO / "backend"),
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def start_frontend() -> subprocess.Popen:
    env = dict(os.environ)
    env["TEMP"] = env.get("TEMP") or r"C:\Users\仓鼠王\AppData\Local\Temp"
    handle = open(FRONTEND_LOG, "a", encoding="utf-8", buffering=1)
    handle.write(f"\n=== restart {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    return subprocess.Popen(
        [
            str(NODE),
            str(VITE_JS),
            "--config",
            "vite.v19-local.config.ts",
            "--host",
            "127.0.0.1",
            "--port",
            str(FRONTEND_PORT),
        ],
        cwd=str(REPO / "frontend"),
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def main() -> int:
    report: list[str] = []

    if _port_open(BACKEND_PORT):
        report.append(f"backend  :{BACKEND_PORT} already listening")
    else:
        proc = start_backend()
        report.append(f"backend  :{BACKEND_PORT} spawned pid={proc.pid}")

    if _port_open(FRONTEND_PORT):
        report.append(f"frontend :{FRONTEND_PORT} already listening")
    else:
        proc = start_frontend()
        report.append(f"frontend :{FRONTEND_PORT} spawned pid={proc.pid}")

    deadline = time.time() + 90
    backend_code = frontend_code = 0
    while time.time() < deadline:
        backend_code = _http_ok(f"http://127.0.0.1:{BACKEND_PORT}/api/v1/health")
        frontend_code = _http_ok(f"http://127.0.0.1:{FRONTEND_PORT}/")
        if backend_code == 200 and frontend_code == 200:
            break
        time.sleep(2)

    report.append(f"backend  health = {backend_code}")
    report.append(f"frontend root   = {frontend_code}")

    print("\n".join(report))
    return 0 if (backend_code == 200 and frontend_code == 200) else 1


if __name__ == "__main__":
    sys.exit(main())
