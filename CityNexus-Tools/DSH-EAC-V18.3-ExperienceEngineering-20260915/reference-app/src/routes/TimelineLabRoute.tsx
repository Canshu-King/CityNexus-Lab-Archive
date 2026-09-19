import { useMemo } from "react";
import { AgentRunTimeline } from "../components/AgentRunTimeline";
import { normalizeEventBatch } from "../adapters/normalize";
import type { NormalizedAgentEvent } from "../adapters/contract";

function buildStressEvents(count: number): NormalizedAgentEvent[] {
  const raw: Array<Record<string, unknown>> = [
    { event_type: "semantic.interpreted", sequence_no: 1, timestamp: "2026-09-15T08:00:00.000+08:00", status: "completed" },
    { event_type: "mission.planned", sequence_no: 2, timestamp: "2026-09-15T08:00:00.100+08:00", status: "completed" },
    { event_type: "run.started", sequence_no: 3, timestamp: "2026-09-15T08:00:00.200+08:00", status: "started" },
  ];
  let sequence = raw.length;
  const tools = ["inspect_journey", "inspect_twin", "search_city_services", "request_replan"];
  while (raw.length < count - 2) {
    const tool = tools[sequence % tools.length];
    raw.push({ event_type: "tool.started", sequence_no: ++sequence, tool_name: tool, timestamp: new Date(Date.parse("2026-09-15T08:00:00.200+08:00") + sequence * 120).toISOString(), status: "started" });
    raw.push({ event_type: "tool.completed", sequence_no: ++sequence, tool_name: tool, timestamp: new Date(Date.parse("2026-09-15T08:00:00.200+08:00") + sequence * 120).toISOString(), status: "completed", duration_ms: 120 });
  }
  raw.push({ event_type: "approval.required", sequence_no: ++sequence, timestamp: new Date(Date.parse("2026-09-15T08:00:00.200+08:00") + sequence * 120).toISOString(), status: "approval_required" });
  raw.push({ event_type: "run.completed", sequence_no: ++sequence, timestamp: new Date(Date.parse("2026-09-15T08:00:00.200+08:00") + sequence * 120).toISOString(), status: "completed" });
  return normalizeEventBatch(raw, { runId: `stress-${count}`, source: "RECORDED_FIXTURE" }).slice(0, count);
}

export default function TimelineLabRoute({ count }: { count: number }) {
  const events = useMemo(() => buildStressEvents(count), [count]);
  return (
    <section className="card" data-testid="timeline-lab">
      <span className="kicker">RECORDED_FIXTURE · STRESS LAB</span>
      <h2>Agent timeline rendering · {count} events</h2>
      <p className="muted">
        This lab renders a recorded stress fixture. It does not claim a live run and it does not fabricate
        progress; only the latest 50 events are rendered until you choose “Show all”.
      </p>
      <AgentRunTimeline events={events} runStatus="approval_required" source="RECORDED_FIXTURE" connection="recorded" approvalState="approval_required" />
    </section>
  );
}
