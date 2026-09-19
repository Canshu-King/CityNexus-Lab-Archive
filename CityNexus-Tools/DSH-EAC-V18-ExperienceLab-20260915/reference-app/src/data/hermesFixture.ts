import type { AgentRunEvent, AgentRunFixture } from "../types";

const FIXTURE_SOURCE = "RECORDED_FIXTURE" as const;

function event(
  sequence_no: number,
  event_type: AgentRunEvent["event_type"],
  timestamp: string,
  summary: string,
  tool_name?: string,
  approval_id?: string,
): AgentRunEvent {
  return {
    id: `fixture-event-${sequence_no}`,
    sequence_no,
    event_type,
    timestamp,
    summary,
    source: FIXTURE_SOURCE,
    ...(tool_name ? { tool_name } : {}),
    ...(approval_id ? { approval_id } : {}),
  };
}

/**
 * Recorded Hermes-style multistep run.
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
  recorded_at: "2026-09-15T08:12:06+08:00",
  scenario: "Rain-safe alternative · recorded native Hermes tool loop",
  events: [
    event(1, "run.started", "2026-09-15T08:12:00.000+08:00", "Native Hermes run accepted by CityNexus runtime"),
    event(2, "tool.started", "2026-09-15T08:12:00.420+08:00", "Inspecting the active Journey and protected commitments", "inspect_journey"),
    event(3, "tool.completed", "2026-09-15T08:12:01.180+08:00", "Journey facts and C4 cruise confirmed", "inspect_journey"),
    event(4, "tool.started", "2026-09-15T08:12:01.240+08:00", "Searching recorded CityNexus city services for an indoor alternative", "search_city_services"),
    event(5, "tool.completed", "2026-09-15T08:12:03.900+08:00", "Recorded provider evidence returned 3 indoor candidates", "search_city_services"),
    event(6, "tool.started", "2026-09-15T08:12:04.010+08:00", "Requesting a CityNexus-owned replan proposal", "request_replan"),
    event(7, "approval.required", "2026-09-15T08:12:04.560+08:00", "Policy requires traveler confirmation for this recovery", "request_replan", "approval-fixture-001"),
    event(8, "tool.completed", "2026-09-15T08:12:06.240+08:00", "Recorded confirmation received · proposal persisted as PRESENTED", "request_replan"),
    event(9, "run.completed", "2026-09-15T08:12:06.310+08:00", "Run completed · no live model call and no mutation in this reference"),
  ],
};

/** Edge-case fixture: a failed tool step. */
export const HERMES_FAILED_RUN: AgentRunFixture = {
  ...HERMES_RECORDED_RUN,
  run_id: "run-fixture-hermes-failed-20260915-02",
  scenario: "Recorded failed run · provider timeout",
  events: [
    HERMES_RECORDED_RUN.events[0],
    HERMES_RECORDED_RUN.events[1],
    HERMES_RECORDED_RUN.events[2],
    event(4, "tool.started", "2026-09-15T08:12:01.240+08:00", "Calling recorded provider", "search_city_services"),
    event(5, "tool.failed", "2026-09-15T08:12:07.500+08:00", "Recorded provider timed out after 6s", "search_city_services"),
    event(6, "run.completed", "2026-09-15T08:12:07.650+08:00", "Run completed with failure_reason=provider_timeout"),
  ],
};

/** Edge-case fixture: a stopped run with a long tool name. */
export const HERMES_STOPPED_RUN: AgentRunFixture = {
  ...HERMES_RECORDED_RUN,
  run_id: "run-fixture-hermes-stopped-20260915-03",
  scenario: "Recorded stopped run · long tool name",
  events: [
    HERMES_RECORDED_RUN.events[0],
    event(
      2,
      "tool.started",
      "2026-09-15T08:12:00.420+08:00",
      "Calling a recorded tool with a deliberately long name for layout stress",
      "citynexus.search_city_services_for_rain_safe_indoor_activity_candidates",
    ),
    event(3, "run.stopped", "2026-09-15T08:12:02.100+08:00", "Traveler stopped the recorded run · server truth closed it as STOPPED"),
  ],
};

export const HERMES_FIXTURES = {
  completed: HERMES_RECORDED_RUN,
  failed: HERMES_FAILED_RUN,
  stopped: HERMES_STOPPED_RUN,
} as const;

export type HermesFixtureKey = keyof typeof HERMES_FIXTURES;
