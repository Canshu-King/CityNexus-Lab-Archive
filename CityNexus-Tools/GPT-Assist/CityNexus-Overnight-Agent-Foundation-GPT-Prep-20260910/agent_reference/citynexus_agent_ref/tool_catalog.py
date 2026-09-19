from __future__ import annotations

from dataclasses import dataclass

from .contracts import AgentAction


@dataclass(frozen=True)
class ToolDescriptor:
    action: AgentAction
    tool_name: str
    mutates_domain_truth: bool
    changes_money: bool
    changes_c4: bool


TOOLS = (
    ToolDescriptor(AgentAction.INSPECT_JOURNEY, "inspect_journey", False, False, False),
    ToolDescriptor(AgentAction.INSPECT_TWIN, "inspect_twin", False, False, False),
    ToolDescriptor(AgentAction.LIST_REPLANS, "list_replans", False, False, False),
    ToolDescriptor(AgentAction.SEARCH_CITY_SERVICES, "search_city_services", False, False, False),
    ToolDescriptor(AgentAction.REQUEST_REPLAN, "request_replan", False, False, False),
    ToolDescriptor(AgentAction.ACCEPT_REPLAN, "accept_replan", True, False, False),
    ToolDescriptor(AgentAction.UPDATE_PREFERENCES, "update_preferences", True, False, False),
    ToolDescriptor(AgentAction.CREATE_BOOKING, "create_booking", True, True, False),
    ToolDescriptor(AgentAction.CANCEL_BOOKING, "cancel_booking", True, True, False),
    ToolDescriptor(AgentAction.PAYMENT, "payment", True, True, False),
    ToolDescriptor(AgentAction.REFUND, "refund", True, True, False),
    ToolDescriptor(AgentAction.MODIFY_C4, "modify_c4", True, False, True),
)

TOOL_BY_ACTION = {item.action: item for item in TOOLS}
RUNTIME_MCP_ALLOWLIST_V1 = frozenset(
    {
        "inspect_journey",
        "inspect_twin",
        "list_replans",
        "search_city_services",
        "request_replan",
        "accept_replan",
    }
)
