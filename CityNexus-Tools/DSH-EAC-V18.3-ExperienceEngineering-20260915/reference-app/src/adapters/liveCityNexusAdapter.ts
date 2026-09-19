/**
 * LiveCityNexusAdapter — the real CityNexus REST/SSE contract at `/api/v1`.
 *
 * Source honesty:
 * - `source: "LIVE"` is reported only after a real HTTP response or SSE frame
 *   has been received.
 * - When fetch/EventSource fails the adapter never invents runtime progress.
 *   It surfaces a retryable `onError` and falls back to OfflineSnapshotAdapter
 *   semantics (`source: "OFFLINE"`).
 * - Approval success is shown only after server truth returns; network losses
 *   never become authoritative success.
 *
 * Reconnect policy:
 * - SSE is re-opened with `?since_sequence=` and a `last_event_id` query value
 *   (browsers also send `Last-Event-ID`); duplicate frames are de-duplicated by
 *   EventStore and a payload signature set.
 * - Backoff is bounded to 3 attempts. Timers are used only for network
 *   reconnect, never to generate events.
 */

import type {
  DataSource,
  PulseState,
  RecoveryProposal,
  RuntimeIdentity,
  RuntimeStatus,
} from "../types";
import type {
  AdapterMode,
  ApprovalDecisionInput,
  ApprovalDecisionResult,
  CopilotMissionStart,
  ExperienceAdapter,
  MapState,
  NormalizedAgentEvent,
  NormalizedProposal,
  NormalizedRun,
  NormalizedRunStatus,
  RunEventHandlers,
  RunSubscription,
  RuntimeStatusInfo,
  StopResult,
} from "./contract";
import { EventStore, buildNormalizedRun } from "./eventStore";
import { NORMALIZED_EVENT_TYPES } from "./normalize";
import type { RawAgentEvent } from "./normalize";
import { OfflineSnapshotAdapter } from "./offlineSnapshotAdapter";

type RawEvent = RawAgentEvent;

export const LIVE_API_BASE = "/api/v1";
const DEFAULT_JOURNEY_ID = "journey-reference-tianjin-20260915";
const MAX_SSE_ATTEMPTS = 3;
const DEFAULT_REQUEST_TIMEOUT_MS = 15_000;

export interface LiveMessageEvent {
  data?: string;
  lastEventId?: string;
  type?: string;
}

export interface EventSourceLike {
  addEventListener(type: string, listener: (event: LiveMessageEvent) => void): void;
  removeEventListener?(type: string, listener: (event: LiveMessageEvent) => void): void;
  close(): void;
  onopen?: ((event: unknown) => void) | null;
  onerror?: ((event: unknown) => void) | null;
  readyState?: number;
}

export type EventSourceFactory = (url: string) => EventSourceLike;

export interface LiveDiagnostic {
  message: string;
  source: DataSource;
  retryable: boolean;
  detail?: string;
}

export interface LiveCityNexusOptions {
  baseUrl?: string;
  journeyId?: string;
  fetchImpl?: typeof fetch;
  eventSourceFactory?: EventSourceFactory;
  requestTimeoutMs?: number;
  onDiagnostic?: (diagnostic: LiveDiagnostic) => void;
}

export class AdapterHttpError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.name = "AdapterHttpError";
    this.status = status;
    this.body = body;
  }
}

function isAdapterHttpError(error: unknown): error is AdapterHttpError {
  return error instanceof AdapterHttpError;
}

function defaultEventSourceFactory(url: string): EventSourceLike {
  const globalObject = globalThis as { EventSource?: new (url: string) => EventSourceLike };
  if (typeof globalObject.EventSource !== "function") {
    throw new AdapterHttpError(0, null, "EventSource is not available in this environment");
  }
  return new globalObject.EventSource(url);
}

function journeyIdFromLocation(): string | null {
  if (typeof window === "undefined") return null;
  const value = new URLSearchParams(window.location.search).get("journey");
  return value && value.length > 0 ? value : null;
}

function asText(value: unknown): string | undefined {
  if (value === null || value === undefined) return undefined;
  const text = String(value);
  return text.length > 0 ? text : undefined;
}

function mapRuntimeIdentity(value: unknown): RuntimeIdentity {
  const text = String(value ?? "").toUpperCase();
  if (
    text === "DIRECT" ||
    text === "HERMES_NATIVE_MCP" ||
    text === "HERMES_COMPAT_ENDPOINT" ||
    text === "NATIVE_DEEPSEEK_TOOL_LOOP" ||
    text === "FALLBACK" ||
    text === "UNAVAILABLE"
  ) {
    return text;
  }
  return "UNAVAILABLE";
}

function mapRunStatus(value: unknown): NormalizedRunStatus | null {
  const status = String(value ?? "").toLowerCase();
  if (["failed", "error", "failure"].includes(status)) return "failed";
  if (["stopped", "cancelled", "canceled"].includes(status)) return "stopped";
  if (["completed", "succeeded", "success", "done"].includes(status)) return "success";
  if (["approval_required", "awaiting_approval", "pending_approval"].includes(status)) {
    return "approval_required";
  }
  if (["running", "started", "in_progress", "active", "processing"].includes(status)) return "running";
  return null;
}

function runtimeStatusFromPayload(payload: RawEvent): RuntimeStatusInfo {
  const identity = mapRuntimeIdentity(payload.runtime_identity);
  let status: RuntimeStatus = "ready";
  if (identity === "UNAVAILABLE") status = "hermes_unavailable";
  else if (payload.deepseek_configured === false) status = "deepseek_unavailable";
  else if (payload.native_binary_detected === false && payload.hermes_compat_configured === false) {
    status = "hermes_unavailable";
  }
  return {
    identity,
    status,
    source: "LIVE",
    last_updated: new Date().toISOString(),
    detail: asText(payload.mcp_server) ? `MCP server: ${asText(payload.mcp_server)}` : undefined,
  };
}

function intentFromPayload(payload: RawEvent): string {
  const intent = payload.intent;
  if (intent && typeof intent === "object") {
    const record = intent as RawEvent;
    const envelope = record.semantic_envelope;
    if (envelope && typeof envelope === "object") {
      const envelopeIntent = (envelope as RawEvent).intent;
      if (typeof envelopeIntent === "string" && envelopeIntent.length > 0) return envelopeIntent;
    }
    if (typeof record.name === "string" && record.name.length > 0) return record.name;
  }
  return "MESSAGE";
}

export class LiveCityNexusAdapter implements ExperienceAdapter {
  readonly mode: AdapterMode = "live";
  readonly source: DataSource = "LIVE";

  private readonly baseUrl: string;
  private readonly defaultJourneyId: string;
  private readonly fetchImpl: typeof fetch;
  private readonly eventSourceFactory: EventSourceFactory;
  private readonly requestTimeoutMs: number;
  private readonly onDiagnostic?: (diagnostic: LiveDiagnostic) => void;
  private readonly offline = new OfflineSnapshotAdapter();
  private readonly runJourneyIds = new Map<string, string>();
  private lastDiagnostic: LiveDiagnostic | null = null;

  constructor(options: LiveCityNexusOptions = {}) {
    this.baseUrl = options.baseUrl ?? LIVE_API_BASE;
    this.defaultJourneyId = options.journeyId ?? journeyIdFromLocation() ?? DEFAULT_JOURNEY_ID;
    this.fetchImpl = options.fetchImpl ?? ((input, init) => fetch(input, init));
    this.eventSourceFactory = options.eventSourceFactory ?? defaultEventSourceFactory;
    this.requestTimeoutMs = options.requestTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS;
    this.onDiagnostic = options.onDiagnostic;
  }

  getLastUpdated(): string {
    return new Date().toISOString();
  }

  getLastDiagnostic(): LiveDiagnostic | null {
    return this.lastDiagnostic;
  }

  // ---------------------------------------------------------------- read-only
  async getJourneyPulse(): Promise<PulseState> {
    this.diagnose("live journey pulse projection is not exposed by the required endpoint set", "OFFLINE", true);
    return this.offline.getJourneyPulse();
  }

  async getRuntimeStatus(): Promise<RuntimeStatusInfo> {
    try {
      const payload = await this.requestJson<RawEvent>("/agent/runtime-status");
      return runtimeStatusFromPayload(payload);
    } catch (error) {
      this.diagnose("live runtime status unavailable", "OFFLINE", true, error);
      return this.offline.getRuntimeStatus();
    }
  }

  async getRecoveryDiff(proposalId?: string): Promise<RecoveryProposal | null> {
    this.diagnose(
      "live recovery projection requires the journey recovery endpoint; using cached snapshot",
      "OFFLINE",
      true,
    );
    return this.offline.getRecoveryDiff(proposalId);
  }

  async getMapState(): Promise<MapState> {
    const journeyId = this.journeyIdFor();
    try {
      const payload = await this.requestJson<RawEvent>(`/journeys/${journeyId}/route-evidence`);
      return this.mapRouteEvidence(payload, journeyId);
    } catch (error) {
      this.diagnose("live route evidence unavailable", "OFFLINE", true, error);
      return this.offline.getMapState();
    }
  }

  async getTodayTimeline() {
    return this.offline.getTodayTimeline();
  }

  async getProposal(proposalId?: string): Promise<NormalizedProposal | null> {
    this.diagnose("live proposal projection is not exposed by the required endpoint set", "OFFLINE", true);
    return this.offline.getProposal(proposalId);
  }

  // ------------------------------------------------------------------- copilot
  async startCopilotMission(input: { message: string; locale: "en" | "zh-CN" }): Promise<CopilotMissionStart> {
    const journeyId = this.journeyIdFor();
    try {
      const payload = await this.requestJson<RawEvent>(`/journeys/${journeyId}/copilot/messages`, {
        method: "POST",
        body: JSON.stringify({ message: input.message, locale: input.locale === "zh-CN" ? "zh" : "en" }),
      });
      const agentRun = payload.agent_run;
      const semanticIntent = intentFromPayload(payload);
      const answer = asText(payload.message) ?? "CityNexus responded.";
      if (agentRun && typeof agentRun === "object") {
        const runPayload = agentRun as RawEvent;
        const runId = asText(runPayload.run_id) ?? asText(runPayload.id);
        if (runId) {
          this.runJourneyIds.set(runId, journeyId);
          const initial = Array.isArray(runPayload.initial_events) ? runPayload.initial_events : [];
          const events = this.normalizeLiveEvents(initial, runId);
          const run = this.buildLiveRun(runPayload, runId, journeyId, events);
          return {
            mission_id: asText(runPayload.mission_id) ?? asText(payload.mission_id) ?? runId,
            run,
            semantic_intent: semanticIntent,
            answer,
            source: "LIVE",
          };
        }
      }
      // The server answered honestly but did not start a run.
      const idleRun = buildNormalizedRun({
        runId: "no-run",
        journeyId,
        runtimeIdentity: "DIRECT",
        providerKey: "citynexus",
        modelKey: "none",
        events: [],
        source: "LIVE",
        status: "idle",
        lastUpdated: new Date().toISOString(),
      });
      return {
        mission_id: asText(payload.mission_id) ?? "mission",
        run: idleRun,
        semantic_intent: semanticIntent,
        answer,
        source: "LIVE",
      };
    } catch (error) {
      this.diagnose("live copilot mission failed", "OFFLINE", true, error);
      const fallback = await this.offline.startCopilotMission(input);
      return { ...fallback, answer: `Live CityNexus is unreachable. ${fallback.answer}` };
    }
  }

  async getRun(runId: string): Promise<NormalizedRun | null> {
    const journeyId = this.journeyIdFor(runId);
    let sawNetworkFailure = false;
    let sawNotFound = false;
    const safeRequest = async (path: string): Promise<RawEvent | null> => {
      try {
        return await this.requestJson<RawEvent>(path);
      } catch (error) {
        if (isAdapterHttpError(error) && error.status === 404) sawNotFound = true;
        else sawNetworkFailure = true;
        return null;
      }
    };
    const timeline = await safeRequest(
      `/journeys/${journeyId}/agent/hermes/runs/${encodeURIComponent(runId)}/timeline`,
    );
    const runPayload = await safeRequest(
      `/journeys/${journeyId}/agent/hermes/runs/${encodeURIComponent(runId)}`,
    );
    if (!timeline && !runPayload) {
      if (sawNetworkFailure && !sawNotFound) {
        this.diagnose("live run lookup failed", "OFFLINE", true);
        return this.offline.getRun(runId);
      }
      return null;
    }
    const rawEvents = Array.isArray(timeline?.events)
      ? timeline.events
      : Array.isArray(runPayload?.initial_events)
        ? runPayload.initial_events
        : [];
    const events = this.normalizeLiveEvents(rawEvents, runId);
    const observability =
      timeline?.observability && typeof timeline.observability === "object"
        ? (timeline.observability as RawEvent)
        : {};
    const merged: RawEvent = {
      ...observability,
      ...runPayload,
      run_id: runId,
      journey_id: journeyId,
      runtime_identity: runPayload?.runtime_identity ?? timeline?.runtime_identity ?? "HERMES_NATIVE_MCP",
    };
    return this.buildLiveRun(merged, runId, journeyId, events);
  }

  subscribeRunEvents(
    runId: string,
    handlers: RunEventHandlers,
    options?: { since_sequence?: number },
  ): RunSubscription {
    const journeyId = this.journeyIdFor(runId);
    const store = new EventStore({ source: "LIVE" });
    const signatures = new Set<string>();
    let closed = false;
    let usingOffline = false;
    let attempt = 0;
    let lastEventId = "";
    let eventSource: EventSourceLike | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let offlineSubscription: RunSubscription | null = null;

    const sinceStart = options?.since_sequence ?? 0;
    if (sinceStart > store.getLastSequence()) {
      // The cursor is a caller hint only; the server still owns sequence truth.
      store.append([], { source: "LIVE", runId });
    }

    const currentRun = (): NormalizedRun =>
      buildNormalizedRun({
        runId,
        journeyId,
        runtimeIdentity: "HERMES_NATIVE_MCP",
        providerKey: "hermes-native",
        modelKey: "unknown",
        events: store.snapshot(),
        source: "LIVE",
        lastUpdated: new Date().toISOString(),
      });

    const fallbackToOffline = (message: string): void => {
      if (usingOffline || closed) return;
      usingOffline = true;
      handlers.onError?.({ message, retryable: true, source: "LIVE" });
      offlineSubscription = this.offline.subscribeRunEvents(runId, handlers, options);
    };

    const handleMessage = (event: LiveMessageEvent): void => {
      if (closed || usingOffline) return;
      const data = typeof event.data === "string" ? event.data : "";
      if (!data) return;
      let raw: RawEvent;
      try {
        raw = JSON.parse(data) as RawEvent;
      } catch {
        handlers.onError?.({ message: "Malformed SSE frame ignored", retryable: true, source: "LIVE" });
        return;
      }
      if (event.lastEventId) lastEventId = event.lastEventId;
      const signature = JSON.stringify(raw);
      if (signatures.has(signature)) return;
      signatures.add(signature);
      const inserted = store.append(raw, { source: "LIVE", runId });
      if (inserted.length === 0) return;
      for (const item of inserted) handlers.onEvent(item);
      handlers.onStatusChange?.(currentRun());
    };

    const closeSource = (): void => {
      if (!eventSource) return;
      try {
        eventSource.close();
      } catch {
        // Closing a failed EventSource is best-effort.
      }
      eventSource = null;
    };

    const handleSseError = (): void => {
      closeSource();
      if (closed || usingOffline) return;
      if (attempt < MAX_SSE_ATTEMPTS) {
        attempt += 1;
        handlers.onReconnect?.({ attempt, since_sequence: store.getLastSequence() });
        const delay = Math.min(4000, 500 * 2 ** (attempt - 1));
        retryTimer = setTimeout(open, delay);
        return;
      }
      fallbackToOffline("Live SSE unavailable after bounded retries; showing the offline snapshot.");
    };

    const open = (): void => {
      if (closed || usingOffline) return;
      const params = new URLSearchParams();
      params.set("since_sequence", String(store.getLastSequence()));
      if (lastEventId) params.set("last_event_id", lastEventId);
      const url =
        `${this.baseUrl}/journeys/${encodeURIComponent(journeyId)}/agent/hermes/runs/` +
        `${encodeURIComponent(runId)}/events?${params.toString()}`;
      let next: EventSourceLike;
      try {
        next = this.eventSourceFactory(url);
      } catch (error) {
        this.diagnose("EventSource could not be created", "OFFLINE", true, error);
        fallbackToOffline("Live SSE could not be opened; showing the offline snapshot.");
        return;
      }
      eventSource = next;
      next.onopen = () => {
        attempt = 0;
      };
      next.onerror = () => {
        handleSseError();
      };
      const listener = (event: LiveMessageEvent): void => handleMessage(event);
      const eventTypes = [...NORMALIZED_EVENT_TYPES, "message", "unknown"];
      for (const type of eventTypes) next.addEventListener(type, listener);
    };

    open();

    return {
      unsubscribe: () => {
        closed = true;
        if (retryTimer !== null) {
          clearTimeout(retryTimer);
          retryTimer = null;
        }
        closeSource();
        offlineSubscription?.unsubscribe();
        offlineSubscription = null;
      },
      getLastSequence: () => store.getLastSequence(),
      isLive: () => !closed && !usingOffline,
    };
  }

  async stopRun(runId: string): Promise<StopResult> {
    const journeyId = this.journeyIdFor(runId);
    try {
      const payload = await this.requestJson<RawEvent>(
        `/journeys/${journeyId}/agent/hermes/runs/${encodeURIComponent(runId)}/stop`,
        { method: "POST" },
      );
      return {
        ok: true,
        run_id: runId,
        status: mapRunStatus(payload?.status) ?? "stopped",
        reason: asText(payload?.failure_reason),
        source: "LIVE",
      };
    } catch (error) {
      if (isAdapterHttpError(error)) {
        return {
          ok: false,
          run_id: runId,
          status: "running",
          reason: `http_${error.status}`,
          source: "LIVE",
        };
      }
      this.diagnose("live stop failed", "OFFLINE", true, error);
      return { ok: false, run_id: runId, status: "running", reason: "network_loss", source: "OFFLINE" };
    }
  }

  async submitApprovalDecision(input: ApprovalDecisionInput): Promise<ApprovalDecisionResult> {
    const lastUpdated = new Date().toISOString();
    if (!input.online) {
      return {
        state: "approval_required",
        server_truth: false,
        proposal_id: input.proposal_id,
        approval_id: input.approval_id,
        reason: "offline",
        retryable: true,
        message: "Offline: approval is disabled until authoritative truth returns.",
        last_updated: lastUpdated,
      };
    }
    if (!input.approval_id) {
      return {
        state: "approval_required",
        server_truth: false,
        proposal_id: input.proposal_id,
        reason: "failed",
        retryable: false,
        message: "No server approval_id is available for this proposal.",
        last_updated: lastUpdated,
      };
    }
    const journeyId = this.journeyIdFor();
    try {
      const payload = await this.requestJson<RawEvent>(
        `/journeys/${journeyId}/agent/approvals/${encodeURIComponent(input.approval_id)}/approve`,
        { method: "POST", body: JSON.stringify({ approval_method: "USER_CONFIRMATION" }) },
      );
      const status = String(payload?.status ?? "PENDING").toUpperCase();
      const base = {
        proposal_id: input.proposal_id,
        approval_id: input.approval_id,
        server_truth: true,
        last_updated: new Date().toISOString(),
      };
      if (status === "APPROVED" || status === "CONSUMED") {
        return { ...base, state: "approved", retryable: false, message: `Server truth: ${status}` };
      }
      if (status === "REVOKED") {
        return { ...base, state: "rejected", retryable: false, message: "Server truth: REVOKED" };
      }
      if (status === "EXPIRED") {
        return {
          ...base,
          state: "approval_required",
          reason: "expired",
          retryable: false,
          message: "Server truth: approval expired; refresh for a new proposal.",
        };
      }
      return {
        ...base,
        state: "approval_required",
        retryable: true,
        message: `Server truth: ${status}`,
      };
    } catch (error) {
      if (isAdapterHttpError(error)) {
        const bodyText = JSON.stringify(error.body ?? "").toLowerCase();
        if (error.status === 409) {
          const reason =
            bodyText.includes("expired")
              ? "expired"
              : bodyText.includes("consum")
                ? "already_consumed"
                : "superseded";
          return {
            state: reason === "already_consumed" ? "approved" : "approval_required",
            server_truth: true,
            proposal_id: input.proposal_id,
            approval_id: input.approval_id,
            reason,
            retryable: false,
            message: `Server truth 409: ${reason}. Refresh before retrying.`,
            last_updated: new Date().toISOString(),
          };
        }
        if (error.status === 404) {
          return {
            state: "approval_required",
            server_truth: true,
            proposal_id: input.proposal_id,
            approval_id: input.approval_id,
            reason: "failed",
            retryable: false,
            message: "Server truth 404: approval was not found.",
            last_updated: new Date().toISOString(),
          };
        }
        return {
          state: "approval_required",
          server_truth: true,
          proposal_id: input.proposal_id,
          approval_id: input.approval_id,
          reason: "failed",
          retryable: false,
          message: `Server truth ${error.status}: approval did not apply.`,
          last_updated: new Date().toISOString(),
        };
      }
      this.diagnose("live approval failed", "OFFLINE", true, error);
      return {
        state: "approval_required",
        server_truth: false,
        proposal_id: input.proposal_id,
        approval_id: input.approval_id,
        reason: "network_loss",
        retryable: true,
        message: "Network loss during approval. No authoritative success is shown.",
        last_updated: new Date().toISOString(),
      };
    }
  }

  // ------------------------------------------------------------------ internals
  private journeyIdFor(_runId?: string): string {
    if (_runId) {
      const mapped = this.runJourneyIds.get(_runId);
      if (mapped) return mapped;
    }
    return this.defaultJourneyId;
  }

  private normalizeLiveEvents(rawEvents: readonly unknown[], runId: string): NormalizedAgentEvent[] {
    const store = new EventStore({ source: "LIVE" });
    store.append(rawEvents, { source: "LIVE", runId });
    return store.snapshot();
  }

  private buildLiveRun(
    payload: RawEvent,
    runId: string,
    journeyId: string,
    events: NormalizedAgentEvent[],
  ): NormalizedRun {
    const statusHint = mapRunStatus(payload.status) ?? undefined;
    return buildNormalizedRun({
      runId,
      journeyId: asText(payload.journey_id) ?? journeyId,
      runtimeIdentity: mapRuntimeIdentity(payload.runtime_identity ?? "HERMES_NATIVE_MCP"),
      providerKey: asText(payload.provider_key),
      modelKey: asText(payload.model_key),
      events,
      source: "LIVE",
      status: statusHint,
      startedAt: asText(payload.started_at),
      completedAt: payload.completed_at === null ? null : asText(payload.completed_at),
      lastUpdated: new Date().toISOString(),
    });
  }

  private mapRouteEvidence(payload: RawEvent, journeyId: string): MapState {
    const feature = (payload.new_route ?? payload.old_route) as RawEvent | undefined;
    const geometry = feature?.geometry as RawEvent | undefined;
    const coordinates = Array.isArray(geometry?.coordinates)
      ? (geometry?.coordinates as Array<[number, number]>)
      : [];
    if (coordinates.length === 0) {
      throw new AdapterHttpError(0, payload, "route evidence contained no geometry");
    }
    const markerCollection = payload.markers as RawEvent | undefined;
    const markerFeatures = Array.isArray(markerCollection?.features)
      ? (markerCollection?.features as RawEvent[])
      : [];
    const stops = markerFeatures
      .map((marker, index) => {
        const properties = (marker.properties ?? {}) as RawEvent;
        const markerGeometry = (marker.geometry ?? {}) as RawEvent;
        const coordinate = markerGeometry.coordinates as [number, number] | undefined;
        if (!Array.isArray(coordinate) || coordinate.length < 2) return null;
        return {
          id: asText(properties.activity_id) ?? asText(properties.role) ?? `stop-${index}`,
          name: asText(properties.title) ?? "Stop",
          coordinate: [Number(coordinate[0]), Number(coordinate[1])] as [number, number],
        };
      })
      .filter((stop): stop is { id: string; name: string; coordinate: [number, number] } => stop !== null);
    const longitudes = coordinates.map((coordinate) => coordinate[0]);
    const latitudes = coordinates.map((coordinate) => coordinate[1]);
    const minLng = Math.min(...longitudes);
    const maxLng = Math.max(...longitudes);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    return {
      journey_id: journeyId,
      route: {
        type: "Feature",
        properties: { provenance: asText((feature?.properties as Record<string, unknown> | undefined)?.["provider"]) ?? "route-evidence" },
        geometry: { type: "LineString", coordinates },
      },
      stops,
      bounds: [
        [minLng, minLat],
        [maxLng, maxLat],
      ],
      center: [(minLng + maxLng) / 2, (minLat + maxLat) / 2],
      source: "LIVE",
      last_updated: new Date().toISOString(),
    };
  }

  private diagnose(
    message: string,
    source: DataSource,
    retryable: boolean,
    error?: unknown,
  ): void {
    const diagnostic: LiveDiagnostic = {
      message,
      source,
      retryable,
      detail: error instanceof Error ? error.message : error === undefined ? undefined : String(error),
    };
    this.lastDiagnostic = diagnostic;
    this.onDiagnostic?.(diagnostic);
  }

  private async requestJson<T>(path: string, init?: RequestInit): Promise<T> {
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    const timer =
      controller && this.requestTimeoutMs > 0
        ? setTimeout(() => controller.abort(), this.requestTimeoutMs)
        : null;
    try {
      const response = await this.fetchImpl(this.baseUrl + path, {
        ...init,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...(init?.headers ?? {}),
        },
        signal: controller?.signal,
      });
      const text = await response.text();
      let body: unknown = null;
      if (text) {
        try {
          body = JSON.parse(text);
        } catch {
          body = text;
        }
      }
      if (!response.ok) {
        throw new AdapterHttpError(response.status, body, `CityNexus ${response.status}: ${path}`);
      }
      return body as T;
    } finally {
      if (timer !== null) clearTimeout(timer);
    }
  }
}
