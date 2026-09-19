/**
 * Append-only, de-duplicating, stable-order runtime event store.
 *
 * Hot paths use `Map` indexes so appends are O(1) amortized; only an explicit
 * `snapshot()` sorts, and the sorted list is cached until the next insert.
 * This keeps 100/300/1000-event runs responsive without an O(n^2) append path.
 *
 * Ordering is stable by `sequence_no`, then `timestamp`, then arrival order.
 * Duplicate detection uses `id` when present, otherwise
 * `run_id + sequence_no + event_type + tool_name`.
 */

import type { DataSource, RuntimeIdentity } from "../types";
import type {
  NormalizedAgentEvent,
  NormalizedRun,
  NormalizedRunStatus,
} from "./contract";
import type { NormalizeOptions, RawAgentEvent } from "./normalize";
import { normalizeRawEvent } from "./normalize";

export interface EventStoreOptions {
  source?: DataSource;
  normalizeOptions?: NormalizeOptions;
  /** Called with newly inserted events (stable order) after each append. */
  onInsert?: (inserted: NormalizedAgentEvent[]) => void;
}

export type AppendOptions = NormalizeOptions;

function isNormalizedEvent(value: unknown): value is NormalizedAgentEvent {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.event_type === "string" &&
    typeof candidate.received_at === "string" &&
    typeof candidate.unknown === "boolean" &&
    typeof candidate.sequence_no === "number"
  );
}

function rawIdOf(value: unknown): string | null {
  if (typeof value !== "object" || value === null) return null;
  const candidate = value as Record<string, unknown>;
  const id = candidate.id ?? candidate.event_id ?? candidate.eventId;
  return typeof id === "string" && id.length > 0 ? id : null;
}

function timestampMs(event: NormalizedAgentEvent): number {
  const parsed = Date.parse(event.timestamp);
  return Number.isFinite(parsed) ? parsed : 0;
}

/** Stable comparator: sequence, then timestamp, then received/arrival time. */
export function compareNormalizedEvents(a: NormalizedAgentEvent, b: NormalizedAgentEvent): number {
  if (a.sequence_no !== b.sequence_no) return a.sequence_no - b.sequence_no;
  const ta = timestampMs(a);
  const tb = timestampMs(b);
  if (ta !== tb) return ta - tb;
  return a.received_at.localeCompare(b.received_at);
}

/** Derive a run status from an event stream (terminal truth wins). */
export function deriveRunStatus(events: readonly NormalizedAgentEvent[]): NormalizedRunStatus {
  if (events.length === 0) return "idle";
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index];
    switch (event.event_type) {
      case "run.completed":
        return "success";
      case "run.failed":
      case "tool.failed":
        return "failed";
      case "run.stopped":
        return "stopped";
      case "approval.required":
      case "proposal.created":
        return "approval_required";
      case "run.started":
      case "semantic.interpreted":
      case "mission.planned":
      case "tool.started":
      case "tool.completed":
      case "gateway.checked":
      case "guardian.checked":
        return "running";
      default:
        continue;
    }
  }
  return "idle";
}

export interface BuildRunInput {
  runId: string;
  journeyId: string;
  runtimeIdentity: RuntimeIdentity;
  providerKey?: string;
  modelKey?: string;
  events: readonly NormalizedAgentEvent[];
  source: DataSource;
  status?: NormalizedRunStatus;
  startedAt?: string;
  completedAt?: string | null;
  lastUpdated?: string;
}

/** Assemble the `NormalizedRun` projection from normalized events. */
export function buildNormalizedRun(input: BuildRunInput): NormalizedRun {
  const events = input.events.slice().sort(compareNormalizedEvents);
  const status = input.status ?? deriveRunStatus(events);
  const startedEvent = events.find((event) => event.event_type === "run.started") ?? events[0];
  const terminal = [...events]
    .reverse()
    .find(
      (event) =>
        event.event_type === "run.completed" ||
        event.event_type === "run.failed" ||
        event.event_type === "run.stopped",
    );
  const toolStarts = events.filter((event) => event.event_type === "tool.started");
  const completed = status === "success" || status === "failed" || status === "stopped";
  return {
    run_id: input.runId,
    journey_id: input.journeyId,
    runtime_identity: input.runtimeIdentity,
    provider_key: input.providerKey ?? "unknown",
    model_key: input.modelKey ?? "unknown",
    status,
    source: input.source,
    started_at: input.startedAt ?? startedEvent?.timestamp,
    completed_at: input.completedAt ?? (completed ? terminal?.timestamp ?? null : null),
    events,
    current_tool: toolStarts.length > 0 ? toolStarts[toolStarts.length - 1].tool_name : null,
    tool_count: toolStarts.length,
    last_updated: input.lastUpdated ?? events[events.length - 1]?.received_at ?? new Date().toISOString(),
  };
}

export class EventStore {
  private readonly options: EventStoreOptions;
  private readonly byKey = new Map<string, NormalizedAgentEvent>();
  private readonly arrivalById = new Map<string, number>();
  private readonly events: NormalizedAgentEvent[] = [];
  private sortedCache: NormalizedAgentEvent[] | null = null;
  private arrivalCounter = 0;
  private lastSequence = 0;

  constructor(sourceOrOptions: DataSource | EventStoreOptions = {}) {
    this.options = typeof sourceOrOptions === "string" ? { source: sourceOrOptions } : sourceOrOptions;
  }

  private keyFor(raw: unknown, event: NormalizedAgentEvent): string {
    const explicit = rawIdOf(raw);
    if (explicit) return `id:${explicit}`;
    return `k:${event.run_id}:${event.sequence_no}:${event.event_type}:${event.tool_name ?? "none"}`;
  }

  /**
   * Append raw and/or already-normalized events. Returns only newly inserted
   * events, in stable order; duplicates are ignored.
   */
  append(
    input: unknown | readonly unknown[],
    options: AppendOptions = {},
  ): NormalizedAgentEvent[] {
    const items = Array.isArray(input) ? input : [input];
    const normalizeOptions: NormalizeOptions = {
      ...this.options.normalizeOptions,
      ...options,
      source: options.source ?? this.options.source ?? this.options.normalizeOptions?.source,
    };
    const inserted: NormalizedAgentEvent[] = [];

    for (const item of items) {
      let event: NormalizedAgentEvent | null;
      if (isNormalizedEvent(item)) {
        event = options.source ? { ...item, source: options.source } : item;
      } else {
        event = normalizeRawEvent(item, normalizeOptions);
      }
      if (!event) continue;
      const key = this.keyFor(item, event);
      if (this.byKey.has(key)) continue;
      const arrival = this.arrivalCounter;
      this.arrivalCounter += 1;
      this.arrivalById.set(event.id, arrival);
      this.byKey.set(key, event);
      this.events.push(event);
      if (event.sequence_no > this.lastSequence) this.lastSequence = event.sequence_no;
      inserted.push(event);
    }

    if (inserted.length === 0) return inserted;
    this.sortedCache = null;
    const ordered = inserted.slice().sort((a, b) => this.compareWithArrival(a, b));
    this.options.onInsert?.(ordered);
    return ordered;
  }

  /** Compatibility alias for callers that append raw batches with a run id. */
  appendRaw(raws: RawAgentEvent | readonly RawAgentEvent[], runId?: string | null): NormalizedAgentEvent[] {
    return this.append(raws, { runId: runId ?? undefined });
  }

  private compareWithArrival(a: NormalizedAgentEvent, b: NormalizedAgentEvent): number {
    const base = compareNormalizedEvents(a, b);
    if (base !== 0) return base;
    const aa = this.arrivalById.get(a.id) ?? 0;
    const ab = this.arrivalById.get(b.id) ?? 0;
    return aa - ab;
  }

  /** Stable, sorted snapshot of every stored event. */
  snapshot(): NormalizedAgentEvent[] {
    if (this.sortedCache === null) {
      this.sortedCache = this.events.slice().sort((a, b) => this.compareWithArrival(a, b));
    }
    return this.sortedCache.slice();
  }

  /** Highest sequence number seen (0 when empty). */
  getLastSequence(): number {
    return this.lastSequence;
  }

  /** Derived run status, optionally scoped to one run id. */
  getStatus(runId?: string): NormalizedRunStatus {
    return deriveRunStatus(runId ? this.eventsFor(runId) : this.events);
  }

  /** Alias used by older call sites. */
  status(): NormalizedRunStatus {
    return this.getStatus();
  }

  size(): number {
    return this.events.length;
  }

  clear(): void {
    this.events.length = 0;
    this.byKey.clear();
    this.arrivalById.clear();
    this.sortedCache = null;
    this.arrivalCounter = 0;
    this.lastSequence = 0;
  }

  eventsFor(runId: string): NormalizedAgentEvent[] {
    return this.events.filter((event) => event.run_id === runId);
  }

  currentTool(runId?: string): string | null {
    const source = runId ? this.eventsFor(runId) : this.events;
    for (let index = source.length - 1; index >= 0; index -= 1) {
      const tool = source[index].tool_name;
      if (tool) return tool;
    }
    return null;
  }

  toolCount(runId?: string): number {
    const source = runId ? this.eventsFor(runId) : this.events;
    return source.filter((event) => event.event_type === "tool.started").length;
  }

  has(key: string): boolean {
    return this.byKey.has(key);
  }
}

/** Backwards-compatible alias for the store class name. */
export { EventStore as AgentEventStore };

export type { RawAgentEvent };
