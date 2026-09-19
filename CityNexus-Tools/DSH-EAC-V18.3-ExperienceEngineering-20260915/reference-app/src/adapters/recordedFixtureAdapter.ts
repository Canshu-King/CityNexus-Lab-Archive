/**
 * RecordedFixtureAdapter — deterministic replay of the checked-in reference
 * fixtures. It always reports `source: "RECORDED_FIXTURE"` and never claims
 * server truth.
 *
 * Recorded scenario keys: `completed` (14 events, approval_required),
 * `approved` (15 events, success), `failed` (6 events), `stopped` (5 events).
 *
 * Approval simulation (documented):
 * - `selectRecordedScenario(key)` accepts either one of the four scenario keys
 *   or an approval-outcome override: `approval:expired`,
 *   `approval:superseded`, `approval:already_consumed`, `approval:offline`,
 *   `approval:rejected`, `approval:review_requested`.
 * - `submitApprovalDecision` also honors proposal-id prefixes containing
 *   `expired`, `superseded`, `already-consumed`/`consumed`, `offline`,
 *   `reject`, or `review`.
 * - Repeated calls with the same `idempotency_key` return the identical
 *   settled result (double-click safety).
 *
 * Replay progress is driven exclusively by `requestAnimationFrame`; this file
 * intentionally contains no timer-based event generation.
 */

import type {
  AgentRunEvent,
  AgentRunFixture,
  ApprovalState,
  DataSource,
  PulseState,
  RecoveryProposal,
} from "../types";
import { HERMES_FIXTURES } from "./fixtures/hermesFixtures";
import { ACTIVITIES, JOURNEY, PULSE, RECOVERY, TODAY_TIMELINE } from "./fixtures/journeyFixtures";
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
  RecordedScenarioSummary,
  RunEventHandlers,
  RunSubscription,
  RuntimeStatusInfo,
  StopResult,
} from "./contract";
import type { RawAgentEvent } from "./normalize";
import { EventStore, buildNormalizedRun } from "./eventStore";

type RawEvent = RawAgentEvent;

export const RECORDED_SCENARIO_KEYS = ["completed", "approved", "failed", "stopped"] as const;
export type RecordedScenarioKey = (typeof RECORDED_SCENARIO_KEYS)[number];

export interface RecordedRunSubscription extends RunSubscription {
  stop: () => void;
  whenComplete: () => Promise<void>;
}

function isRecordedScenarioKey(value: string): value is RecordedScenarioKey {
  return (RECORDED_SCENARIO_KEYS as readonly string[]).includes(value);
}

function eventToRaw(event: AgentRunEvent, runId: string): RawEvent {
  return {
    id: event.id,
    run_id: runId,
    sequence_no: event.sequence_no,
    event_type: event.event_type,
    tool_name: event.tool_name,
    timestamp: event.timestamp,
    duration_ms: event.duration_ms,
    approval_id: event.approval_id,
    proposal_id: event.proposal_id,
    summary: event.summary,
    result: event.run_status ? { status: event.run_status } : undefined,
    source: "HERMES_NATIVE",
  };
}

/** Normalize a fixture into the runtime event contract under the given source. */
export function normalizedFixtureEvents(
  fixture: AgentRunFixture,
  source: DataSource,
): NormalizedAgentEvent[] {
  const store = new EventStore({ source });
  store.append(fixture.events.map((event) => eventToRaw(event, fixture.run_id)), {
    source,
    runId: fixture.run_id,
  });
  return store.snapshot();
}

function runFromFixture(key: RecordedScenarioKey, source: DataSource): NormalizedRun {
  const fixture = HERMES_FIXTURES[key];
  const events = normalizedFixtureEvents(fixture, source);
  return buildNormalizedRun({
    runId: fixture.run_id,
    journeyId: JOURNEY.id,
    runtimeIdentity: fixture.runtime_identity,
    providerKey: fixture.provider_key,
    modelKey: fixture.model_key,
    events,
    source,
    lastUpdated: fixture.recorded_at,
  });
}

const FIXTURE_STOP_COORDS: Record<string, [number, number]> = {
  "act-morning-walk": [117.2005, 39.1168],
  "act-river-cruise": [117.2108, 39.1264],
  "act-market-window": [117.2163, 39.1322],
  "act-museum": [117.2224, 39.1375],
  "act-hotel": [117.228, 39.1402],
  "act-departure": [117.2295, 39.1418],
};

/** Build the fixture map projection from `journeyFixtures` activities. */
export function buildFixtureMapState(source: DataSource, lastUpdated: string): MapState {
  const located = ACTIVITIES.filter((activity) => FIXTURE_STOP_COORDS[activity.id] !== undefined);
  const coordinates = located.map((activity) => FIXTURE_STOP_COORDS[activity.id]);
  const longitudes = coordinates.map((coordinate) => coordinate[0]);
  const latitudes = coordinates.map((coordinate) => coordinate[1]);
  const minLng = Math.min(...longitudes);
  const maxLng = Math.max(...longitudes);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  return {
    journey_id: JOURNEY.id,
    route: {
      type: "Feature",
      properties: { provenance: "recorded-fixture://route-rain-003" },
      geometry: { type: "LineString", coordinates },
    },
    stops: located.map((activity) => ({
      id: activity.id,
      name: activity.title.en,
      coordinate: FIXTURE_STOP_COORDS[activity.id],
      protected: activity.protected,
    })),
    bounds: [
      [minLng, minLat],
      [maxLng, maxLat],
    ],
    center: [(minLng + maxLng) / 2, (minLat + maxLat) / 2],
    source,
    last_updated: lastUpdated,
  };
}

type ApprovalOutcome =
  | "approved"
  | "expired"
  | "superseded"
  | "already_consumed"
  | "offline"
  | "rejected"
  | "review_requested";

function outcomeFromProposalId(proposalId: string): ApprovalOutcome | null {
  const value = proposalId.toLowerCase();
  if (value.includes("expired")) return "expired";
  if (value.includes("superseded")) return "superseded";
  if (value.includes("already-consumed") || value.includes("already_consumed")) return "already_consumed";
  if (value.includes("consumed")) return "already_consumed";
  if (value.includes("offline")) return "offline";
  if (value.includes("reject")) return "rejected";
  if (value.includes("review")) return "review_requested";
  return null;
}

/** Schedule one replay step. Uses rAF in browsers, microtasks in Node. */
function scheduleFrame(callback: () => void): () => void {
  if (typeof requestAnimationFrame === "function") {
    const handle = requestAnimationFrame(() => callback());
    return () => cancelAnimationFrame(handle);
  }
  let cancelled = false;
  queueMicrotask(() => {
    if (!cancelled) callback();
  });
  return () => {
    cancelled = true;
  };
}

export class RecordedFixtureAdapter implements ExperienceAdapter {
  readonly mode: AdapterMode = "recorded";
  readonly source: DataSource = "RECORDED_FIXTURE";

  private scenarioKey: RecordedScenarioKey = "completed";
  private approvalOutcomeOverride: ApprovalOutcome | null = null;
  private readonly idempotencyResults = new Map<string, ApprovalDecisionResult>();
  private readonly proposalResults = new Map<string, ApprovalDecisionResult>();

  /** Select a recorded scenario or an approval-outcome override (see header). */
  selectRecordedScenario(key: string): void {
    if (isRecordedScenarioKey(key)) {
      this.scenarioKey = key;
      this.approvalOutcomeOverride = null;
      return;
    }
    this.approvalOutcomeOverride = key.startsWith("approval:")
      ? (key.slice("approval:".length) as ApprovalOutcome)
      : (key as ApprovalOutcome);
  }

  listRecordedScenarios(): RecordedScenarioSummary[] {
    return RECORDED_SCENARIO_KEYS.map((key) => {
      const fixture = HERMES_FIXTURES[key];
      return {
        key,
        label: fixture.scenario,
        run_status: runFromFixture(key, this.source).status,
        event_count: fixture.events.length,
      };
    });
  }

  async getJourneyPulse(): Promise<PulseState> {
    return { ...PULSE, risk: { ...PULSE.risk, source: this.source } };
  }

  async getRuntimeStatus(): Promise<RuntimeStatusInfo> {
    return {
      identity: HERMES_FIXTURES[this.scenarioKey].runtime_identity,
      status: "ready",
      source: this.source,
      last_updated: this.lastUpdated(),
      detail: "Recorded fixture replay. No live Hermes run is executing.",
    };
  }

  async getRecoveryDiff(proposalId?: string): Promise<RecoveryProposal | null> {
    return {
      ...RECOVERY,
      proposal_id: proposalId ?? RECOVERY.proposal_id,
      source: this.source,
    };
  }

  async getMapState(): Promise<MapState> {
    return buildFixtureMapState(this.source, this.lastUpdated());
  }

  async getTodayTimeline() {
    return TODAY_TIMELINE.map((item) => ({ ...item, title: { ...item.title } }));
  }

  async startCopilotMission(input: { message: string; locale: "en" | "zh-CN" }): Promise<CopilotMissionStart> {
    const wantsReplan = /replan|alternative|rain|swap|change|雨|替代|换/i.test(input.message);
    const key = this.scenarioKey;
    const run = runFromFixture(key, this.source);
    return {
      mission_id: `mission-fixture-${key}`,
      run,
      semantic_intent: wantsReplan ? "REQUEST_REPLAN" : "WHAT_IF",
      answer: wantsReplan
        ? "Recorded Hermes-style run selected. The timeline below replays recorded events only."
        : "Preview only. The protected 09:30 cruise is unchanged and no mutation occurs.",
      source: this.source,
    };
  }

  async getRun(runId: string): Promise<NormalizedRun | null> {
    const key = RECORDED_SCENARIO_KEYS.find((candidate) => HERMES_FIXTURES[candidate].run_id === runId);
    return key ? runFromFixture(key, this.source) : null;
  }

  subscribeRunEvents(
    runId: string,
    handlers: RunEventHandlers,
    options?: { since_sequence?: number },
  ): RecordedRunSubscription {
    const key =
      RECORDED_SCENARIO_KEYS.find((candidate) => HERMES_FIXTURES[candidate].run_id === runId) ??
      this.scenarioKey;
    const fixture = HERMES_FIXTURES[key];
    const allEvents = normalizedFixtureEvents(fixture, this.source);
    const lastEventReceivedAt = fixture.recorded_at;
    const since = options?.since_sequence ?? 0;
    const replay = allEvents.filter((event) => event.sequence_no > since);

    let lastSequence = since;
    let index = 0;
    let cancelled = false;
    let cancelFrame: (() => void) | null = null;
    let resolveComplete: () => void = () => undefined;
    const completion = new Promise<void>((resolve) => {
      resolveComplete = resolve;
    });

    const statusAt = (sequence: number): NormalizedRun =>
      buildNormalizedRun({
        runId: fixture.run_id,
        journeyId: JOURNEY.id,
        runtimeIdentity: fixture.runtime_identity,
        providerKey: fixture.provider_key,
        modelKey: fixture.model_key,
        events: allEvents.filter((event) => event.sequence_no <= sequence),
        source: this.source,
        lastUpdated: lastEventReceivedAt,
      });

    handlers.onStatusChange?.(statusAt(since));

    const step = () => {
      if (cancelled) return;
      if (index >= replay.length) {
        resolveComplete();
        return;
      }
      const event = replay[index];
      index += 1;
      lastSequence = Math.max(lastSequence, event.sequence_no);
      handlers.onEvent(event);
      handlers.onStatusChange?.(statusAt(lastSequence));
      cancelFrame = scheduleFrame(step);
    };
    cancelFrame = scheduleFrame(step);

    const stop = () => {
      if (cancelled) return;
      cancelled = true;
      cancelFrame?.();
      cancelFrame = null;
      resolveComplete();
    };

    return {
      unsubscribe: stop,
      stop,
      getLastSequence: () => lastSequence,
      isLive: () => false,
      whenComplete: () => completion,
    };
  }

  async stopRun(runId: string): Promise<StopResult> {
    return {
      ok: true,
      run_id: runId,
      status: "stopped",
      reason: "recorded replay stopped locally; no server event fabricated",
      source: this.source,
    };
  }

  async getProposal(proposalId?: string): Promise<NormalizedProposal | null> {
    const id = proposalId ?? "proposal-fixture-002";
    const settled = this.proposalResults.get(id);
    let state: ApprovalState;
    if (settled) state = settled.state;
    else if (this.scenarioKey === "approved") state = "approved";
    else if (this.scenarioKey === "completed") state = "approval_required";
    else state = "proposal_only";
    const approvalId =
      id === "proposal-fixture-002" ? "approval-fixture-002" : settled?.approval_id;
    return {
      proposal_id: id,
      journey_id: JOURNEY.id,
      title: { ...RECOVERY.trigger },
      state,
      approval_id: approvalId,
      source: this.source,
      recovery: { ...RECOVERY, proposal_id: id, source: this.source },
      last_updated: this.lastUpdated(),
    };
  }

  async submitApprovalDecision(input: ApprovalDecisionInput): Promise<ApprovalDecisionResult> {
    const cached = this.idempotencyResults.get(input.idempotency_key);
    if (cached) return { ...cached };
    const lastUpdated = new Date().toISOString();

    if (!input.online) {
      return this.settle(
        input,
        "approval_required",
        "offline",
        true,
        "Offline: recorded approval is disabled until connectivity returns.",
        lastUpdated,
      );
    }
    if (input.decision === "reject") {
      return this.settle(input, "rejected", undefined, false, "Recorded rejection settled. Current plan kept.", lastUpdated);
    }
    if (input.decision === "review_requested") {
      return this.settle(
        input,
        "review_requested",
        undefined,
        true,
        "Review requested. The recorded proposal returns to review.",
        lastUpdated,
      );
    }

    const outcome = this.approvalOutcomeOverride ?? outcomeFromProposalId(input.proposal_id);
    switch (outcome) {
      case "expired":
        return this.settle(input, "approval_required", "expired", false, "Recorded approval expired. Refresh for a new proposal.", lastUpdated);
      case "superseded":
        return this.settle(input, "approval_required", "superseded", false, "Recorded proposal was superseded by newer truth.", lastUpdated);
      case "already_consumed":
        return this.settle(input, "approved", "already_consumed", false, "Recorded approval was already consumed; no new transition occurred.", lastUpdated);
      case "offline":
        return this.settle(input, "approval_required", "offline", true, "Offline: recorded approval is disabled until connectivity returns.", lastUpdated);
      case "rejected":
        return this.settle(input, "rejected", undefined, false, "Recorded rejection settled. Current plan kept.", lastUpdated);
      case "review_requested":
        return this.settle(input, "review_requested", undefined, true, "Review requested. The recorded proposal returns to review.", lastUpdated);
      default:
        return this.settle(
          input,
          "approved",
          undefined,
          false,
          "Recorded approval accepted in reference mode. No backend mutation and no server truth claim.",
          lastUpdated,
        );
    }
  }

  getLastUpdated(): string {
    return this.lastUpdated();
  }

  private lastUpdated(): string {
    return HERMES_FIXTURES[this.scenarioKey].recorded_at;
  }

  private settle(
    input: ApprovalDecisionInput,
    state: ApprovalState,
    reason: ApprovalDecisionResult["reason"],
    retryable: boolean,
    message: string,
    lastUpdated: string,
  ): ApprovalDecisionResult {
    const result: ApprovalDecisionResult = {
      state,
      server_truth: false,
      proposal_id: input.proposal_id,
      approval_id: input.approval_id,
      reason,
      retryable,
      message,
      last_updated: lastUpdated,
    };
    this.idempotencyResults.set(input.idempotency_key, result);
    this.proposalResults.set(input.proposal_id, result);
    return { ...result };
  }
}
