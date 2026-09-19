"""Create the isolated ``citynexus-harness-lab`` Hermes profile.

The profile is written only under the validation workspace. It points the MCP
bridge at the isolated backend on port 8022 and the Hermes Runs API at 8653.
No credential value is written to this file or to the profile.
"""
from __future__ import annotations

from pathlib import Path

from lab_common import HERMES_HOME, HERMES_RUNTIME_PY, BACKEND_PORT, HERMES_PORT, AGENT_MCP

CONFIG_TEMPLATE = """\
model:
  provider: deepseek
  default: deepseek-v4-flash
  reasoning_effort: high

mcp_servers:
  citynexus:
    command: '{mcp_python}'
    args:
      - '{mcp_runner}'
      - '--v2'
    env:
      CITYNEXUS_API_BASE_URL: 'http://127.0.0.1:{backend_port}'
      PYTHONUTF8: '1'
      PYTHONIOENCODING: 'utf-8'
      PYTHONPATH: '{agent_mcp}'
    enabled: true
    timeout: 120
    connect_timeout: 20
    tools:
      include:
        - inspect_journey
        - inspect_twin
        - list_replans
        - search_city_services
        - request_replan
        - accept_replan
        - replace_activity
        - reschedule_activity
        - create_booking
        - cancel_refundable_booking
        - request_commitment_change
      resources: false
      prompts: false

platform_toolsets:
  api_server:
    - citynexus

agent:
  disabled_toolsets:
    - terminal
    - filesystem
    - browser
    - web
    - computer-use
"""


def main() -> None:
    HERMES_HOME.mkdir(parents=True, exist_ok=True)
    mcp_runner = Path(__file__).resolve().with_name("mcp_runner.py")
    config = CONFIG_TEMPLATE.format(
        mcp_python=HERMES_RUNTIME_PY,
        mcp_runner=mcp_runner,
        backend_port=BACKEND_PORT,
        agent_mcp=AGENT_MCP,
    )
    (HERMES_HOME / "config.yaml").write_text(config, encoding="utf-8")
    (HERMES_HOME / "SOUL.md").write_text(
        "You are a CityNexus validation-lab assistant. Use only the configured "
        "CityNexus MCP tools. CityNexus Gateway/Guardian are authoritative.\n",
        encoding="utf-8",
    )
    print(f"lab profile created at {HERMES_HOME}")
    print(f"hermes runs port expected: {HERMES_PORT}")


if __name__ == "__main__":
    main()
