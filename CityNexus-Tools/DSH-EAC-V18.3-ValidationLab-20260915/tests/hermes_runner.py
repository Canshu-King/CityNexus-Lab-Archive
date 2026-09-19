"""Run a Hermes CLI command using the portable Hermes runtime.

Usage: python tests/hermes_runner.py <hermes args...>

The wrapper only uses process-scoped credential material supplied by the
parent process. It never reads or writes credential values itself.
"""
from __future__ import annotations

import site
import sys
from pathlib import Path

HERMES_AGENT = Path(
    r"C:\Users\仓鼠王\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0"
    r"\LocalCache\Local\hermes\hermes-agent"
)
HERMES_SITE = HERMES_AGENT / ".venv" / "Lib" / "site-packages"
RUNTIME_DIR = HERMES_AGENT / ".hermes-runtime" / "python" / "cpython-3.11.16-windows-x86_64-none"

if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))
if str(HERMES_AGENT) not in sys.path:
    sys.path.insert(0, str(HERMES_AGENT))
if HERMES_SITE.is_dir():
    site.addsitedir(str(HERMES_SITE))

if __name__ == "__main__":
    from hermes_cli.main import main

    main()
