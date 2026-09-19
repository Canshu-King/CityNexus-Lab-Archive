import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { V8Data } from "../../app/v8Types";
import {
  cityNexusApi,
  type AgentMissionPlan,
  type CopilotResponse,
  type NativeRuntimeEvent,
} from "../../api/citynexus";
import { useLocale, useT } from "../../i18n/LocaleContext";
import { AgentRunRail, type AgentRailStep } from "./AgentRunRail";

type Message = { role: "user" | "assistant"; text: string; response?: CopilotResponse };
type NativeRun = NonNullable<CopilotResponse["agent_run"]>;

const EVENT_TYPES = [
  "semantic.interpreted",
  "mission.planned",
  "run.started",
  "tool.started",
  "tool.completed",
  "tool.failed",
  "gateway.checked",
  "guardian.checked",
  "proposal.created",
  "approval.required",
  "run.completed",
  "run.failed",
  "run.stopped",
] as const;

const TERMINAL_RE = /^(completed|succeeded|failed|cancelled|canceled|stopped|error)$/i;

const lifecycleLabels: Record<string, { en: string; zh: string }> = {
  "semantic.interpreted": { en: "Understanding request", zh: "理解请求" },
  "mission.planned": { en: "Mission plan ready", zh: "任务计划已生成" },
  "run.started": { en: "Starting native Hermes", zh: "启动原生 Hermes" },
  "gateway.checked": { en: "CityNexus Gateway checked", zh: "CityNexus Gateway 已检查" },
  "guardian.checked": { en: "Guardian checked", zh: "Guardian 已检查" },
  "proposal.created": { en: "Proposal created", zh: "方案已生成" },
  "approval.required": { en: "Waiting for approval", zh: "等待确认" },
  "run.completed": { en: "Mission complete", zh: "任务完成" },
  "run.failed": { en: "Mission failed", zh: "任务失败" },
  "run.stopped": { en: "Mission stopped", zh: "任务已停止" },
};

const toolLabels: Record<string, { en: string; zh: string }> = {
  inspect_journey: { en: "Inspect current Journey", zh: "检查当前行程" },
  inspect_twin: { en: "Inspect JourneyTwin", zh: "检查 JourneyTwin" },
  list_replans: { en: "Inspect proposals and commitments", zh: "检查方案和受保护承诺" },
  search_city_services: { en: "Search candidate places and services", zh: "搜索候选地点和服务" },
  request_replan: { en: "Request deterministic replan", zh: "请求确定性重规划" },
  accept_replan: { en: "Accept replan", zh: "接受重规划" },
  replace_activity: { en: "Replace activity", zh: "替换活动" },
  reschedule_activity: { en: "Reschedule activity", zh: "调整活动时间" },
  create_booking: { en: "Create booking", zh: "创建预订" },
  cancel_refundable_booking: { en: "Cancel refundable booking", zh: "取消可退款预订" },
  request_commitment_change: { en: "Request commitment change", zh: "请求修改受保护承诺" },
};

function terminalStatus(value: string | null | undefined) {
  return TERMINAL_RE.test(String(value ?? ""));
}

function eventKey(event: NativeRuntimeEvent) {
  return [
    event.event_type,
    event.event_id ?? "",
    event.sequence ?? "",
    event.tool_name ?? "",
    event.timestamp ?? "",
    event.duration_ms ?? "",
    event.approval_id ?? "",
    event.proposal_id ?? "",
  ].join("|");
}

function readStoredEvents(journeyId: string, runId: string): NativeRuntimeEvent[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(`citynexus.native-hermes.timeline.${journeyId}.${runId}`);
    const value = raw ? JSON.parse(raw) : [];
    return Array.isArray(value) ? (value as NativeRuntimeEvent[]).slice(-250) : [];
  } catch {
    return [];
  }
}

function mergeEvents(...groups: Array<NativeRuntimeEvent[] | undefined>) {
  const result: NativeRuntimeEvent[] = [];
  const seen = new Set<string>();
  for (const group of groups) {
    for (const item of group ?? []) {
      if (!item || typeof item !== "object") continue;
      const key = eventKey(item);
      if (seen.has(key)) continue;
      seen.add(key);
      result.push(item);
    }
  }
  return result
    .map((event, index) => ({ event, index }))
    .sort((left, right) => {
      const leftSequence = Number.isFinite(left.event.sequence) ? Number(left.event.sequence) : null;
      const rightSequence = Number.isFinite(right.event.sequence) ? Number(right.event.sequence) : null;
      if (leftSequence != null && rightSequence != null && leftSequence !== rightSequence) {
        return leftSequence - rightSequence;
      }
      const leftTime = left.event.timestamp ? Date.parse(String(left.event.timestamp)) : Number.NaN;
      const rightTime = right.event.timestamp ? Date.parse(String(right.event.timestamp)) : Number.NaN;
      if (Number.isFinite(leftTime) && Number.isFinite(rightTime) && leftTime !== rightTime) {
        return leftTime - rightTime;
      }
      return left.index - right.index;
    })
    .map(({ event }) => event)
    .slice(-250);
}

function statusForEvent(event: NativeRuntimeEvent): AgentRailStep["status"] {
  if (event.event_type === "approval.required" || event.status === "approval_required") return "approval";
  if (event.event_type.endsWith(".failed") || event.status === "failed") return "failed";
  if (event.event_type.endsWith(".completed") || event.status === "completed") return "done";
  if (event.event_type === "run.stopped" || event.status === "stopped") return "failed";
  return "active";
}

function formatDuration(value: number) {
  if (!Number.isFinite(value) || value <= 0) return "—";
  if (value < 1000) return `${Math.round(value)} ms`;
  return `${(value / 1000).toFixed(1)} s`;
}

function summaryText(event: NativeRuntimeEvent, zh: boolean) {
  if (event.tool_name && toolLabels[event.tool_name]) {
    return toolLabels[event.tool_name][zh ? "zh" : "en"];
  }
  return lifecycleLabels[event.event_type]?.[zh ? "zh" : "en"] ?? event.friendly_label;
}

function safeJson(value: unknown) {
  if (value === null || value === undefined) return "";
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export function NativeMissionTimeline({
  data,
  run,
  onNavigate,
  compact = false,
  onExecutionChange,
}: {
  data: V8Data;
  run: NativeRun;
  onNavigate: (route: string) => void;
  compact?: boolean;
  onExecutionChange?: (executed: boolean) => void;
}) {
  const { locale } = useLocale();
  const zh = locale === "zh-CN";
  const [events, setEvents] = useState<NativeRuntimeEvent[]>(() =>
    mergeEvents(run.initial_events, readStoredEvents(data.journey.id, run.run_id)),
  );
  const [runState, setRunState] = useState(run.status);
  const [actionState, setActionState] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);

  const appendEvents = useCallback((incoming: NativeRuntimeEvent[]) => {
    setEvents((current) => mergeEvents(current, incoming));
  }, []);

  // A closed panel or route unmount does not discard the mission timeline.
  // This is only a local UI cache; authoritative history is the server audit
  // timeline fetched below.
  useEffect(() => {
    setEvents(mergeEvents(run.initial_events, readStoredEvents(data.journey.id, run.run_id)));
    setRunState(run.status);
    setActionState(null);
    setStreamError(null);
  }, [data.journey.id, run.run_id]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(
        `citynexus.native-hermes.timeline.${data.journey.id}.${run.run_id}`,
        JSON.stringify(events.slice(-250)),
      );
    } catch {
      // Local storage is an enhancement only; server audit history remains authoritative.
    }
  }, [data.journey.id, events, run.run_id]);

  useEffect(() => {
    let cancelled = false;
    void cityNexusApi
      .getNativeHermesTimeline(data.journey.id, run.run_id)
      .then((payload) => {
        if (!cancelled) appendEvents(payload.events);
      })
      .catch(() => {
        // A freshly-created run may not have emitted an event yet.
      });
    return () => {
      cancelled = true;
    };
  }, [appendEvents, data.journey.id, run.run_id]);

  useEffect(() => {
    const url = run.events_url;
    if (!url || typeof window === "undefined") return undefined;
    let cancelled = false;
    let ended = false;
    let attempts = 0;
    let retryTimer: number | undefined;
    let source: EventSource | null = null;
    const connect = () => {
      if (cancelled || ended) return;
      source = new EventSource(url);
      const handleEvent = (incoming: Event) => {
        try {
          const payload = JSON.parse((incoming as MessageEvent<string>).data) as NativeRuntimeEvent;
          if (!payload || typeof payload !== "object") return;
          attempts = 0;
          setStreamError(null);
          appendEvents([payload]);
          if (payload.status) setRunState(String(payload.status));
          if (["run.completed", "run.failed", "run.stopped"].includes(payload.event_type)) {
            ended = true;
            source?.close();
            source = null;
          }
        } catch {
          setStreamError(zh ? "运行事件暂时无法解析" : "A runtime event could not be read");
        }
      };
      source.addEventListener("message", handleEvent);
      for (const name of EVENT_TYPES) source.addEventListener(name, handleEvent);
      source.onerror = () => {
        if (ended || cancelled) return;
        source?.close();
        source = null;
        attempts += 1;
        if (attempts <= 3) {
          setStreamError(zh ? "正在重新连接运行事件" : "Reconnecting to runtime events");
          retryTimer = window.setTimeout(connect, Math.min(5000, 500 * 2 ** (attempts - 1)));
        } else {
          setStreamError(zh ? "运行事件流不可用；已保留已收到的事件" : "Event stream unavailable; received events are preserved");
        }
      };
    };
    connect();
    return () => {
      cancelled = true;
      ended = true;
      if (retryTimer != null) window.clearTimeout(retryTimer);
      source?.close();
    };
  }, [appendEvents, run.events_url, zh]);

  useEffect(() => {
    let cancelled = false;
    const poll = () => {
      void cityNexusApi
        .getNativeHermesRun(data.journey.id, run.run_id)
        .then((payload) => {
          if (!cancelled && typeof payload.status === "string") setRunState(payload.status);
        })
        .catch(() => undefined);
    };
    poll();
    const timer = window.setInterval(poll, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [data.journey.id, run.run_id]);

  const executed = useMemo(
    () => events.some((event) => event.source === "HERMES_NATIVE" && (
      event.event_type === "run.started" || event.event_type.startsWith("tool.")
    )),
    [events],
  );
  useEffect(() => onExecutionChange?.(executed), [executed, onExecutionChange]);

  const steps = useMemo<AgentRailStep[]>(() => events.map((event, index) => {
    const detail: ReactNode = (
      <span className="cn-agent-event-detail">
        {event.tool_name ? <code>{event.tool_name}</code> : event.status}
        {event.duration_ms != null && ` · ${formatDuration(Number(event.duration_ms))}`}
        {event.policy_decision ? ` · ${event.policy_decision}` : ""}
      </span>
    );
    return {
      id: `${index}-${eventKey(event)}`,
      label: summaryText(event, zh),
      status: statusForEvent(event),
      detail: (
        <>
          {detail}
          <details className="cn-agent-raw">
            <summary>{zh ? "运行详情" : "Runtime details"}</summary>
            <code>{safeJson({
              event_type: event.raw_event_type ?? event.event_type,
              source: event.source,
              tool_name: event.tool_name,
              result_summary: event.result_summary,
              policy_decision: event.policy_decision,
            })}</code>
          </details>
        </>
      ),
    };
  }), [events, zh]);

  const toolEvents = events.filter((event) => event.event_type.startsWith("tool."));
  const currentTool = [...events].reverse().find((event) => event.event_type === "tool.started")?.tool_name;
  const totalDuration = events.reduce((sum, event) => sum + (Number(event.duration_ms) || 0), 0);
  const approvalEvent = [...events].reverse().find((event) =>
    event.event_type === "approval.required" || (
      Boolean(event.approval_id) && String(event.approval_status ?? "PENDING").toUpperCase() === "PENDING"
    ),
  );
  const proposalEvent = [...events].reverse().find((event) => event.event_type === "proposal.created" || event.proposal_id);
  const active = !terminalStatus(runState) && !events.some((event) => event.event_type === "run.stopped");

  const stop = async () => {
    if (!active) return;
    setActionState(zh ? "正在停止…" : "Stopping…");
    try {
      await cityNexusApi.stopNativeHermesRun(data.journey.id, run.run_id);
      setRunState("stopped");
      setActionState(zh ? "已通过 CityNexus 停止" : "Stopped through CityNexus");
    } catch (cause) {
      setActionState(cause instanceof Error ? cause.message : (zh ? "停止失败" : "Stop failed"));
    }
  };

  const approve = async () => {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setActionState(zh ? "离线时不能确认方案" : "Approval is disabled while offline");
      return;
    }
    if (!approvalEvent?.approval_id) {
      setActionState(zh ? "缺少 CityNexus approval_id，需打开恢复中心审核" : "CityNexus approval_id is not available; review in Recovery");
      return;
    }
    setActionState(zh ? "正在记录 CityNexus 确认…" : "Recording CityNexus approval…");
    try {
      await cityNexusApi.approveAgentAction(data.journey.id, approvalEvent.approval_id);
      setActionState(zh ? "确认已记录；仍需由 CityNexus 执行授权" : "Approval recorded; CityNexus still owns execution authorization");
    } catch (cause) {
      setActionState(cause instanceof Error ? cause.message : (zh ? "确认失败" : "Approval failed"));
    }
  };

  return (
    <section className={`cn-native-mission ${compact ? "compact" : ""}`} data-testid="native-hermes-timeline">
      <header className="cn-native-mission-head">
        <div>
          <b>{zh ? "Native Hermes 任务" : "Native Hermes mission"}</b>
          <small>{executed ? (zh ? "真实 MCP 运行中/已完成" : "Real MCP execution observed") : (zh ? "等待真实运行事件" : "Waiting for a real runtime event")}</small>
        </div>
        <span className={`cn-native-status ${terminalStatus(runState) ? "terminal" : "active"}`}>{runState}</span>
      </header>

      <div className="cn-copilot-observability" data-testid="native-hermes-observability">
        <span><b>run_id</b> <code>{run.run_id}</code></span>
        {run.mission_id && <span><b>mission</b> <code>{run.mission_id}</code></span>}
        <span><b>{zh ? "工具" : "tools"}</b> {toolEvents.length}</span>
        <span><b>{zh ? "当前" : "current"}</b> {currentTool ? (toolLabels[currentTool]?.[zh ? "zh" : "en"] ?? currentTool) : "—"}</span>
        <span><b>{zh ? "耗时" : "duration"}</b> {formatDuration(totalDuration)}</span>
      </div>

      {steps.length ? <AgentRunRail steps={steps} /> : <p className="cn-native-empty">{zh ? "正在等待 Hermes 的真实事件…" : "Waiting for Hermes to emit a real event…"}</p>}

      {run.mission_plan && (
        <details className="cn-native-plan">
          <summary>{zh ? "查看安全任务计划" : "View safe mission plan"}</summary>
          <ol>
            {run.mission_plan.steps.map((step) => (
              <li key={step.id}>
                <span>{zh ? localizePlanStep(step.operation) : step.operation}</span>
                {step.requires_authority && <small>{zh ? "CityNexus 授权" : "CityNexus authority"}</small>}
              </li>
            ))}
          </ol>
        </details>
      )}

      <div className="cn-native-proposal">
        <b>{zh ? "方案与承诺" : "Proposal & commitments"}</b>
        <span>{proposalEvent ? (zh ? "已收到方案事件，详情在运行详情中" : "Proposal event received; see runtime details") : (zh ? "等待确定性方案；不会静默修改行程" : "Awaiting a deterministic proposal; no silent mutation")}</span>
        <div className="cn-protected-badges">
          {(run.protected_commitments ?? []).map((commitment, index) => (
            <span key={String(commitment.id ?? index)}>{zh ? "受保护承诺" : "Protected commitment"}{commitment.id ? ` · ${String(commitment.id).slice(0, 8)}` : ""}</span>
          ))}
          {!run.protected_commitments?.length && run.mission_plan?.protected_activity_ids.map((id) => (
            <span key={id}>{zh ? "受保护活动" : "Protected activity"} · {id.slice(0, 8)}</span>
          ))}
        </div>
      </div>

      {approvalEvent && (
        <div className="cn-copilot-approval" data-testid="native-hermes-approval">
          <b>{zh ? "需要 CityNexus 确认" : "CityNexus approval required"}</b>
          <span>{zh ? "Hermes 不能越过 Gateway / Guardian 修改受保护承诺、预订或付款。" : "Hermes cannot bypass the Gateway / Guardian for protected commitments, bookings, or payment."}</span>
          <div>
            <button type="button" className="v8-primary" onClick={() => void approve()}>{zh ? "批准" : "Approve"}</button>
            <button type="button" className="v8-secondary" onClick={() => void stop()}>{zh ? "拒绝" : "Reject"}</button>
            <button type="button" className="v8-outline-button" onClick={() => onNavigate("authoritative")}>{zh ? "修改 / 审核" : "Modify / Review"}</button>
          </div>
        </div>
      )}

      {actionState && <p className="cn-copilot-action-state" role="status">{actionState}</p>}
      {streamError && <p className="cn-copilot-stream-state" role="status">{streamError}</p>}
      {active && <button type="button" className="cn-copilot-stop" onClick={() => void stop()}>{zh ? "停止任务" : "Stop mission"}</button>}
    </section>
  );
}

function localizePlanStep(operation: string) {
  const values: Record<string, string> = {
    "Inspect current Journey": "检查当前行程",
    "Inspect JourneyTwin": "检查 JourneyTwin",
    "Inspect protected commitments": "检查受保护承诺",
    "Inspect affected activities": "检查受影响活动",
    "Search candidate places and services": "搜索候选地点和服务",
    "Evaluate candidates against constraints": "按约束评估候选项",
    "Request a deterministic replan proposal": "请求确定性重规划方案",
    "Inspect proposal trade-offs": "检查方案权衡",
    "Proposal only; no mutation without user approval": "仅方案；未经确认不修改",
  };
  return values[operation] ?? operation;
}

export function CopilotDock({
  data,
  onNavigate,
}: {
  data: V8Data;
  onNavigate: (route: string) => void;
}) {
  const t = useT();
  const { locale } = useLocale();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<Message[]>(() => readStoredMessages(data.journey.id));
  const [error, setError] = useState<string | null>(null);
  const [lastRuntime, setLastRuntime] = useState("DIRECT");
  const latestNativeRun = useMemo<NativeRun | null>(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const run = messages[index].response?.agent_run;
      if (run) return run;
    }
    return null;
  }, [messages]);
  const localeCode = locale === "zh-CN" ? "zh" : "en";

  useEffect(() => {
    try {
      window.localStorage.setItem(
        `citynexus.copilot.history.${data.journey.id}`,
        JSON.stringify(messages.slice(-50)),
      );
    } catch {
      // Local persistence is best effort.
    }
  }, [data.journey.id, messages]);

  const send = async () => {
    const value = draft.trim();
    if (value.length < 2 || sending) return;
    setSending(true);
    setError(null);
    setDraft("");
    setMessages((current) => [...current, { role: "user", text: value }]);
    try {
      const response = await cityNexusApi.sendCopilotMessage(data.journey.id, value, localeCode);
      // Until the first real Hermes lifecycle/tool event arrives, the visible
      // execution identity remains DIRECT. The timeline callback upgrades it
      // only after native execution is observed.
      setLastRuntime("DIRECT");
      setMessages((current) => [...current, { role: "assistant", text: response.message, response }]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t("agent.sendError"));
    } finally {
      setSending(false);
    }
  };

  const continueAction = (action?: string) => {
    if (action === "REQUEST_PLACE_SEARCH") onNavigate("discover");
    if (action === "REQUEST_REPLAN") onNavigate("authoritative");
    if (action === "REQUEST_PREFERENCE_UPDATE") onNavigate("me");
  };

  return (
    <aside className={`cn-copilot-dock ${open ? "open" : "collapsed"}`} data-testid="v18-copilot-dock">
      {!open ? (
        <button className="cn-copilot-edge" type="button" onClick={() => setOpen(true)} aria-label={t("agent.citynexus")}>
          <span className="cn-copilot-edge-mark">✦</span>
          <span>{t("agent.citynexus")}</span>
          <i className="cn-copilot-status" />
        </button>
      ) : (
        <div className="cn-copilot-panel">
          <header className="cn-copilot-head">
            <div>
              <b>{t("agent.citynexus")}</b>
              <small>{locale === "zh-CN" ? "DeepSeek 语义 · Hermes 真实事件 · CityNexus 真相" : "DeepSeek semantics · real Hermes events · CityNexus truth"}</small>
            </div>
            <button type="button" className="cn-copilot-close" onClick={() => setOpen(false)} aria-label={t("shell.close")}>×</button>
          </header>
          <div className="cn-copilot-runtime">
            <span>Semantic: DeepSeek</span>
            <span>Execution: {lastRuntime}</span>
            <span>Truth: CityNexus</span>
          </div>
          <div className="cn-copilot-history" aria-live="polite">
            {messages.length === 0 && <p className="cn-copilot-empty">{locale === "zh-CN" ? "问我为什么这样安排、试算变化，或报告已经确认的中断。" : "Ask why, preview a change, or report a confirmed disruption."}</p>}
            {messages.map((item, index) => (
              <article key={`${item.role}-${index}`} className={`cn-copilot-bubble ${item.role}`}>
                <small>{item.role === "user" ? (locale === "zh-CN" ? "你" : "You") : "CityNexus"}</small>
                <p>{item.text}</p>
                {item.response?.intent && <span className="cn-copilot-chip">{item.response.intent.name}</span>}
                {item.response?.verification && <span className="cn-copilot-chip">{item.response.verification.status}</span>}
                {item.response?.action?.type && <button type="button" className="cn-copilot-link" onClick={() => continueAction(item.response?.action?.type)}>{item.response.action.type}</button>}
              </article>
            ))}
          </div>
          {latestNativeRun && (
            <NativeMissionTimeline
              data={data}
              run={latestNativeRun}
              onNavigate={onNavigate}
              onExecutionChange={(executed) => setLastRuntime(executed ? "HERMES_NATIVE_MCP" : "DIRECT")}
            />
          )}
          {error && <p className="cn-copilot-error" role="alert">{error}</p>}
          <form className="cn-copilot-form" onSubmit={(event) => { event.preventDefault(); void send(); }}>
            <textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("agent.inputPlaceholder")} aria-label={t("agent.message")} rows={2} />
            <button className="v8-primary" type="submit" disabled={sending || draft.trim().length < 2}>{sending ? t("agent.working") : t("agent.send")}</button>
          </form>
        </div>
      )}
    </aside>
  );
}

function readStoredMessages(journeyId: string): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(`citynexus.copilot.history.${journeyId}`);
    const value = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is Message =>
      item && (item.role === "user" || item.role === "assistant") && typeof item.text === "string",
    ).slice(-50);
  } catch {
    return [];
  }
}
