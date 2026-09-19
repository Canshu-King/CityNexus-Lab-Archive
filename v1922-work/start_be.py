"""Start exactly ONE CityNexus backend with live credentials.

Secrets are read from the user environment and injected into the child only.
"""
import os, subprocess, sys, winreg
from pathlib import Path

REPO = Path("D:/moodle/CityNexus")
DB = Path("D:/moodle/_v1922_work/fc_evidence/_db/live.db")
DB.parent.mkdir(parents=True, exist_ok=True)

def reg(name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            return str(winreg.QueryValueEx(k, name)[0]) or None
    except OSError:
        return None

env = dict(os.environ)
env.update({
    "CITYNEXUS_DATABASE_URL": f"sqlite:///{DB}",
    "PYTHONDONTWRITEBYTECODE": "1",
    "CITYNEXUS_AI_ENABLED": "true",
    "CITYNEXUS_AI_PROVIDER": "deepseek",
    "CITYNEXUS_PHOTON_ENABLED": "true",
    "CITYNEXUS_OPEN_METEO_ENABLED": "true",
    "CITYNEXUS_REAL_CITY_ENABLED": "true",
    "CITYNEXUS_REAL_CITY_MODE": "live",
    "CITYNEXUS_REAL_CITY_TIMEOUT_SECONDS": "60",
})
# The public map/accommodation providers are reached through the user's local
# proxy (Mihomo).  Windows stores it in the Internet Settings registry, not in
# the environment, so httpx's trust_env=True would find nothing and every
# provider call would time out.  Mirror the registry value into the child env.
proxy = None
try:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
    ) as k:
        enabled, _ = winreg.QueryValueEx(k, "ProxyEnable")
        if enabled:
            proxy = str(winreg.QueryValueEx(k, "ProxyServer")[0]) or None
except OSError:
    proxy = None
if proxy:
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        env.setdefault(name, f"http://{proxy}")
print("proxy_injected:", bool(proxy), file=sys.stderr)

key = reg("DEEPSEEK_API_KEY")
if key:
    env["DEEPSEEK_API_KEY"] = key
    env["CITYNEXUS_AI_API_KEY"] = key
print("deepseek_key_injected:", bool(key), file=sys.stderr)
proc = subprocess.Popen(
    [str(REPO / ".venv/Scripts/python.exe"), "-m", "uvicorn", "app.main:app",
     "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(REPO / "backend"), env=env,
    stdout=open("D:/moodle/_v1922_work/fc_evidence/be.log", "w", encoding="utf-8"),
    stderr=subprocess.STDOUT,
)
print("BE_PID", proc.pid)
proc.wait()
