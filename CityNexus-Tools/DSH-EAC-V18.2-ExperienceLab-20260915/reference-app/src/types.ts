/**
 * CityNexus V18.2 reference contracts.
 *
 * Human -> DeepSeek Semantic Compiler -> DIRECT or Hermes Native
 * -> CityNexus MCP -> Gateway / Guardian -> Domain truth.
 *
 * The UI must never present recorded fixtures as LIVE runtime evidence.
 */

export type RuntimeIdentity =
  | "DIRECT"
  | "HERMES_NATIVE_MCP"
  | "HERMES_COMPAT_ENDPOINT"
  | "NATIVE_DEEPSEEK_TOOL_LOOP"
  | "FALLBACK"
  | "UNAVAILABLE";

export type RuntimeStatus =
  | "ready"
  | "hermes_unavailable"
  | "deepseek_unavailable"
  | "provider_unavailable"
  | "offline_stale";

export type DataSource = "LIVE" | "RECORDED_FIXTURE" | "OFFLINE";

export type LocalizedCopy = { en: string; zh: string };

export type AgentEventType =
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
  | "run.stopped";

export interface AgentRunEvent {
  id: string;
  sequence_no: number;
  event_type: AgentEventType;
  tool_name?: string;
  timestamp: string;
  summary: string;
  source: DataSource;
  /** Tool duration when recorded by the runtime. */
  duration_ms?: number;
  /** Present for approval.required events. */
  approval_id?: string;
  /** Present for proposal.created events. */
  proposal_id?: string;
  /** Server/recorded runtime status for the run. */
  run_status?: "running" | "success" | "failed" | "stopped" | "approval_required";
}

export interface AgentRunFixture {
  fixture_label: "RECORDED_FIXTURE";
  run_id: string;
  runtime_identity: RuntimeIdentity;
  provider_key: string;
  model_key: string;
  recorded_at: string;
  scenario: string;
  events: AgentRunEvent[];
}

export type TimelineStepStatus =
  | "pending"
  | "active"
  | "done"
  | "approval"
  | "failed"
  | "stopped";

export interface TimelineStep {
  id: string;
  event_type: AgentEventType;
  label: string;
  toolName?: string;
  status: TimelineStepStatus;
  timestamp: string;
  summary: string;
  source: DataSource;
  duration_ms?: number;
}

export interface RuntimeTruth {
  semantic: "DeepSeek";
  execution: RuntimeIdentity;
  truth: "CityNexus";
  source: DataSource;
  status: RuntimeStatus;
}

export type ApprovalState =
  | "proposal_only"
  | "approval_required"
  | "approved"
  | "rejected"
  | "review_requested";

export interface JourneyActivity {
  id: string;
  title: string;
  start_at: string;
  end_at: string;
  place: string;
  category: string;
  environment: "indoor" | "outdoor" | "transit";
  walking_min: number;
  protected: boolean;
  status: "done" | "current" | "upcoming" | "candidate";
}

export interface PulseState {
  now: {
    activity: JourneyActivity;
    time: string;
    eta: string;
    note: string;
  };
  next: {
    activity: JourneyActivity;
    time: string;
    buffer_min: number;
    note: string;
  };
  risk: {
    level: "low" | "watch" | "high";
    title: string;
    detail: string;
    source: DataSource;
  };
  primaryAction: {
    label: string;
    route: string;
    reason: string;
  };
}

export interface RecoveryProposal {
  proposal_id: string;
  trigger: LocalizedCopy;
  severity: "minor" | "major";
  source: DataSource;
  before: JourneyActivity[];
  after: JourneyActivity[];
  removed: LocalizedCopy;
  added: LocalizedCopy;
  why: LocalizedCopy[];
  protected_commitments: LocalizedCopy[];
  time_delta_min: number;
  cost_delta_minor: number;
  travel_delta_min: number;
  walking_delta_min: number;
  protected_commitments_preserved: boolean;
  evidence_state: "verified" | "unresolved" | "stale";
  verified_evidence: {
    route_provenance: string;
    source_provider: string;
    snapshot_id: string;
  };
  explanation: LocalizedCopy;
}

export interface MapCameraCommand {
  center?: [number, number];
  zoom?: number;
  bounds?: [[number, number], [number, number]];
  duration_token: "instant" | "fast" | "base" | "slow" | "map";
  animate: boolean;
}

export interface CopilotMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  intent?: string;
  runtime?: RuntimeTruth;
  fixture?: AgentRunFixture;
  whatIf?: {
    simulation_only: true;
    status: string;
    changed_activity: string;
    unchanged_commitments: number;
  };
}
