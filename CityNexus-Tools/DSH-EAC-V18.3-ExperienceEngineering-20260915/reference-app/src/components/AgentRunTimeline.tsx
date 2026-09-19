import { useEffect, useMemo, useState } from "react";
import { LiveRegion } from "../features/accessibility/LiveRegion";
import { useThrottledAnnouncer } from "../features/accessibility/useThrottledAnnouncer";
import { useT } from "../i18n";
import { testIds } from "../testids";
import type { ApprovalState, DataSource } from "../types";
import type { NormalizedAgentEvent, NormalizedRunStatus } from "../adapters/contract";
import { RuntimeTruthBadge } from "./RuntimeTruthBadge";

export interface TimelineStepView {
  id: string;
  label: string;
  toolName: string | null;
  status: "pending" | "active" | "done" | "approval" | "failed" | "stopped";
  timestamp: string;
  summary: string;
  durationMs: number | null;
  unknown: boolean;
  rawEventType: string;
}

const TOOL_LABELS: Record<string, { started: string; done: string }> = {
  inspect_journey: { started: "Checking Journey", done: "Checked Journey" },
  inspect_twin: { started: "Checking protected commitments", done: "Checked protected commitments" },
  search_city_services: { started: "Searching alternatives", done: "Searched alternatives" },
  request_replan: { started: "Requesting replan", done: "Requested replan" },
};

function statusFor(event: NormalizedAgentEvent): TimelineStepView["status"] {
  switch (event.event_type) {
    case "tool.started":
      return "active";
    case "tool.failed":
    case "run.failed":
      return "failed";
    case "approval.required":
      return "approval";
    case "run.stopped":
      return "stopped";
    default:
      return "done";
  }
}

function labelFor(event: NormalizedAgentEvent): string {
  if (event.unknown) return `Unknown event · ${event.raw_event_type}`;
  const tool = event.tool_name ?? "tool";
  switch (event.event_type) {
    case "semantic.interpreted":
      return "Understood request";
    case "mission.planned":
      return "Mission planned";
    case "run.started":
      return "Run started";
    case "tool.started":
      return TOOL_LABELS[event.tool_name ?? ""]?.started ?? `Started · ${tool}`;
    case "tool.completed":
      return TOOL_LABELS[event.tool_name ?? ""]?.done ?? `Completed · ${tool}`;
    case "tool.failed":
      return `Failed · ${tool}`;
    case "gateway.checked":
      return "Gateway checked";
    case "guardian.checked":
      return "Guardian checked";
    case "proposal.created":
      return "Proposal created";
    case "approval.required":
      return "Waiting for approval";
    case "run.completed":
      return "Run completed";
    case "run.failed":
      return "Run failed";
    case "run.stopped":
      return "Run stopped";
    default:
      return tool;
  }
}

function summaryText(event: NormalizedAgentEvent): string {
  if (typeof event.result_summary === "string") return event.result_summary;
  if (event.result_summary && typeof event.result_summary === "object") {
    const summary = event.result_summary;
    if (typeof summary.summary === "string") return summary.summary;
    if (typeof summary.decision === "string") return `decision: ${summary.decision}`;
    if (typeof summary.status === "string") return `status: ${summary.status}`;
    if (Array.isArray(summary.keys)) return `result keys: ${summary.keys.join(", ")}`;
  }
  return event.friendly_label || event.raw_event_type;
}

export function deriveTimelineSteps(events: NormalizedAgentEvent[]): TimelineStepView[] {
  return events.map((event) => ({
    id: event.id,
    label: labelFor(event),
    toolName: event.tool_name,
    status: statusFor(event),
    timestamp: event.timestamp,
    summary: summaryText(event),
    durationMs: event.duration_ms,
    unknown: event.unknown,
    rawEventType: event.raw_event_type,
  }));
}

const WINDOW_SIZE = 50;

export function AgentRunTimeline({
  events,
  runStatus,
  source,
  connection,
  approvalState = "proposal_only",
  submitting = false,
  offline = false,
  onApproval,
  onStop,
  compact = false,
}: {
  events: NormalizedAgentEvent[];
  runStatus: NormalizedRunStatus;
  source: DataSource;
  connection?: "idle" | "connecting" | "live" | "recorded" | "offline" | "error";
  approvalState?: ApprovalState;
  submitting?: boolean;
  offline?: boolean;
  onApproval?: (decision: "approve" | "reject" | "review_requested") => void;
  onStop?: () => void;
  compact?: boolean;
}) {
  const t = useT();
  const [expanded, setExpanded] = useState(!compact);
  const [showAll, setShowAll] = useState(false);

  const { announce, message: liveMessage } = useThrottledAnnouncer();

  useEffect(() => {
    // Only important lifecycle transitions are announced to screen readers.
    if (["success", "failed", "stopped", "approval_required"].includes(runStatus)) {
      announce(`Agent run ${runStatus.replace("_", " ")}`, "completed");
    }
  }, [announce, runStatus]);

  const steps = useMemo(() => deriveTimelineSteps(events), [events]);
  const visibleSteps = useMemo(
    () => (showAll ? steps : steps.slice(Math.max(0, steps.length - WINDOW_SIZE))),
    [steps, showAll],
  );
  const approvalVisible = steps.some((step) => step.status === "approval");
  const currentStep = steps[steps.length - 1];
  const statusLabel = t(`timeline.run.${runStatus}`);

  return (
    <section
      className={`timeline timeline--${runStatus}`}
      data-testid={testIds.agentRunTimeline}
      data-source={source}
      data-run-status={runStatus}
      data-event-count={steps.length}
    >
      <LiveRegion message={liveMessage} />
      <header className="timeline__head">
        <div>
          <span className="kicker">{t("timeline.kicker")}</span>
          <h3>{t("timeline.title")}</h3>
        </div>
        <RuntimeTruthBadge
          truth={{ semantic: "DeepSeek", execution: "HERMES_NATIVE_MCP", truth: "CityNexus", source, status: offline ? "offline_stale" : "ready" }}
          compact
        />
      </header>
      {source === "RECORDED_FIXTURE" && (
        <p className="fixture-banner" data-testid={testIds.timelineSource}>
          <b>{t("timeline.recorded")}</b> · {t("timeline.recordedNote")}
        </p>
      )}
      {source === "OFFLINE" && (
        <p className="fixture-banner stopped" role="status">
          OFFLINE snapshot · reconnect to refresh authoritative truth.
        </p>
      )}
      <div className="timeline__summary" data-testid="timeline-summary" data-status={runStatus}>
        <b>{statusLabel}</b>
        {currentStep && currentStep.label !== statusLabel && (
          <span>
            {currentStep.label}
            {currentStep.toolName ? ` · ${currentStep.toolName}` : ""}
            {currentStep.durationMs ? ` · ${currentStep.durationMs}ms` : ""}
          </span>
        )}
        {connection && <small>connection: {connection}</small>}
      </div>
      {compact && !expanded ? (
        <button type="button" className="btn" data-testid="timeline-expand" onClick={() => setExpanded(true)}>
          {t("timeline.expand")}
        </button>
      ) : (
        <>
          {steps.length === 0 ? (
            <p className="muted">{t("timeline.empty")}</p>
          ) : (
            <ol className="timeline__steps">
              {!showAll && steps.length > WINDOW_SIZE && (
                <li className="timeline-window-note" data-testid="timeline-window-note">
                  Showing latest {WINDOW_SIZE} of {steps.length} events.{" "}
                  <button type="button" className="chip-btn" data-testid="timeline-show-all" onClick={() => setShowAll(true)}>
                    Show all
                  </button>
                </li>
              )}
              {visibleSteps.map((step) => (
                <li
                  key={step.id}
                  className={`timeline-step ${step.status}${step.unknown ? " unknown" : ""}`}
                  data-testid={testIds.timelineStep}
                  data-status={step.status}
                  data-tool={step.toolName ?? ""}
                  data-unknown={step.unknown ? "true" : "false"}
                >
                  <span className="timeline-step__mark" aria-hidden="true" />
                  <div className="timeline-step__body">
                    <b>{step.label}</b>
                    {step.toolName && (
                      <code className="timeline-step__tool" title={step.toolName}>
                        {step.toolName}
                        {step.durationMs ? ` · ${step.durationMs}ms` : ""}
                      </code>
                    )}
                    <small>{step.summary}</small>
                    <time dateTime={step.timestamp}>{step.timestamp.slice(11, 23)}</time>
                  </div>
                  <span className="timeline-step__status">{t(`timeline.status.${step.unknown ? "pending" : step.status}`)}</span>
                </li>
              ))}
            </ol>
          )}
          {compact && (
            <button type="button" className="btn" data-testid="timeline-collapse" onClick={() => setExpanded(false)}>
              {t("timeline.collapse")}
            </button>
          )}
        </>
      )}
      {approvalVisible && (
        <div
          className="approval-panel"
          data-testid="approval-panel"
          data-approval-state={approvalState}
          role="group"
          aria-label={t("approval.title")}
        >
          <div>
            <b>{t("approval.title")}</b>
            <p>{t("approval.impact")}</p>
            {offline && <p className="muted small">OFFLINE: approval disabled until authoritative truth returns.</p>}
          </div>
          <div className="approval-actions">
            <button
              type="button"
              className="btn btn--approve"
              data-testid="approval-approve"
              disabled={submitting || offline}
              onClick={() => onApproval?.("approve")}
            >
              {submitting ? "Submitting…" : t("approval.approve")}
            </button>
            <button
              type="button"
              className="btn btn--reject"
              data-testid="approval-reject"
              disabled={submitting || offline}
              onClick={() => onApproval?.("reject")}
            >
              {t("approval.reject")}
            </button>
            <button
              type="button"
              className="btn"
              data-testid="approval-review"
              disabled={submitting || offline}
              onClick={() => onApproval?.("review_requested")}
            >
              {t("approval.review")}
            </button>
          </div>
          <p className="muted small" data-testid="approval-state-copy">
            {t(`approval.state.${approvalState}`)} · {t("approval.authority")}
          </p>
        </div>
      )}
      <div className="timeline__controls">
        {source !== "LIVE" && onStop && (
          <button type="button" className="btn" data-testid={testIds.timelineStop} onClick={onStop} disabled={offline}>
            {t("timeline.stop")}
          </button>
        )}
        <span className="muted small" data-testid="timeline-count">
          {t("timeline.eventCount", { visible: visibleSteps.length, total: steps.length })}
        </span>
      </div>
    </section>
  );
}
