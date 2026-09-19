import { useEffect, useMemo, useRef, useState } from "react";
import { useT } from "../i18n";
import { prefersReducedMotion } from "../motion";
import { testIds } from "../testids";
import type { AgentRunEvent, AgentRunFixture, DataSource, TimelineStep } from "../types";
import { RuntimeTruthBadge } from "./RuntimeTruthBadge";

function statusForEvent(event: AgentRunEvent): TimelineStep["status"] {
  switch (event.event_type) {
    case "run.started":
      return "done";
    case "tool.started":
      return "active";
    case "tool.completed":
      return "done";
    case "tool.failed":
      return "failed";
    case "approval.required":
      return "approval";
    case "run.completed":
      return "done";
    case "run.stopped":
      return "stopped";
    default:
      return "pending";
  }
}

function labelForEvent(event: AgentRunEvent, t: (key: string) => string): string {
  const tool = event.tool_name ?? t("timeline.tool");
  switch (event.event_type) {
    case "run.started":
      return "Run started";
    case "tool.started":
      return `Started · ${tool}`;
    case "tool.completed":
      return `Completed · ${tool}`;
    case "tool.failed":
      return `Failed · ${tool}`;
    case "approval.required":
      return `Approval required · ${tool}`;
    case "run.completed":
      return "Run completed";
    case "run.stopped":
      return "Run stopped";
    default:
      return tool;
  }
}

export function deriveTimelineSteps(events: AgentRunEvent[], t: (key: string) => string): TimelineStep[] {
  return events.map((event) => ({
    id: event.id,
    event_type: event.event_type,
    label: labelForEvent(event, t),
    toolName: event.tool_name,
    status: statusForEvent(event),
    timestamp: event.timestamp,
    summary: event.summary,
    source: event.source,
  }));
}

/**
 * Agent progress is derived strictly from the events array. The replay control
 * only reveals recorded events with requestAnimationFrame; it never fabricates
 * tool execution with setTimeout/setInterval. A real LIVE run can bind the SSE
 * URL contract instead of using the fixture replay.
 */
export function AgentRunTimeline({
  fixture,
  liveEventsUrl,
  liveEvents,
  onStop,
}: {
  fixture?: AgentRunFixture;
  liveEventsUrl?: string;
  liveEvents?: AgentRunEvent[];
  onStop?: () => void;
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
  const frameRef = useRef<number | null>(null);
  const lastAdvanceRef = useRef<number>(0);

  useEffect(() => {
    setVisibleCount(isLive ? sourceEvents.length : 0);
    setReplaying(false);
    setReplayStopped(false);
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
  const steps = deriveTimelineSteps(visibleEvents, t);
  const source: DataSource = isLive ? "LIVE" : fixture?.fixture_label ?? "RECORDED_FIXTURE";
  const runtimeIdentity = isLive ? "HERMES_NATIVE_MCP" : fixture?.runtime_identity ?? "HERMES_NATIVE_MCP";

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

  return (
    <section className="timeline" data-testid={testIds.agentRunTimeline} data-source={source}>
      <header className="timeline__head">
        <div>
          <span className="kicker">{t("timeline.kicker")}</span>
          <h3>{t("timeline.title")}</h3>
        </div>
        <RuntimeTruthBadge
          truth={{ semantic: "DeepSeek", execution: runtimeIdentity, truth: "CityNexus", source }}
          compact
        />
      </header>
      {source === "RECORDED_FIXTURE" && (
        <p className="fixture-banner" data-testid={testIds.timelineSource}>
          <b>{t("timeline.recorded")}</b> · {t("timeline.recordedNote")}
        </p>
      )}
      {replayStopped && (
        <p className="fixture-banner stopped" role="status">
          Replay stopped locally. No server event was fabricated.
        </p>
      )}
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

export { statusForEvent };
