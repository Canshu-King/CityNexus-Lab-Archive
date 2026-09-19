"""Run the isolated CityNexus MCP v2 server with the Hermes portable runtime.

This wrapper avoids depending on the MSIX/uv trampoline path resolution of the
installed Hermes venv. Hermes spawns this file as the MCP stdio command.
"""
from __future__ import annotations

import os
import site
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SNAPSHOT = WORKSPACE / "source-snapshot"
AGENT_MCP = SNAPSHOT / "agent-mcp"
HERMES_SITE = Path(
    r"C:\Users\仓鼠王\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0"
    r"\LocalCache\Local\hermes\hermes-agent\.venv\Lib\site-packages"
)

if HERMES_SITE.is_dir():
    site.addsitedir(str(HERMES_SITE))
for path in (str(AGENT_MCP), str(SNAPSHOT / "backend")):
    if path not in sys.path:
        sys.path.insert(0, path)

if __name__ == "__main__":
    from citynexus_mcp.server import main

    main()
