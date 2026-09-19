/**
 * Runtime normalization boundary for CityNexus V18.3.
 *
 * Mirrors the read-only server contract in
 * `backend/app/agent/runtime_events.py`: raw Hermes/REST/SSE payloads are
 * mapped to the stable `NormalizedAgentEvent` contract.
 *
 * Guarantees:
 * - normalization never throws;
 * - known streaming noise is dropped by returning `null`;
 * - unrecognized event names become `unknown` with `unknown: true` and the
 *   original `raw_event_type` preserved;
 * - `citynexus__tool_name` style tool names are reduced to the suffix;
 * - optional fields always receive safe defaults.
 *
 * Source honesty: the caller decides the `source`. Recorded fixtures pass
 * `RECORDED_FIXTURE`, real responses/events pass `LIVE`, cached snapshots pass
 * `OFFLINE`.
 */

import type { DataSource } from "../types";
import type { NormalizedAgentEvent, NormalizedEventType } from "./contract";

export type RawAgentEvent = Record<string, unknown>;

/** The public semantic event set. Anything else normalizes to `unknown`. */
export const NORMALIZED_EVENT_TYPES: readonly NormalizedEventType[] = [
  "semantic.interpreted",
  "mission.planned",
  "run.started",
  "tool.started",
  "tool.completed",
  "tool.failed",
  "gateway.checked",
  "guardian.checked",
  "proposal.created",
  "approval.required",
  "run.completed",
  "run.failed",
  "run.stopped",
];

/** Streaming noise that must never become a timeline step. */
const IGNORED_EVENT_NAMES: ReadonlySet<string> = new Set([
  "message.delta",
  "reasoning.available",
  "reasoning.delta",
  "content.delta",
  "content",
  "reasoning",
  "heartbeat",
  "heartbeat.delta",
  "ping",
  "pong",
  "keepalive",
  "keep.alive",
  "token.delta",
  "stream.delta",
  "progress.delta",
]);

const TOOL_LABELS: Record<string, string> = {
  inspect_journey: "Inspect current Journey",
  inspect_twin: "Inspect JourneyTwin",
  list_replans: "Inspect proposals and protected commitments",
  search_city_services: "Search candidate places and services",
  request_replan: "Request deterministic replan",
  accept_replan: "Accept replan (CityNexus approval required)",
  replace_activity: "Replace activity (CityNexus approval required)",
  reschedule_activity: "Reschedule activity (CityNexus approval required)",
  create_booking: "Create booking (CityNexus approval required)",
  cancel_refundable_booking: "Cancel refundable booking (CityNexus approval required)",
  request_commitment_change: "Request commitment change (CityNexus approval required)",
};

const ALLOWED_STATUSES: ReadonlySet<string> = new Set([
  "started",
  "completed",
  "failed",
  "approval_required",
  "stopped",
]);

export interface NormalizeOptions {
  /** Run id stamped when the raw payload has none. */
  runId?: string | null;
  /** Data source stamped on every event. Defaults to `RECORDED_FIXTURE`. */
  source?: DataSource;
  /** Fallback timestamp when the raw payload has none. */
  receivedAt?: string;
  /** Fallback sequence number when the raw payload has none. */
  sequenceNo?: number;
}

function asString(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  const text = String(value);
  return text.length > 0 ? text : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Extract and canonicalize the raw event name (`_` -> `.`, lowercase). */
export function eventNameFromRaw(raw: RawAgentEvent): string {
  const candidate = raw.event_type ?? raw.event ?? raw.type ?? raw.name ?? raw.event_name;
  const text = asString(candidate);
  if (!text) return "run.started";
  const normalized = text.trim().toLowerCase().replaceAll("_", ".");
  return normalized.length > 0 ? normalized : "run.started";
}

/** True when the raw event is known streaming noise. */
export function isIgnoredRawEvent(input: unknown): boolean {
  if (!isRecord(input)) return false;
  return IGNORED_EVENT_NAMES.has(eventNameFromRaw(input));
}

/** Tool names may arrive namespaced as `citynexus__search_city_services`. */
export function toolNameFromRaw(raw: RawAgentEvent): string | null {
  const value = raw.tool_name ?? raw.tool ?? (typeof raw.name === "string" ? raw.name : undefined);
  if (value === null || value === undefined) return null;
  let name = String(value).trim();
  if (!name) return null;
  const separator = name.lastIndexOf("__");
  if (separator >= 0) name = name.slice(separator + 2).trim();
  return name.length > 0 ? name : null;
}

/** Bounded, non free-form result projection (mirrors `_safe_summary`). */
export function safeSummary(value: unknown): Record<string, unknown> | string | null {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) return { items: value.length };
  if (isRecord(value)) {
    const result: Record<string, unknown> = {};
    for (const key of [
      "decision",
      "status",
      "approval_status",
      "proposal_id",
      "mission_id",
      "executed",
      "error",
      "tool",
    ]) {
      const item = value[key];
      if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") {
        result[key] = item;
      }
    }
    if (Object.keys(result).length === 0) {
      result.keys = Object.keys(value).map((key) => String(key)).sort().slice(0, 20);
    }
    return result;
  }
  if (typeof value === "string") return { kind: "text", length: value.length };
  if (typeof value === "number" || typeof value === "boolean") return { value };
  return null;
}

/** Map an arbitrary event name to the semantic contract. */
export function normalizeEventType(
  name: string,
  raw: RawAgentEvent,
  tool: string | null,
): NormalizedEventType {
  if ((NORMALIZED_EVENT_TYPES as readonly string[]).includes(name)) {
    return name as NormalizedEventType;
  }
  if (name === "run" || name === "start" || name === "started" || name === "run.start") {
    return "run.started";
  }
  if (name === "completed" || name === "succeeded" || name === "success") {
    return "run.completed";
  }
  if (name === "failed" || name === "error" || name === "failure") {
    return "run.failed";
  }
  if (name === "stopped" || name === "cancelled" || name === "canceled" || name === "cancel") {
    return "run.stopped";
  }
  if (name.includes("approval")) return "approval.required";
  if (name.includes("gateway") || name.includes("policy")) return "gateway.checked";
  if (name.includes("guardian")) return "guardian.checked";
  if (name.includes("proposal") && name.includes("created")) return "proposal.created";
  if (tool) {
    if (name.includes("failed") || name.includes("error") || raw.error === true) return "tool.failed";
    if (
      name.includes("completed") ||
      name.includes("finished") ||
      name.includes("done") ||
      name.includes("ended") ||
      raw.status === "completed" ||
      raw.status === "succeeded"
    ) {
      return "tool.completed";
    }
    if (
      name.includes("start") ||
      name.includes("call") ||
      name.includes("begin") ||
      name.startsWith("tool") ||
      raw.status === "started"
    ) {
      return "tool.started";
    }
  }
  return "unknown";
}

function sequenceNoFromRaw(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return Math.trunc(value);
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return Math.trunc(parsed);
  }
  return null;
}

function timestampFromRaw(value: unknown, fallback: string): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    const milliseconds = value > 1e12 ? value : value * 1000;
    const date = new Date(milliseconds);
    return Number.isNaN(date.getTime()) ? fallback : date.toISOString();
  }
  if (typeof value === "string" && value.trim() !== "") return value;
  return fallback;
}

function durationMsFromRaw(raw: RawAgentEvent): number | null {
  const direct = raw.duration_ms;
  if (typeof direct === "number" && Number.isFinite(direct)) return Math.round(direct);
  if (typeof direct === "string" && direct.trim() !== "" && Number.isFinite(Number(direct))) {
    return Math.round(Number(direct));
  }
  const seconds = raw.duration;
  if (typeof seconds === "number" && Number.isFinite(seconds)) return Math.round(seconds * 1000);
  if (typeof seconds === "string" && seconds.trim() !== "" && Number.isFinite(Number(seconds))) {
    return Math.round(Number(seconds) * 1000);
  }
  return null;
}

function safeFallback(source: DataSource, receivedAt: string): NormalizedAgentEvent {
  return {
    id: "unknown:runtime",
    run_id: "",
    sequence_no: 0,
    event_type: "unknown",
    raw_event_type: "unknown",
    tool_name: null,
    friendly_label: "Hermes runtime",
    status: "started",
    timestamp: receivedAt,
    duration_ms: null,
    result_summary: null,
    policy_decision: null,
    source,
    received_at: receivedAt,
    unknown: true,
  };
}

/**
 * Normalize one raw runtime event. Returns `null` for noise or non-objects.
 * Never throws.
 */
export function normalizeRawEvent(
  input: unknown,
  options: NormalizeOptions = {},
): NormalizedAgentEvent | null {
  const receivedAt = options.receivedAt ?? new Date().toISOString();
  const source = options.source ?? "RECORDED_FIXTURE";
  if (!isRecord(input)) return null;
  const raw = input;

  try {
    const rawName = eventNameFromRaw(raw);
    if (IGNORED_EVENT_NAMES.has(rawName)) return null;

    const tool = toolNameFromRaw(raw);
    const eventType = normalizeEventType(rawName, raw, tool);
    const sequenceNo =
      sequenceNoFromRaw(raw.sequence_no) ??
      sequenceNoFromRaw(raw.sequence) ??
      sequenceNoFromRaw(raw.seq) ??
      sequenceNoFromRaw(raw.sequenceNumber) ??
      (typeof options.sequenceNo === "number" ? options.sequenceNo : 0);
    const explicitId = asString(raw.id) ?? asString(raw.event_id) ?? asString(raw.eventId);
    const runId = asString(options.runId) ?? asString(raw.run_id) ?? asString(raw.runId) ?? "";
    const id = explicitId ?? `${runId}:${sequenceNo}:${eventType}:${tool ?? "none"}`;

    const timestamp = timestampFromRaw(raw.timestamp ?? raw.created_at ?? raw.started_at, receivedAt);
    const durationMs = durationMsFromRaw(raw);

    const resultCandidate =
      raw.result ?? raw.output ?? (raw.error !== undefined ? { error: raw.error } : undefined);
    let resultSummary: Record<string, unknown> | string | null =
      isRecord(raw.result_summary) || typeof raw.result_summary === "string"
        ? (raw.result_summary as Record<string, unknown> | string)
        : null;
    if (resultSummary === null && resultCandidate !== undefined) resultSummary = safeSummary(resultCandidate);
    if (resultSummary === null && typeof raw.summary === "string" && raw.summary.length > 0) {
      resultSummary = raw.summary;
    }

    const decision =
      raw.policy_decision ??
      raw.decision ??
      (isRecord(resultCandidate) ? resultCandidate.decision : undefined);

    const friendlyLabel =
      asString(raw.friendly_label) ??
      (typeof raw.summary === "string" && raw.summary.length > 0 ? raw.summary : null) ??
      (tool ? TOOL_LABELS[tool] ?? tool : null) ??
      "Hermes runtime";

    let status = (asString(raw.status) ?? "started").toLowerCase();
    if (eventType.endsWith("completed")) status = "completed";
    else if (eventType.endsWith("failed")) status = "failed";
    else if (eventType === "approval.required") status = "approval_required";
    else if (eventType.endsWith("stopped")) status = "stopped";
    else if (!ALLOWED_STATUSES.has(status)) status = "started";

    const normalized: NormalizedAgentEvent = {
      id,
      run_id: runId,
      sequence_no: sequenceNo,
      event_type: eventType,
      raw_event_type: rawName,
      tool_name: tool,
      friendly_label: friendlyLabel,
      status,
      timestamp,
      duration_ms: durationMs,
      result_summary: resultSummary,
      policy_decision: asString(decision),
      source,
      received_at: receivedAt,
      unknown: eventType === "unknown",
    };

    const approvalId =
      asString(raw.approval_id) ??
      (isRecord(resultCandidate) ? asString(resultCandidate.approval_id) : null);
    const proposalId =
      asString(raw.proposal_id) ??
      (isRecord(resultCandidate) ? asString(resultCandidate.proposal_id) : null);
    const missionId =
      asString(raw.mission_id) ??
      (isRecord(resultCandidate) ? asString(resultCandidate.mission_id) : null);
    const approvalStatus =
      asString(raw.approval_status) ??
      (isRecord(resultCandidate)
        ? asString(resultCandidate.approval_status) ?? asString(resultCandidate.status)
        : null);

    if (approvalId) normalized.approval_id = approvalId;
    if (proposalId) normalized.proposal_id = proposalId;
    if (missionId) normalized.mission_id = missionId;
    if (approvalStatus) normalized.approval_status = approvalStatus;

    return normalized;
  } catch {
    return safeFallback(source, receivedAt);
  }
}

/** Normalize a batch, dropping noise and non-objects. */
export function normalizeRawEvents(
  inputs: readonly unknown[],
  options: NormalizeOptions = {},
): NormalizedAgentEvent[] {
  const output: NormalizedAgentEvent[] = [];
  for (const input of inputs) {
    const normalized = normalizeRawEvent(input, options);
    if (normalized) output.push(normalized);
  }
  return output;
}

/**
 * Compatibility wrapper: normalize a single raw event with an explicit
 * arrival index used as the fallback sequence number.
 */
export function normalizeAgentEvent(
  raw: RawAgentEvent,
  options: {
    runId?: string | null;
    source: DataSource;
    arrivalIndex?: number;
    receivedAt?: string;
  },
): NormalizedAgentEvent | null {
  return normalizeRawEvent(raw, {
    runId: options.runId,
    source: options.source,
    receivedAt: options.receivedAt,
    sequenceNo: options.arrivalIndex,
  });
}

/** Compatibility wrapper: normalize a batch with arrival-index sequencing. */
export function normalizeEventBatch(
  raws: readonly RawAgentEvent[],
  options: { runId?: string | null; source: DataSource; receivedAt?: string },
): NormalizedAgentEvent[] {
  return raws
    .map((raw, index) => normalizeAgentEvent(raw, { ...options, arrivalIndex: index }))
    .filter((event): event is NormalizedAgentEvent => event !== null);
}
