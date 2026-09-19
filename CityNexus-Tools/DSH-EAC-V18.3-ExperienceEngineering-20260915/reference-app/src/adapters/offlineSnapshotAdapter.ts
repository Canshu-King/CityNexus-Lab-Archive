/**
 * OfflineSnapshotAdapter — read-only cached view of the same reference
 * fixtures. It always reports `source: "OFFLINE"`.
 *
 * This adapter never starts a run, never creates events and never claims
 * server truth. `submitApprovalDecision` always fails safely with
 * `reason: "offline"` and `retryable: true`, so destructive approval actions
 * stay disabled in the UI until authoritative connectivity returns.
 */

import type {
  AgentRunFixture,
  DataSource,
  PulseState,
  RecoveryProposal,
} from "../types";
import { HERMES_FIXTURES } from "./fixtures/hermesFixtures";
import { JOURNEY, PULSE, RECOVERY, TODAY_TIMELINE } from "./fixtures/journeyFixtures";
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
  RunEventHandlers,
  RunSubscription,
  RuntimeStatusInfo,
  StopResult,
} from "./contract";
import { buildNormalizedRun } from "./eventStore";
import { buildFixtureMapState, normalizedFixtureEvents } from "./recordedFixtureAdapter";

export interface OfflineRunSubscription extends RunSubscription {
  stop: () => void;
  whenComplete: () => Promise<void>;
}

function cachedRun(fixture: AgentRunFixture, source: DataSource): NormalizedRun {
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

export class OfflineSnapshotAdapter implements ExperienceAdapter {
  readonly mode: AdapterMode = "offline";
  readonly source: DataSource = "OFFLINE";

  private readonly lastUpdatedIso: string;

  constructor(lastUpdated: string = HERMES_FIXTURES.completed.recorded_at) {
    this.lastUpdatedIso = lastUpdated;
  }

  /** ISO timestamp describing when the cached snapshot was captured. */
  getLastUpdated(): string {
    return this.lastUpdatedIso;
  }

  async getJourneyPulse(): Promise<PulseState> {
    return { ...PULSE, risk: { ...PULSE.risk, source: this.source } };
  }

  async getRuntimeStatus(): Promise<RuntimeStatusInfo> {
    return {
      identity: "UNAVAILABLE",
      status: "offline_stale",
      source: this.source,
      last_updated: this.lastUpdatedIso,
      detail: "Offline cached snapshot. Destructive actions are disabled until authoritative truth returns.",
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
    return buildFixtureMapState(this.source, this.lastUpdatedIso);
  }

  async getTodayTimeline() {
    return TODAY_TIMELINE.map((item) => ({ ...item, title: { ...item.title } }));
  }

  async startCopilotMission(input: { message: string; locale: "en" | "zh-CN" }): Promise<CopilotMissionStart> {
    // Read-only: no new run is started; the cached run is returned for context.
    const run = cachedRun(HERMES_FIXTURES.completed, this.source);
    return {
      mission_id: "mission-offline-cache",
      run,
      semantic_intent: "OFFLINE",
      answer:
        "Offline snapshot: CityNexus cannot start or advance a live run until connectivity returns. " +
        `Requested: ${input.message}`,
      source: this.source,
    };
  }

  async getRun(runId: string): Promise<NormalizedRun | null> {
    const fixture = Object.values(HERMES_FIXTURES).find((candidate) => candidate.run_id === runId);
    return fixture ? cachedRun(fixture, this.source) : null;
  }

  subscribeRunEvents(
    runId: string,
    handlers: RunEventHandlers,
    options?: { since_sequence?: number },
  ): OfflineRunSubscription {
    const fixture =
      Object.values(HERMES_FIXTURES).find((candidate) => candidate.run_id === runId) ??
      HERMES_FIXTURES.completed;
    const since = options?.since_sequence ?? 0;
    const stored: NormalizedAgentEvent[] = normalizedFixtureEvents(fixture, this.source);
    const replay = stored.filter((event) => event.sequence_no > since);
    let lastSequence = since;

    // Cached events are emitted once, synchronously. No timers, no invention.
    for (const event of replay) {
      lastSequence = Math.max(lastSequence, event.sequence_no);
      handlers.onEvent(event);
    }
    if (replay.length > 0) {
      handlers.onStatusChange?.(cachedRun(fixture, this.source));
    }

    return {
      unsubscribe: () => undefined,
      stop: () => undefined,
      getLastSequence: () => lastSequence,
      isLive: () => false,
      whenComplete: () => Promise.resolve(),
    };
  }

  async stopRun(runId: string): Promise<StopResult> {
    const fixture = Object.values(HERMES_FIXTURES).find((candidate) => candidate.run_id === runId);
    const status = fixture ? cachedRun(fixture, this.source).status : "stopped";
    return {
      ok: false,
      run_id: runId,
      status,
      reason: "offline",
      source: this.source,
    };
  }

  async getProposal(proposalId?: string): Promise<NormalizedProposal | null> {
    const id = proposalId ?? RECOVERY.proposal_id;
    return {
      proposal_id: id,
      journey_id: JOURNEY.id,
      title: { ...RECOVERY.trigger },
      state: "proposal_only",
      source: this.source,
      recovery: { ...RECOVERY, proposal_id: id, source: this.source },
      last_updated: this.lastUpdatedIso,
    };
  }

  async submitApprovalDecision(input: ApprovalDecisionInput): Promise<ApprovalDecisionResult> {
    return {
      state: "approval_required",
      server_truth: false,
      proposal_id: input.proposal_id,
      approval_id: input.approval_id,
      reason: "offline",
      retryable: true,
      message: "Offline: destructive approval is disabled. Reconnect to refresh authoritative truth.",
      last_updated: this.lastUpdatedIso,
    };
  }
}
