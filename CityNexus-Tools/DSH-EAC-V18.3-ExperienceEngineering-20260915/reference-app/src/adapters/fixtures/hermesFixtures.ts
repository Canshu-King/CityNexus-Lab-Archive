import type { AgentRunEvent, AgentRunFixture } from "../../types";

const FIXTURE_SOURCE = "RECORDED_FIXTURE" as const;

function event(
  sequence_no: number,
  event_type: AgentRunEvent["event_type"],
  timestamp: string,
  summary: string,
  extra: Partial<Omit<AgentRunEvent, "id" | "sequence_no" | "event_type" | "timestamp" | "summary" | "source">> = {},
): AgentRunEvent {
  return {
    id: `fixture-event-${sequence_no}`,
    sequence_no,
    event_type,
    timestamp,
    summary,
    source: FIXTURE_SOURCE,
    ...extra,
  };
}

/**
 * Recorded Hermes-style multistep run with approval required.
 *
 * IMPORTANT: these events are a recording. The UI replays only the events that
 * exist in this array and never synthesizes progress with setTimeout/setInterval.
 */
export const HERMES_RECORDED_RUN: AgentRunFixture = {
  fixture_label: "RECORDED_FIXTURE",
  run_id: "run-fixture-hermes-20260915-01",
  runtime_identity: "HERMES_NATIVE_MCP",
  provider_key: "deepseek-native-fixture",
  model_key: "deepseek-chat-fixture",
  recorded_at: "2026-09-15T08:12:08+08:00",
  scenario: "Rain-safe alternative · recorded native Hermes tool loop with approval",
  events: [
    event(1, "semantic.interpreted", "2026-09-15T08:12:00.000+08:00", "DeepSeek compiled the request as REQUEST_REPLAN · assertion confirmed", { run_status: "running" }),
    event(2, "mission.planned", "2026-09-15T08:12:00.180+08:00", "CityNexus mission planned: search indoor alternatives, protect C4 commitments", { run_status: "running" }),
    event(3, "run.started", "2026-09-15T08:12:00.320+08:00", "Native Hermes run accepted by the CityNexus runtime", { run_status: "running" }),
    event(4, "tool.started", "2026-09-15T08:12:00.420+08:00", "Checking the active Journey", { tool_name: "inspect_journey", run_status: "running" }),
    event(5, "tool.completed", "2026-09-15T08:12:00.600+08:00", "Journey facts loaded", { tool_name: "inspect_journey", duration_ms: 180, run_status: "running" }),
    event(6, "tool.started", "2026-09-15T08:12:00.660+08:00", "Checking protected commitments", { tool_name: "inspect_twin", run_status: "running" }),
    event(7, "tool.completed", "2026-09-15T08:12:00.800+08:00", "C4 cruise, hotel, and departure buffer confirmed protected", { tool_name: "inspect_twin", duration_ms: 140, run_status: "running" }),
    event(8, "tool.started", "2026-09-15T08:12:00.860+08:00", "Searching recorded CityNexus city services for an indoor alternative", { tool_name: "search_city_services", run_status: "running" }),
    event(9, "tool.completed", "2026-09-15T08:12:01.480+08:00", "Recorded provider evidence returned 3 indoor candidates", { tool_name: "search_city_services", duration_ms: 620, run_status: "running" }),
    event(10, "gateway.checked", "2026-09-15T08:12:01.520+08:00", "Gateway policy checked: reversible indoor swap, no budget expansion", { run_status: "running" }),
    event(11, "guardian.checked", "2026-09-15T08:12:01.560+08:00", "Guardian checked: protected commitments remain feasible", { run_status: "running" }),
    event(12, "tool.started", "2026-09-15T08:12:01.620+08:00", "Requesting a CityNexus-owned replan proposal", { tool_name: "request_replan", run_status: "running" }),
    event(13, "proposal.created", "2026-09-15T08:12:02.240+08:00", "Recovery proposal persisted as PRESENTED", { proposal_id: "proposal-fixture-002", run_status: "approval_required" }),
    event(14, "approval.required", "2026-09-15T08:12:02.300+08:00", "CityNexus requires traveler approval before this high-impact recovery", { approval_id: "approval-fixture-002", proposal_id: "proposal-fixture-002", run_status: "approval_required" }),
  ],
};

/** Same recorded run after the traveler approved the high-impact recovery. */
export const HERMES_APPROVED_RUN: AgentRunFixture = {
  ...HERMES_RECORDED_RUN,
  run_id: "run-fixture-hermes-approved-20260915-01b",
  scenario: "Rain-safe alternative · recorded approval and completion",
  events: [
    ...HERMES_RECORDED_RUN.events,
    event(15, "run.completed", "2026-09-15T08:12:05.600+08:00", "Approval recorded by CityNexus · child PlanVersion became authoritative", { proposal_id: "proposal-fixture-002", run_status: "success" }),
  ],
};

/** Edge-case fixture: a failed tool step and a failed run. */
export const HERMES_FAILED_RUN: AgentRunFixture = {
  ...HERMES_RECORDED_RUN,
  run_id: "run-fixture-hermes-failed-20260915-02",
  scenario: "Recorded failed run · provider timeout",
  events: [
    HERMES_RECORDED_RUN.events[0],
    HERMES_RECORDED_RUN.events[1],
    HERMES_RECORDED_RUN.events[2],
    HERMES_RECORDED_RUN.events[3],
    event(5, "tool.failed", "2026-09-15T08:12:07.500+08:00", "Recorded provider timed out after 6s", { tool_name: "inspect_journey", duration_ms: 6000, run_status: "failed" }),
    event(6, "run.failed", "2026-09-15T08:12:07.650+08:00", "Run failed · failure_reason=provider_timeout · next action: retry or keep current plan", { run_status: "failed" }),
  ],
};

/** Edge-case fixture: a stopped run with a deliberately long tool name. */
export const HERMES_STOPPED_RUN: AgentRunFixture = {
  ...HERMES_RECORDED_RUN,
  run_id: "run-fixture-hermes-stopped-20260915-03",
  scenario: "Recorded stopped run · long tool name",
  events: [
    HERMES_RECORDED_RUN.events[0],
    HERMES_RECORDED_RUN.events[1],
    event(3, "run.started", "2026-09-15T08:12:00.320+08:00", "Native Hermes run accepted by the CityNexus runtime", { run_status: "running" }),
    event(
      4,
      "tool.started",
      "2026-09-15T08:12:00.420+08:00",
      "Calling a recorded tool with a deliberately long name for layout stress",
      { tool_name: "citynexus.search_city_services_for_rain_safe_indoor_activity_candidates", run_status: "running" },
    ),
    event(5, "run.stopped", "2026-09-15T08:12:02.100+08:00", "Traveler stopped the recorded run · server truth closed it as STOPPED", { run_status: "stopped" }),
  ],
};

export const HERMES_FIXTURES = {
  completed: HERMES_RECORDED_RUN,
  approved: HERMES_APPROVED_RUN,
  failed: HERMES_FAILED_RUN,
  stopped: HERMES_STOPPED_RUN,
} as const;

export type HermesFixtureKey = keyof typeof HERMES_FIXTURES;
