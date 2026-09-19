"""V19.2.2 isolated web lab: backend 8070 + frontend 4214 from snapshot_d."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LAB = Path(os.environ.get("V192_LAB", Path(__file__).resolve().parent.parent))
SNAP = LAB / "snapshot_d"
FRONTEND = SNAP / "frontend"
VENV_PY = Path(r"D:\moodle\CityNexus\.venv\Scripts\python.exe")
MAIN_NODE_MODULES = Path(r"D:\moodle\CityNexus\frontend\node_modules")

BACKEND_PORT = 8070
FRONTEND_PORT = 4214


def wait_port(port: int, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.4)
    return False


def wait_http(url: str, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status < 500:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> int:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CITYNEXUS_DATABASE_URL"] = (
        f"sqlite:///{LAB / 'evidence' / '_db' / 'web_lab_d.db'}"
    )
    (LAB / "evidence" / "_db").mkdir(parents=True, exist_ok=True)
    env["CITYNEXUS_AI_ENABLED"] = "false"
    env["CITYNEXUS_GUARDIAN_AUTORUN"] = "false"

    backend = subprocess.Popen(
        [str(VENV_PY), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(BACKEND_PORT)],
        cwd=str(SNAP / "backend"), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if not wait_http(f"http://127.0.0.1:{BACKEND_PORT}/api/v1/demo/reset"):
        # demo/reset is POST-only; a 405 still proves the server is up.
        if not wait_port(BACKEND_PORT):
            backend.kill()
            print("backend failed to start")
            return 1
    print(f"backend ready on {BACKEND_PORT}")

    node = Path(r"C:\Users\仓鼠王\.workbuddy-ai\binaries\node\versions\22.22.2-2\node.exe")
    if not node.exists():
        node = Path("node")
    frontend_env = dict(env)
    frontend_env["CITYNEXUS_API_TARGET"] = f"http://127.0.0.1:{BACKEND_PORT}"
    frontend = subprocess.Popen(
        [str(node), str(MAIN_NODE_MODULES / "vite" / "bin" / "vite.js"),
         "--host", "127.0.0.1", "--port", str(FRONTEND_PORT), "--strictPort"],
        cwd=str(FRONTEND), env=frontend_env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if not wait_http(f"http://127.0.0.1:{FRONTEND_PORT}/"):
        frontend.kill()
        backend.kill()
        print("frontend failed to start")
        return 1
    print(f"frontend ready on {FRONTEND_PORT}")
    print(f"PID_BACKEND={backend.pid}")
    print(f"PID_FRONTEND={frontend.pid}")
    print(f"API={BACKEND_PORT} WEB={FRONTEND_PORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
