/**
 * Runtime truth / experience contracts for the isolated V18 reference app.
 *
 * The names intentionally mirror the CityNexus V18 frontend contract:
 * semantic understanding belongs to DeepSeek, execution truth belongs to the
 * server runtime, and all facts remain CityNexus-owned.
 */

export type RuntimeIdentity =
  | "DIRECT"
  | "HERMES_NATIVE_MCP"
  | "NATIVE_DEEPSEEK_TOOL_LOOP"
  | "HERMES_COMPAT_ENDPOINT"
  | "NOT_CONFIGURED";

export type DataSource = "LIVE" | "RECORDED_FIXTURE" | "OFFLINE";

export type AgentEventType =
  | "run.started"
  | "tool.started"
  | "tool.completed"
  | "tool.failed"
  | "approval.required"
  | "run.completed"
  | "run.stopped";

export interface AgentRunEvent {
  id: string;
  sequence_no: number;
  event_type: AgentEventType;
  tool_name?: string;
  timestamp: string;
  summary: string;
  source: DataSource;
  /** Present for approval.required events. */
  approval_id?: string;
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
}

export interface RuntimeTruth {
  semantic: "DeepSeek";
  execution: RuntimeIdentity;
  truth: "CityNexus";
  source: DataSource;
}

export interface JourneyActivity {
  id: string;
  title: string;
  start_at: string;
  end_at: string;
  place: string;
  category: string;
  protected: boolean;
  status: "done" | "current" | "upcoming" | "candidate";
}

export interface PulseState {
  now: {
    activity: JourneyActivity;
    time: string;
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
  trigger: string;
  severity: "minor" | "major";
  source: DataSource;
  before: JourneyActivity[];
  after: JourneyActivity[];
  removed: string[];
  added: string[];
  cost_delta_minor: number;
  travel_delta_min: number;
  protected_commitments_preserved: boolean;
  verified_evidence: {
    route_provenance: string;
    source_provider: string;
    snapshot_id: string;
  };
  explanation: string;
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
