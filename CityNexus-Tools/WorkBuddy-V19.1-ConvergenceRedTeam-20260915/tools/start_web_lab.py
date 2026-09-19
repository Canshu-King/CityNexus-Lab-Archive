"""V19.1 isolated web/mobile lab: backend 8050 + frontend 4203, built from Snapshot B.

Deliberately different ports from the still-running V19 lab (8040/4193) and from
Codex (8000/5173).  The main worktree is never written to.

Usage:
    python tools/start_web_lab.py          # start both, wait until ready
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

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
SNAP = LAB / "snapshot_b"
FRONTEND = SNAP / "frontend"
VENV_PY = Path(r"D:\moodle\CityNexus\backend\.venv\Scripts\python.exe")
NODE = Path(r"C:\Users\仓鼠王\.workbuddy-ai\binaries\node\versions\22.22.2-2\node.exe")
MAIN_NODE_MODULES = Path(r"D:\moodle\CityNexus\frontend\node_modules")

BACKEND_PORT = 8050
FRONTEND_PORT = 4203
DB_PATH = LAB / "evidence" / "_db" / "web_lab_b.db"

# Log files are dedicated and never deleted while a process holds them:
# deleting a live stdout handle kills the server on Windows.
BACKEND_LOG = LAB / "_v191_web_backend.log"
FRONTEND_LOG = LAB / "_v191_web_frontend.log"

VITE_CONFIG = FRONTEND / "vite.v191-local.config.ts"


def _port_open(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _http_status(url: str) -> int:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url, timeout=4) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def ensure_node_modules() -> str:
    """Reuse the main tree's node_modules via a junction (npm ci hangs here)."""
    target = FRONTEND / "node_modules"
    if target.exists():
        return "already present"
    if not MAIN_NODE_MODULES.is_dir():
        return "MISSING: main tree has no node_modules"
    # cmd.exe writes mklink output in the OEM code page, so capture bytes and
    # decode leniently rather than letting text=True raise UnicodeDecodeError.
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(target), str(MAIN_NODE_MODULES)],
        capture_output=True,
    )
    output = (result.stdout or b"") + (result.stderr or b"")
    text = output.decode("utf-8", errors="replace").strip().replace("\n", " ")
    return f"mklink rc={result.returncode} {text[:160]}"


def write_vite_config() -> None:
    """A local config: proxy to OUR backend, and keep the dep cache out of the tree."""
    VITE_CONFIG.write_text(
        """import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// V19.1 isolated lab config.  Not part of the product build.
export default defineConfig({
  plugins: [react()],
  cacheDir: process.env.TEMP ? `${process.env.TEMP}/v191-vite-cache` : ".vite-cache",
  server: {
    host: "127.0.0.1",
    port: 4203,
    strictPort: true,
    proxy: {
      "/api/v1": { target: "http://127.0.0.1:8050", changeOrigin: false },
    },
  },
});
""",
        encoding="utf-8",
    )


def start_backend() -> subprocess.Popen:
    env = dict(os.environ)
    env.update(
        {
            "CITYNEXUS_DATABASE_URL": f"sqlite:///{DB_PATH}",
            "CITYNEXUS_ENV": "test",
            "CITYNEXUS_AI_ENABLED": "false",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    handle = BACKEND_LOG.open("a", encoding="utf-8")
    handle.write(f"\n=== start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    handle.flush()
    return subprocess.Popen(
        [str(VENV_PY), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(BACKEND_PORT), "--log-level", "warning"],
        cwd=str(SNAP / "backend"),
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )


def start_frontend() -> subprocess.Popen:
    vite = FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"
    handle = FRONTEND_LOG.open("a", encoding="utf-8")
    handle.write(f"\n=== start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    handle.flush()
    return subprocess.Popen(
        [str(NODE), str(vite), "--config", str(VITE_CONFIG), "--port", str(FRONTEND_PORT)],
        cwd=str(FRONTEND),
        stdout=handle,
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    print(f"node_modules: {ensure_node_modules()}")
    write_vite_config()

    procs: list[tuple[str, subprocess.Popen]] = []
    if _port_open(BACKEND_PORT):
        print(f"backend {BACKEND_PORT} already listening")
    else:
        procs.append(("backend", start_backend()))
        print(f"backend starting on {BACKEND_PORT} (log {BACKEND_LOG.name})")
    if _port_open(FRONTEND_PORT):
        print(f"frontend {FRONTEND_PORT} already listening")
    else:
        procs.append(("frontend", start_frontend()))
        print(f"frontend starting on {FRONTEND_PORT} (log {FRONTEND_LOG.name})")

    deadline = time.time() + 90
    while time.time() < deadline:
        back = _http_status(f"http://127.0.0.1:{BACKEND_PORT}/api/v1/demo/reset") in (200, 405)
        front = _port_open(FRONTEND_PORT)
        if back and front:
            break
        for name, proc in procs:
            if proc.poll() is not None:
                print(f"!! {name} exited with {proc.returncode}; see its log")
                return 1
        time.sleep(1.5)

    print(f"backend  ready: {_http_status(f'http://127.0.0.1:{BACKEND_PORT}/api/v1/demo/reset')}")
    print(f"frontend ready: {_port_open(FRONTEND_PORT)}")
    print(f"frontend URL  : http://127.0.0.1:{FRONTEND_PORT}/v8/live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
