/**
 * CityNexus V18.3 Experience Adapter Contract.
 *
 * UI components depend on this interface only. Recorded fixtures live behind
 * RecordedFixtureAdapter; live CityNexus REST/SSE lives behind
 * LiveCityNexusAdapter; cached read-only truth lives behind
 * OfflineSnapshotAdapter.
 *
 * Source honesty rules:
 * - LiveCityNexusAdapter may produce source "LIVE" only from real backend data.
 * - RecordedFixtureAdapter always produces source "RECORDED_FIXTURE".
 * - OfflineSnapshotAdapter always produces source "OFFLINE".
 */

import type {
  ApprovalState,
  DataSource,
  LocalizedCopy,
  PulseState,
  RecoveryProposal,
  RuntimeIdentity,
  RuntimeStatus,
} from "../types";

export type AdapterMode = "recorded" | "live" | "offline";

export type NormalizedEventType =
  | "semantic.interpreted"
  | "mission.planned"
  | "run.started"
  | "tool.started"
  | "tool.completed"
  | "tool.failed"
  | "gateway.checked"
  | "guardian.checked"
  | "proposal.created"
  | "approval.required"
  | "run.completed"
  | "run.failed"
  | "run.stopped"
  | "unknown";

export interface NormalizedAgentEvent {
  id: string;
  run_id: string;
  sequence_no: number;
  event_type: NormalizedEventType;
  raw_event_type: string;
  tool_name: string | null;
  friendly_label: string;
  status: string;
  timestamp: string;
  duration_ms: number | null;
  result_summary: Record<string, unknown> | string | null;
  policy_decision: string | null;
  approval_id?: string;
  approval_status?: string;
  proposal_id?: string;
  mission_id?: string;
  source: DataSource;
  received_at: string;
  unknown: boolean;
}

export type NormalizedRunStatus =
  | "idle"
  | "running"
  | "success"
  | "failed"
  | "stopped"
  | "approval_required";

export interface NormalizedRun {
  run_id: string;
  journey_id: string;
  runtime_identity: RuntimeIdentity;
  provider_key: string;
  model_key: string;
  status: NormalizedRunStatus;
  source: DataSource;
  started_at?: string;
  completed_at?: string | null;
  events: NormalizedAgentEvent[];
  current_tool: string | null;
  tool_count: number;
  last_updated: string;
}

export interface RuntimeStatusInfo {
  identity: RuntimeIdentity;
  status: RuntimeStatus;
  source: DataSource;
  last_updated: string;
  detail?: string;
}

export interface CopilotMissionStart {
  mission_id: string;
  run: NormalizedRun;
  semantic_intent: string;
  answer: string;
  source: DataSource;
}

export interface StopResult {
  ok: boolean;
  run_id: string;
  status: NormalizedRunStatus;
  reason?: string;
  source: DataSource;
}

export interface NormalizedProposal {
  proposal_id: string;
  journey_id: string;
  title: LocalizedCopy;
  state: ApprovalState;
  approval_id?: string;
  expires_at?: string;
  superseded_by?: string;
  source: DataSource;
  recovery: RecoveryProposal;
  last_updated: string;
}

export interface ApprovalDecisionInput {
  proposal_id: string;
  approval_id?: string;
  decision: "approve" | "reject" | "review_requested";
  idempotency_key: string;
  online: boolean;
}

export interface ApprovalDecisionResult {
  state: ApprovalState;
  server_truth: boolean;
  proposal_id: string;
  approval_id?: string;
  reason?: "409_conflict" | "already_consumed" | "expired" | "superseded" | "network_loss" | "offline" | "failed";
  retryable: boolean;
  message: string;
  last_updated: string;
}

export interface MapState {
  journey_id: string;
  route: GeoJSON.Feature<GeoJSON.LineString>;
  stops: Array<{ id: string; name: string; coordinate: [number, number]; protected?: boolean }>;
  bounds: [[number, number], [number, number]];
  center: [number, number];
  source: DataSource;
  last_updated: string;
}

export interface RunEventHandlers {
  onEvent: (event: NormalizedAgentEvent) => void;
  onStatusChange?: (run: NormalizedRun) => void;
  onError?: (error: { message: string; retryable: boolean; source: DataSource }) => void;
  onReconnect?: (info: { attempt: number; since_sequence: number }) => void;
}

export interface RunSubscription {
  unsubscribe: () => void;
  getLastSequence: () => number;
  isLive: () => boolean;
}

export interface RecordedScenarioSummary {
  key: string;
  label: string;
  run_status: NormalizedRunStatus;
  event_count: number;
}

export interface ExperienceAdapter {
  readonly mode: AdapterMode;
  readonly source: DataSource;

  getJourneyPulse: () => Promise<PulseState>;
  /** Optional localized Today timeline for the Journey route. */
  getTodayTimeline?: () => Promise<
    Array<{
      id: string;
      time: string;
      title: LocalizedCopy;
      environment: "indoor" | "outdoor" | "transit";
      protected: boolean;
      status: "done" | "current" | "upcoming" | "candidate";
    }>
  >;
  getRuntimeStatus: () => Promise<RuntimeStatusInfo>;
  getRecoveryDiff: (proposalId?: string) => Promise<RecoveryProposal | null>;
  getMapState: () => Promise<MapState>;

  startCopilotMission: (input: { message: string; locale: "en" | "zh-CN" }) => Promise<CopilotMissionStart>;
  getRun: (runId: string) => Promise<NormalizedRun | null>;
  subscribeRunEvents: (
    runId: string,
    handlers: RunEventHandlers,
    options?: { since_sequence?: number },
  ) => RunSubscription;
  stopRun: (runId: string) => Promise<StopResult>;

  getProposal: (proposalId?: string) => Promise<NormalizedProposal | null>;
  submitApprovalDecision: (input: ApprovalDecisionInput) => Promise<ApprovalDecisionResult>;

  /** Optional recorded-only scenario discovery for the reference gallery. */
  listRecordedScenarios?: () => RecordedScenarioSummary[];
  selectRecordedScenario?: (key: string) => void;
  /** Optional offline metadata. */
  getLastUpdated?: () => string;
}
export type { ApprovalState } from "../types";
