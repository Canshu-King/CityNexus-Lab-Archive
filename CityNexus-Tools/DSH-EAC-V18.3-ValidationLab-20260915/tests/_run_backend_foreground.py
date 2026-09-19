"""Run the isolated CityNexus backend in the FOREGROUND.

Intended to be launched via the Bash tool with run_in_background=true so the
session keeps the process alive (detached children get reaped with the shell).

Uses the MAIN tree .venv to serve the SNAPSHOT app against the isolated lab DB.
Never modifies D:\\moodle\\CityNexus.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab_common import (  # noqa: E402
    MAIN_PY,
    BACKEND,
    BACKEND_PORT,
    backend_env,
    primary_deepseek_key,
)


def main() -> int:
    key = primary_deepseek_key()
    env = backend_env(deepseek_key=key, ai_enabled=bool(key))
    print(f"[foreground-backend] pid={MAIN_PY} port={BACKEND_PORT} ai={bool(key)}", flush=True)
    return subprocess.run(
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
            "info",
        ],
        cwd=str(BACKEND),
        env=env,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
