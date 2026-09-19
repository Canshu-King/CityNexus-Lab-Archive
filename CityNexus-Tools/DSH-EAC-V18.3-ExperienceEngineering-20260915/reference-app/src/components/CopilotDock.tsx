import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useLocale, useT } from "../i18n";
import { testIds } from "../testids";
import type { CopilotMessage, RuntimeTruth } from "../types";
import { useExperienceAdapter, useApprovalLifecycle, useCopilotMission, useRunEvents } from "../adapters/ExperienceAdapterContext";
import { useOnlineStatus } from "../pwa/onlineStatus";
import { AgentRunTimeline } from "./AgentRunTimeline";
import { RuntimeStatusBanner, RuntimeTruthBadge } from "./RuntimeTruthBadge";
import { CapabilitySummary } from "../features/capability/CapabilitySummary";
import { loadCapabilities, summarizeCapabilities } from "../features/capability/capabilityStore";

const DIRECT_TRUTH: RuntimeTruth = {
  semantic: "DeepSeek",
  execution: "DIRECT",
  truth: "CityNexus",
  source: "RECORDED_FIXTURE",
  status: "ready",
};

let messageSeq = 0;
function nextMessageId(): string {
  messageSeq += 1;
  return `copilot-message-${messageSeq}`;
}

export function CopilotDock({
  open,
  onOpenChange,
  onNavigate,
  isMobile,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigate: (route: string) => void;
  isMobile: boolean;
}) {
  const t = useT();
  const { locale } = useLocale();
  const adapter = useExperienceAdapter();
  const { online } = useOnlineStatus();
  const mission = useCopilotMission();
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [showFullTimeline, setShowFullTimeline] = useState(!isMobile);
  const [stoppedLocal, setStoppedLocal] = useState(false);
  const edgeRef = useRef<HTMLButtonElement | null>(null);
  const closeRef = useRef<HTMLButtonElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const restoreFocusRef = useRef(false);

  const runState = useRunEvents(activeRunId);
  const activeRun = runState.run;
  const proposalId = useMemo(
    () => runState.events.find((event) => event.proposal_id)?.proposal_id ?? undefined,
    [runState.events],
  );
  const approval = useApprovalLifecycle(proposalId);

  const runtimeTruth: RuntimeTruth = useMemo(
    () => ({
      semantic: "DeepSeek",
      execution: activeRun?.runtime_identity ?? (activeRunId ? "HERMES_NATIVE_MCP" : "DIRECT"),
      truth: "CityNexus",
      source: activeRun?.source ?? adapter.source,
      status: online ? "ready" : "offline_stale",
    }),
    [activeRun, activeRunId, adapter.source, online],
  );

  useEffect(() => {
    if (!open) return undefined;
    const timer = window.setTimeout(() => {
      (isMobile ? inputRef.current ?? closeRef.current : closeRef.current)?.focus();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [open, isMobile]);

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        restoreFocusRef.current = true;
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  useEffect(() => {
    if (!open && restoreFocusRef.current) {
      restoreFocusRef.current = false;
      edgeRef.current?.focus();
    }
  }, [open]);

  const append = (message: CopilotMessage) => setMessages((current) => [...current, message]);

  const startMission = async (message: string) => {
    append({ id: nextMessageId(), role: "user", text: message });
    const started = await mission.start({ message, locale: locale === "zh-CN" ? "zh-CN" : "en" });
    if (!started) {
      append({
        id: nextMessageId(),
        role: "assistant",
        text: mission.error ?? "Runtime unavailable. No live run was started.",
        runtime: { ...DIRECT_TRUTH, execution: "UNAVAILABLE", source: "OFFLINE", status: "offline_stale" },
      });
      return;
    }
    setActiveRunId(started.run.run_id);
    setStoppedLocal(false);
    append({
      id: nextMessageId(),
      role: "assistant",
      text: started.answer,
      intent: started.semantic_intent,
      runtime: { ...runtimeTruth, source: started.source, execution: started.run.runtime_identity },
    });
  };

  const sendWhatIf = () => {
    append({ id: nextMessageId(), role: "user", text: t("copilot.quickWhatIf") });
    append({
      id: nextMessageId(),
      role: "assistant",
      text: t("copilot.whatIfResult"),
      intent: t("copilot.intent.whatIf"),
      runtime: DIRECT_TRUTH,
      whatIf: {
        simulation_only: true,
        status: t("copilot.whatIfStatus"),
        changed_activity: "Five Great Avenues morning walk → 09:30 start",
        unchanged_commitments: 1,
      },
    });
    setActiveRunId(null);
  };

  const sendHermes = () => {
    void startMission(t("copilot.quickHermes"));
  };

  const scenarios = adapter.listRecordedScenarios?.() ?? [];
  const miniPlaceholder = activeRun
    ? activeRun.status === "approval_required"
      ? "Hermes · Waiting for approval…"
      : "Hermes · Searching alternatives…"
    : t("copilot.miniIdle");

  return (
    <aside
      className={`copilot${open ? " is-open" : " is-collapsed"}`}
      data-testid={testIds.copilotDock}
      aria-label={t("copilot.title")}
    >
      {!open && (
        <>
          <button ref={edgeRef} type="button" className="copilot-edge" onClick={() => onOpenChange(true)} aria-label={t("copilot.open")}>
            <span aria-hidden="true">✦</span>
            <span>{t("copilot.title")}</span>
            <i className={`copilot-dot ${activeRun ? "active" : online ? "live" : "warn"}`} />
          </button>
          <form
            className="copilot-mini"
            data-testid={testIds.copilotMiniComposer}
            data-mini-state={activeRun ? "active" : "idle"}
            data-mini-placeholder={miniPlaceholder}
            onSubmit={(event: FormEvent) => {
              event.preventDefault();
              const value = draft.trim();
              if (!value) return;
              setDraft("");
              void startMission(value);
              onOpenChange(true);
            }}
          >
            <input
              value={draft}
              onChange={(event: ChangeEvent<HTMLInputElement>) => setDraft(event.target.value)}
              placeholder={miniPlaceholder}
              aria-label={miniPlaceholder}
            />
            <button type="submit" className="btn btn--primary" aria-label={t("copilot.send")}>
              {t("copilot.send")}
            </button>
          </form>
        </>
      )}
      {open && (
        <div className="copilot-panel" role="dialog" aria-modal="true" aria-label={t("copilot.title")}>
          <header className="copilot-head">
            <div>
              <span className="kicker">{t("copilot.kicker")}</span>
              <b>{t("copilot.title")}</b>
              <small>{t("copilot.subtitle")}</small>
            </div>
            <button
              ref={closeRef}
              type="button"
              className="icon-btn"
              onClick={() => {
                restoreFocusRef.current = true;
                onOpenChange(false);
              }}
              aria-label={t("copilot.close")}
            >
              ×
            </button>
          </header>
          <RuntimeTruthBadge truth={runtimeTruth} compact />
          <RuntimeStatusBanner status={runtimeTruth.status} onAction={() => onNavigate("journey")} />
          {summarizeCapabilities(loadCapabilities()).all.some((item) => item.recognized) && (
            <CapabilitySummary compact className="copilot-capability-summary" />
          )}
          <div className="copilot-history" aria-live="polite">
            {messages.length === 0 && <p className="muted">{t("copilot.empty")}</p>}
            {messages.map((message) => (
              <article key={message.id} className={`bubble ${message.role}`} data-testid={testIds.copilotMessage} data-role={message.role}>
                <small>{message.role === "user" ? "You" : "CityNexus"}</small>
                <p>{message.text}</p>
                <div className="bubble__chips">
                  {message.intent && <span className="chip" data-testid="semantic-interpretation">{message.intent}</span>}
                  {message.whatIf && <span className="chip">{message.whatIf.status}</span>}
                  {message.runtime && <span className="chip" data-testid={testIds.runtimeExecution}>{message.runtime.execution}</span>}
                </div>
              </article>
            ))}
          </div>
          {activeRun && (
            <div className="mission-strip" data-testid="copilot-mission">
              <small>{t("copilot.currentMission")}</small>
              <b>
                {activeRun.runtime_identity} · {activeRun.status}
              </b>
              {activeRun.current_tool && <span className="chip">current: {activeRun.current_tool}</span>}
              {activeRun.status === "approval_required" && <span className="chip warn">{t("copilot.approvalNeeded")}</span>}
            </div>
          )}
          {activeRun && scenarios.length > 0 && (
            <div className="fixture-switcher" role="group" aria-label={t("timeline.scenarios")}>
              <span className="muted small">{t("timeline.scenarios")}</span>
              {scenarios.map((scenario) => (
                <button
                  key={scenario.key}
                  type="button"
                  className="chip-btn"
                  data-testid={`fixture-${scenario.key}`}
                  onClick={() => {
                    adapter.selectRecordedScenario?.(scenario.key);
                    void startMission("replan");
                  }}
                >
                  {scenario.label}
                </button>
              ))}
            </div>
          )}
          {activeRun && (
            <AgentRunTimeline
              events={runState.events}
              runStatus={activeRun.status}
              source={activeRun.source}
              connection={runState.isLive ? "live" : activeRun?.source === "OFFLINE" ? "offline" : runState.loading ? "connecting" : activeRun?.source === "RECORDED_FIXTURE" ? "recorded" : "idle"}
              approvalState={approval.state}
              submitting={approval.submitting}
              offline={!online || adapter.source === "OFFLINE"}
              onApproval={(decision) => void approval.decide(decision)}
              onStop={() => {
                void runState.stop().then(() => setStoppedLocal(true));
              }}
              compact={isMobile && !showFullTimeline}
            />
          )}
          {stoppedLocal && (
            <p className="fixture-banner stopped" role="status">
              Replay stopped locally. No server event was fabricated.
            </p>
          )}
          {activeRun && isMobile && (
            <button
              type="button"
              className="btn"
              data-testid="copilot-toggle-timeline"
              onClick={() => setShowFullTimeline((value) => !value)}
            >
              {showFullTimeline ? t("timeline.collapse") : t("copilot.expandTimeline")}
            </button>
          )}
          <div className="copilot-quick">
            <button type="button" className="chip-btn" data-testid={testIds.copilotQuickWhatIf} onClick={sendWhatIf}>
              {t("copilot.quickWhatIf")}
            </button>
            <button type="button" className="chip-btn" data-testid={testIds.copilotQuickHermes} onClick={sendHermes}>
              {t("copilot.quickHermes")}
            </button>
            <button
              type="button"
              className="chip-btn"
              data-testid="copilot-quick-fallback"
              onClick={() => {
                append({
                  id: nextMessageId(),
                  role: "assistant",
                  text: "FALLBACK runtime is reference-only. CityNexus deterministic facts remain available.",
                  runtime: { ...DIRECT_TRUTH, execution: "FALLBACK", source: "OFFLINE", status: "offline_stale" },
                });
              }}
            >
              {t("runtime.fallback")}
            </button>
            <button
              type="button"
              className="chip-btn"
              data-testid="copilot-quick-unavailable"
              onClick={() => {
                append({
                  id: nextMessageId(),
                  role: "assistant",
                  text: "Hermes is UNAVAILABLE. CityNexus did not invent a live run; use DIRECT planning or the saved plan.",
                  runtime: { ...DIRECT_TRUTH, execution: "UNAVAILABLE", source: "OFFLINE", status: "hermes_unavailable" },
                });
              }}
            >
              {t("runtime.unavailable")}
            </button>
          </div>
          <form
            className="copilot-form"
            onSubmit={(event: FormEvent) => {
              event.preventDefault();
              const value = draft.trim();
              if (!value) return;
              setDraft("");
              void startMission(value);
            }}
          >
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setDraft(event.target.value)}
              placeholder={t("copilot.placeholder")}
              aria-label={t("copilot.placeholder")}
              rows={2}
              data-testid={testIds.copilotInput}
            />
            <button type="submit" className="btn btn--primary" data-testid={testIds.copilotSend} disabled={mission.loading}>
              {mission.loading ? t("copilot.sending") : t("copilot.send")}
            </button>
          </form>
        </div>
      )}
    </aside>
  );
}
