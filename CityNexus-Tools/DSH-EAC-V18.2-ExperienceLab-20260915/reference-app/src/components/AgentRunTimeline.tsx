import { useEffect, useMemo, useRef, useState } from "react";
import { useT } from "../i18n";
import { prefersReducedMotion } from "../motion";
import { testIds } from "../testids";
import type {
  AgentRunEvent,
  AgentRunFixture,
  ApprovalState,
  DataSource,
  RuntimeIdentity,
  TimelineStep,
  TimelineStepStatus,
} from "../types";
import { RuntimeTruthBadge } from "./RuntimeTruthBadge";

const HUMAN_TOOL: Record<string, string> = {
  inspect_journey: "journey",
  inspect_twin: "protected commitments",
  search_city_services: "alternatives",
  request_replan: "replan",
};

const TOOL_LABELS: Record<string, { started: string; done: string }> = {
  inspect_journey: { started: "Checking Journey", done: "Checked Journey" },
  inspect_twin: { started: "Checking protected commitments", done: "Checked protected commitments" },
  search_city_services: { started: "Searching alternatives", done: "Searched alternatives" },
  request_replan: { started: "Requesting replan", done: "Requested replan" },
};

function humanTool(toolName?: string): string {
  if (!toolName) return "tool";
  return HUMAN_TOOL[toolName] ?? toolName;
}

export function statusForEvent(event: AgentRunEvent): TimelineStepStatus {
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

export function labelForEvent(event: AgentRunEvent): string {
  const tool = humanTool(event.tool_name);
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

export function deriveTimelineSteps(events: AgentRunEvent[]): TimelineStep[] {
  return events.map((event) => ({
    id: event.id,
    event_type: event.event_type,
    label: labelForEvent(event),
    toolName: event.tool_name,
    status: statusForEvent(event),
    timestamp: event.timestamp,
    summary: event.summary,
    source: event.source,
    duration_ms: event.duration_ms,
  }));
}

function runStatusFor(events: AgentRunEvent[], stoppedLocally: boolean): string {
  if (stoppedLocally) return "stopped";
  const last = events[events.length - 1];
  if (!last) return "idle";
  if (last.event_type === "run.failed" || last.event_type === "tool.failed") return "failed";
  if (last.event_type === "run.stopped") return "stopped";
  if (last.event_type === "approval.required" || last.run_status === "approval_required") return "approval_required";
  if (last.event_type === "run.completed" || last.run_status === "success") return "success";
  return "running";
}

export function AgentRunTimeline({
  fixture,
  liveEventsUrl,
  liveEvents,
  onStop,
  onApproval,
  compact = false,
}: {
  fixture?: AgentRunFixture;
  liveEventsUrl?: string;
  liveEvents?: AgentRunEvent[];
  onStop?: () => void;
  onApproval?: (state: ApprovalState) => void;
  compact?: boolean;
}) {
  const t = useT();
  const isLive = Boolean(liveEventsUrl || (liveEvents && liveEvents.length > 0));
  const sourceEvents = useMemo<AgentRunEvent[]>(
    () => liveEvents ?? fixture?.events ?? [],
    [liveEvents, fixture],
  );
  const [visibleCount, setVisibleCount] = useState(isLive ? sourceEvents.length : 0);
  const [replaying, setReplaying] = useState(false);
  const [replayStopped, setReplayStopped] = useState(false);
  const [expanded, setExpanded] = useState(!compact);
  const [approvalState, setApprovalState] = useState<ApprovalState>("proposal_only");
  const frameRef = useRef<number | null>(null);
  const lastAdvanceRef = useRef<number>(0);

  useEffect(() => {
    setVisibleCount(isLive ? sourceEvents.length : 0);
    setReplaying(false);
    setReplayStopped(false);
    setApprovalState("proposal_only");
  }, [fixture?.run_id, isLive, sourceEvents.length]);

  useEffect(() => {
    if (!replaying) {
      if (frameRef.current != null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      return undefined;
    }
    const total = sourceEvents.length;
    const step = (now: number) => {
      if (visibleCount >= total) {
        setReplaying(false);
        return;
      }
      const currentEvent = sourceEvents[Math.max(0, visibleCount - 1)];
      const nextEvent = sourceEvents[visibleCount];
      const recordedGap = currentEvent
        ? Math.max(120, Math.min(900, Date.parse(nextEvent.timestamp) - Date.parse(currentEvent.timestamp)))
        : 120;
      if (now - lastAdvanceRef.current >= recordedGap) {
        lastAdvanceRef.current = now;
        setVisibleCount((count) => Math.min(total, count + 1));
      }
      frameRef.current = requestAnimationFrame(step);
    };
    lastAdvanceRef.current = performance.now();
    frameRef.current = requestAnimationFrame(step);
    return () => {
      if (frameRef.current != null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    };
  }, [replaying, sourceEvents, visibleCount]);

  const visibleEvents = sourceEvents.slice(0, visibleCount);
  const steps = deriveTimelineSteps(visibleEvents);
  const currentStep = steps[steps.length - 1];
  const source: DataSource = isLive ? "LIVE" : fixture?.fixture_label ?? "RECORDED_FIXTURE";
  const runtimeIdentity: RuntimeIdentity = isLive ? "HERMES_NATIVE_MCP" : fixture?.runtime_identity ?? "HERMES_NATIVE_MCP";
  const runStatus = runStatusFor(visibleEvents, replayStopped);
  const statusLabel = t(`timeline.run.${runStatus}`);

  const startReplay = () => {
    if (prefersReducedMotion()) {
      setVisibleCount(sourceEvents.length);
      setReplaying(false);
      return;
    }
    setReplayStopped(false);
    setVisibleCount((count) => (count >= sourceEvents.length ? 0 : count));
    setReplaying(true);
  };

  const stopReplay = () => {
    setReplaying(false);
    setReplayStopped(true);
    onStop?.();
  };

  const decide = (state: ApprovalState) => {
    setApprovalState(state);
    onApproval?.(state);
  };

  return (
    <section
      className={`timeline timeline--${runStatus}`}
      data-testid={testIds.agentRunTimeline}
      data-source={source}
      data-run-status={runStatus}
      aria-live="polite"
    >
      <header className="timeline__head">
        <div>
          <span className="kicker">{t("timeline.kicker")}</span>
          <h3>{t("timeline.title")}</h3>
        </div>
        <RuntimeTruthBadge
          truth={{ semantic: "DeepSeek", execution: runtimeIdentity, truth: "CityNexus", source, status: "ready" }}
          compact
        />
      </header>
      {source === "RECORDED_FIXTURE" && (
        <p className="fixture-banner" data-testid={testIds.timelineSource}>
          <b>{t("timeline.recorded")}</b> · {t("timeline.recordedNote")}
        </p>
      )}
      <div className="timeline__summary" data-testid="timeline-summary" data-status={runStatus}>
        <b>{statusLabel}</b>
        {currentStep && currentStep.label !== statusLabel && (
          <span>
            {currentStep.label}
            {currentStep.toolName ? ` · ${humanTool(currentStep.toolName)}` : ""}
            {currentStep.duration_ms ? ` · ${currentStep.duration_ms}ms` : ""}
          </span>
        )}
      </div>
      {replayStopped && (
        <p className="fixture-banner stopped" role="status">
          {t("timeline.stoppedLocally")}
        </p>
      )}
      {compact && !expanded ? (
        <button
          type="button"
          className="btn"
          data-testid="timeline-expand"
          onClick={() => setExpanded(true)}
        >
          {t("timeline.expand")}
        </button>
      ) : (
        <>
          {steps.length === 0 ? (
            <p className="muted">{t("timeline.empty")}</p>
          ) : (
            <ol className="timeline__steps">
              {steps.map((step) => (
                <li
                  key={step.id}
                  className={`timeline-step ${step.status}`}
                  data-testid={testIds.timelineStep}
                  data-status={step.status}
                  data-tool={step.toolName ?? ""}
                >
                  <span className="timeline-step__mark" aria-hidden="true" />
                  <div className="timeline-step__body">
                    <b>{step.label}</b>
                    {step.toolName && (
                      <code className="timeline-step__tool" title={step.toolName}>
                        {step.toolName}
                        {step.duration_ms ? ` · ${step.duration_ms}ms` : ""}
                      </code>
                    )}
                    <small>{step.summary}</small>
                    <time dateTime={step.timestamp}>{step.timestamp.slice(11, 23)}</time>
                  </div>
                  <span className="timeline-step__status">{t(`timeline.status.${step.status}`)}</span>
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
      {visibleEvents.some((item) => item.event_type === "proposal.created") && (
        <div className="proposal-summary" data-testid="proposal-summary">
          <b>{t("approval.proposal")}</b>
          <p>{t("approval.proposalDetail")}</p>
        </div>
      )}
      {steps.some((step) => step.status === "approval") && (
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
          </div>
          <div className="approval-actions">
            <button
              type="button"
              className="btn btn--approve"
              data-testid="approval-approve"
              onClick={() => decide("approved")}
            >
              {t("approval.approve")}
            </button>
            <button
              type="button"
              className="btn btn--reject"
              data-testid="approval-reject"
              onClick={() => decide("rejected")}
            >
              {t("approval.reject")}
            </button>
            <button type="button" className="btn" data-testid="approval-review" onClick={() => decide("review_requested")}>
              {t("approval.review")}
            </button>
          </div>
          <p className="muted small" data-testid="approval-state-copy">
            {t(`approval.state.${approvalState}`)} · {t("approval.authority")}
          </p>
        </div>
      )}
      <div className="timeline__controls">
        <button
          type="button"
          className="btn"
          data-testid={testIds.timelinePrev}
          onClick={() => {
            setReplaying(false);
            setVisibleCount((count) => Math.max(0, count - 1));
          }}
          disabled={visibleCount === 0}
        >
          {t("timeline.previous")}
        </button>
        <button
          type="button"
          className="btn"
          data-testid={testIds.timelineNext}
          onClick={() => {
            setReplaying(false);
            setVisibleCount((count) => Math.min(sourceEvents.length, count + 1));
          }}
          disabled={visibleCount >= sourceEvents.length}
        >
          {t("timeline.next")}
        </button>
        <button type="button" className="btn btn--primary" data-testid={testIds.timelineReplay} onClick={startReplay}>
          {replaying ? t("timeline.pause") : t("timeline.replay")}
        </button>
        {!isLive && (
          <button type="button" className="btn" data-testid={testIds.timelineStop} onClick={stopReplay}>
            {t("timeline.stop")}
          </button>
        )}
      </div>
      <p className="muted small" data-testid="timeline-count">
        {t("timeline.eventCount", { visible: visibleCount, total: sourceEvents.length })}
      </p>
    </section>
  );
}
