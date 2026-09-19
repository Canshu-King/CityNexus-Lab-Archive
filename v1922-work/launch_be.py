"""Start the CityNexus backend with live credentials.

Reads secrets from the user environment, injects them into the child process
only, and never prints or persists them.
"""
from __future__ import annotations

import os
import subprocess
import sys
import winreg
from pathlib import Path

REPO = Path("D:/moodle/CityNexus")
DB = Path("D:/moodle/_v1922_work/fc_evidence/_db/live.db")
DB.parent.mkdir(parents=True, exist_ok=True)


def reg(name: str) -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            value, _ = winreg.QueryValueEx(k, name)
            return str(value) or None
    except OSError:
        return None


env = dict(os.environ)
env["CITYNEXUS_DATABASE_URL"] = f"sqlite:///{DB}"
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["CITYNEXUS_AI_ENABLED"] = "true"
env["CITYNEXUS_AI_PROVIDER"] = "deepseek"
env["CITYNEXUS_PHOTON_ENABLED"] = "true"
env["CITYNEXUS_OPEN_METEO_ENABLED"] = "true"
env["CITYNEXUS_REAL_CITY_ENABLED"] = "true"
env["CITYNEXUS_REAL_CITY_MODE"] = "live"
env["CITYNEXUS_REAL_CITY_TIMEOUT_SECONDS"] = "60"
env["CITYNEXUS_OVERPASS_URL"] = reg("CITYNEXUS_OVERPASS_URL") or "https://overpass-api.de/api"
key = reg("DEEPSEEK_API_KEY")
if key:
    env["DEEPSEEK_API_KEY"] = key
    env["CITYNEXUS_AI_API_KEY"] = key
print("deepseek_key_injected:", bool(key), file=sys.stderr)
if reg("AMAP_WEB_KEY"):
    env["AMAP_WEB_KEY"] = reg("AMAP_WEB_KEY")

proc = subprocess.Popen(
    [str(REPO / ".venv/Scripts/python.exe"), "-m", "uvicorn", "app.main:app",
     "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(REPO / "backend"), env=env,
    stdout=open("D:/moodle/_v1922_work/fc_evidence/be.log", "w", encoding="utf-8"),
    stderr=subprocess.STDOUT,
)
print("BE_PID", proc.pid)
proc.wait()
