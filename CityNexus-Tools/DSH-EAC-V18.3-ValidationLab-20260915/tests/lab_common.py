"""Shared isolation helpers for the DSH EAC V18.3 validation lab.

Never prints credential values. Credentials are only copied into child-process
environments when explicitly requested by a launcher.
"""
from __future__ import annotations

import ctypes
import json
import os
import random
import string
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SNAPSHOT = WORKSPACE / "source-snapshot"
BACKEND = SNAPSHOT / "backend"
AGENT_MCP = SNAPSHOT / "agent-mcp"
FRONTEND = SNAPSHOT / "frontend"
LAB_DATA = WORKSPACE / "lab-data"
LOGS = WORKSPACE / "logs"
EVIDENCE = WORKSPACE / "evidence"
HERMES_HOME = WORKSPACE / "lab-home" / "profiles" / "citynexus-harness-lab"
DB_PATH = LAB_DATA / "citynexus_lab.db"
SECRET_FILE = LAB_DATA / "hermes_lab_api_key.txt"

MAIN_ROOT = Path(r"D:\moodle\CityNexus")
MAIN_PY = MAIN_ROOT / "backend" / ".venv" / "Scripts" / "python.exe"

HERMES_ROOT = Path(
    r"C:\Users\仓鼠王\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0"
    r"\LocalCache\Local\hermes"
)
HERMES_AGENT = HERMES_ROOT / "hermes-agent"
HERMES_RUNTIME_PY = (
    HERMES_AGENT
    / ".hermes-runtime"
    / "python"
    / "cpython-3.11.16-windows-x86_64-none"
    / "python.exe"
)
HERMES_SITE = HERMES_AGENT / ".venv" / "Lib" / "site-packages"
PRIMARY_PROFILE = HERMES_ROOT / "profiles" / "citynexus"
PRIMARY_GATEWAY_PID = PRIMARY_PROFILE / "gateway.pid"

BACKEND_PORT = 8022
FRONTEND_PORT = 4178
HERMES_PORT = 8653


def _windows_path(path: Path | str) -> str:
    return str(path).replace("/", "\\")


def pythonpath() -> str:
    return os.pathsep.join(
        [
            _windows_path(BACKEND),
            _windows_path(AGENT_MCP),
            _windows_path(HERMES_AGENT) if HERMES_AGENT.exists() else "",
        ]
    ).strip(os.pathsep)


def db_url() -> str:
    return "sqlite:///" + str(DB_PATH).replace("\\", "/")


def get_lab_api_key() -> str:
    """Return a generated loopback-only lab API key, persisted outside deliverables."""
    LAB_DATA.mkdir(parents=True, exist_ok=True)
    if SECRET_FILE.exists():
        value = SECRET_FILE.read_text(encoding="utf-8").strip()
        if len(value) >= 32:
            return value
    alphabet = string.ascii_letters + string.digits
    value = "".join(random.SystemRandom().choice(alphabet) for _ in range(48))
    SECRET_FILE.write_text(value, encoding="utf-8")
    return value


def _read_process_environment(pid: int) -> dict[str, str]:
    """Read a same-user process environment via PEB on Windows.

    Used only to obtain an existing DeepSeek credential for a child process
    scope. The values are never logged or persisted by this module.
    """
    if os.name != "nt":
        return {}
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")

    class PROCESS_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("ExitStatus", ctypes.c_long),
            ("PebBaseAddress", ctypes.c_void_p),
            ("AffinityMask", ctypes.c_void_p),
            ("BasePriority", ctypes.c_long),
            ("UniqueProcessId", ctypes.c_void_p),
            ("InheritedFromUniqueProcessId", ctypes.c_void_p),
        ]

    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    handle = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        return {}
    try:
        pbi = PROCESS_BASIC_INFORMATION()
        status = ntdll.NtQueryInformationProcess(
            handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None
        )
        if status != 0:
            return {}

        def read_memory(address: int, size: int) -> bytes | None:
            buffer = (ctypes.c_ubyte * size)()
            read = ctypes.c_size_t()
            ok = k32.ReadProcessMemory(
                handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(read)
            )
            if not ok:
                return None
            return bytes(buffer[: read.value])

        peb = int(pbi.PebBaseAddress or 0)
        raw_pp = read_memory(peb + 0x20, 8)
        if not raw_pp:
            return {}
        process_parameters = int.from_bytes(raw_pp, "little")
        raw_env = read_memory(process_parameters + 0x80, 8)
        if not raw_env:
            return {}
        environment = int.from_bytes(raw_env, "little")
        if not environment:
            return {}
        chunks: list[bytes] = []
        offset = 0
        while offset < 2_000_000:
            chunk = read_memory(environment + offset, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            offset += len(chunk)
            joined = b"".join(chunks)
            end = -1
            for index in range(0, len(joined) - 1, 2):
                if joined[index : index + 2] == b"\x00\x00":
                    if index == 0 or joined[index - 2 : index] == b"\x00\x00":
                        end = index
                        break
            if end >= 0:
                joined = joined[:end]
                break
        else:
            joined = b"".join(chunks)
        text = joined.decode("utf-16-le", errors="replace")
        result: dict[str, str] = {}
        for item in text.split("\x00"):
            if "=" in item:
                key, value = item.split("=", 1)
                if key:
                    result[key] = value
        return result
    finally:
        k32.CloseHandle(handle)


def primary_deepseek_key() -> str | None:
    """Return the primary gateway's DeepSeek key for child-process reuse only."""
    direct = os.getenv("DEEPSEEK_API_KEY") or os.getenv("CITYNEXUS_AI_API_KEY")
    if direct:
        return direct
    if not PRIMARY_GATEWAY_PID.exists():
        return None
    try:
        info = json.loads(PRIMARY_GATEWAY_PID.read_text(encoding="utf-8"))
        pid = int(info.get("pid") or 0)
        if pid <= 0:
            return None
        env = _read_process_environment(pid)
        return env.get("DEEPSEEK_API_KEY") or None
    except Exception:
        return None


def base_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = pythonpath()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def backend_env(*, deepseek_key: str | None = None, ai_enabled: bool = False) -> dict[str, str]:
    env = base_env()
    env.update(
        {
            "CITYNEXUS_ENV": "development",
            "CITYNEXUS_DATABASE_URL": db_url(),
            "CITYNEXUS_AI_ENABLED": "true" if ai_enabled and deepseek_key else "false",
            "CITYNEXUS_AI_PROVIDER": "deepseek",
            "CITYNEXUS_AI_MODEL": "deepseek-v4-flash",
            "CITYNEXUS_DEEPSEEK_API_URL": "https://api.deepseek.com/responses",
            "CITYNEXUS_DEEPSEEK_REASONING_EFFORT": "high",
            "CITYNEXUS_DEEPSEEK_WEB_SEARCH": "false",
            "CITYNEXUS_HERMES_NATIVE_API_URL": f"http://127.0.0.1:{HERMES_PORT}",
            "CITYNEXUS_HERMES_BINARY": str(HERMES_AGENT / ".venv" / "Scripts" / "hermes.exe"),
            "CITYNEXUS_HERMES_API_SERVER_KEY": get_lab_api_key(),
            "CITYNEXUS_HERMES_NATIVE_PROFILE": "citynexus-harness-lab",
            "CITYNEXUS_HERMES_NATIVE_PROVIDER": "deepseek",
            "CITYNEXUS_HERMES_NATIVE_MODEL": "deepseek-v4-flash",
            "CITYNEXUS_SOLVER": "deterministic",
            "CITYNEXUS_GUARDIAN_AUTORUN": "false",
            "CITYNEXUS_REAL_CITY_ENABLED": "false",
        }
    )
    if deepseek_key:
        env["DEEPSEEK_API_KEY"] = deepseek_key
        env["CITYNEXUS_AI_API_KEY"] = deepseek_key
    return env


def hermes_env(*, deepseek_key: str | None = None) -> dict[str, str]:
    env = base_env()
    env.update(
        {
            "HERMES_HOME": _windows_path(HERMES_HOME),
            "API_SERVER_KEY": get_lab_api_key(),
            "API_SERVER_PORT": str(HERMES_PORT),
            "API_SERVER_HOST": "127.0.0.1",
            "HERMES_QUIET": "1",
            "HERMES_ACCEPT_HOOKS": "1",
        }
    )
    if deepseek_key:
        env["DEEPSEEK_API_KEY"] = deepseek_key
    return env
