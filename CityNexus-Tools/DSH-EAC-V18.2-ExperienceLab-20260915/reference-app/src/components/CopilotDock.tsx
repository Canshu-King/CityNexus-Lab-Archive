import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useT } from "../i18n";
import { testIds } from "../testids";
import type { AgentRunFixture, CopilotMessage, RuntimeTruth } from "../types";
import { HERMES_FIXTURES, HERMES_RECORDED_RUN, type HermesFixtureKey } from "../data/hermesFixture";
import { AgentRunTimeline } from "./AgentRunTimeline";
import { RuntimeStatusBanner, RuntimeTruthBadge } from "./RuntimeTruthBadge";

const DIRECT_TRUTH: RuntimeTruth = {
  semantic: "DeepSeek",
  execution: "DIRECT",
  truth: "CityNexus",
  source: "RECORDED_FIXTURE",
  status: "ready",
};

const HERMES_TRUTH: RuntimeTruth = {
  semantic: "DeepSeek",
  execution: "HERMES_NATIVE_MCP",
  truth: "CityNexus",
  source: "RECORDED_FIXTURE",
  status: "ready",
};

const FALLBACK_TRUTH: RuntimeTruth = {
  semantic: "DeepSeek",
  execution: "FALLBACK",
  truth: "CityNexus",
  source: "RECORDED_FIXTURE",
  status: "deepseek_unavailable",
};

const UNAVAILABLE_TRUTH: RuntimeTruth = {
  semantic: "DeepSeek",
  execution: "UNAVAILABLE",
  truth: "CityNexus",
  source: "RECORDED_FIXTURE",
  status: "hermes_unavailable",
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
  activeFixture,
  onFixtureChange,
  isMobile,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigate: (route: string) => void;
  activeFixture: AgentRunFixture | null;
  onFixtureChange: (fixture: AgentRunFixture | null) => void;
  isMobile: boolean;
}) {
  const t = useT();
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [stopped, setStopped] = useState(false);
  const [showFullTimeline, setShowFullTimeline] = useState(!isMobile);
  const edgeRef = useRef<HTMLButtonElement | null>(null);
  const restoreFocusRef = useRef(false);
  const closeRef = useRef<HTMLButtonElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  const latestRuntime = useMemo(() => {
    const latest = [...messages].reverse().find((message) => message.runtime)?.runtime;
    return latest ?? DIRECT_TRUTH;
  }, [messages]);

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
    onFixtureChange(null);
    setStopped(false);
  };

  const sendHermes = () => {
    append({ id: nextMessageId(), role: "user", text: t("copilot.quickHermes") });
    append({
      id: nextMessageId(),
      role: "assistant",
      text: t("copilot.hermesResult"),
      intent: t("copilot.intent.replan"),
      runtime: HERMES_TRUTH,
      fixture: HERMES_RECORDED_RUN,
    });
    onFixtureChange(HERMES_RECORDED_RUN);
    setStopped(false);
  };

  const sendFallback = () => {
    append({ id: nextMessageId(), role: "user", text: "DeepSeek is unavailable. What still works?" });
    append({
      id: nextMessageId(),
      role: "assistant",
      text: "Fallback runtime is active. CityNexus deterministic facts and the saved plan remain available; no live Hermes run was started.",
      intent: "FALLBACK_PLAN",
      runtime: FALLBACK_TRUTH,
    });
    onFixtureChange(null);
    setStopped(false);
  };

  const sendUnavailable = () => {
    append({ id: nextMessageId(), role: "user", text: "Try a native Hermes run." });
    append({
      id: nextMessageId(),
      role: "assistant",
      text: "Hermes is unavailable in this reference snapshot. CityNexus did not invent a run. Next useful action: use DIRECT planning or review the saved plan.",
      intent: "HERMES_UNAVAILABLE",
      runtime: UNAVAILABLE_TRUTH,
    });
    onFixtureChange(null);
    setStopped(false);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = draft.trim();
    if (!value) return;
    setDraft("");
    const isHermes = /replan|替代|rain|雨|alternative|change/i.test(value);
    append({ id: nextMessageId(), role: "user", text: value });
    if (isHermes) {
      append({
        id: nextMessageId(),
        role: "assistant",
        text: t("copilot.hermesResult"),
        intent: t("copilot.intent.replan"),
        runtime: HERMES_TRUTH,
        fixture: HERMES_RECORDED_RUN,
      });
      onFixtureChange(HERMES_RECORDED_RUN);
    } else {
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
      onFixtureChange(null);
    }
    setStopped(false);
  };

  const miniPlaceholder = activeFixture ? t("copilot.miniActive") : t("copilot.miniIdle");
  const approvalNeeded = Boolean(activeFixture?.events.some((item) => item.event_type === "approval.required"));

  return (
    <aside
      className={`copilot${open ? " is-open" : " is-collapsed"}`}
      data-testid={testIds.copilotDock}
      aria-label={t("copilot.title")}
    >
      {!open && (
        <>
          <button
            ref={edgeRef}
            type="button"
            className="copilot-edge"
            onClick={() => onOpenChange(true)}
            aria-label={t("copilot.open")}
          >
            <span aria-hidden="true">✦</span>
            <span>{t("copilot.title")}</span>
            <i className={`copilot-dot ${activeFixture ? "active" : latestRuntime.status === "ready" ? "live" : "warn"}`} />
          </button>
          <form
            className="copilot-mini"
            data-testid={testIds.copilotMiniComposer}
            data-mini-state={activeFixture ? "active" : "idle"}
            onSubmit={(event: FormEvent) => {
              submit(event);
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
        <div className="copilot-panel" role="dialog" aria-label={t("copilot.title")}>
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
          <RuntimeTruthBadge truth={latestRuntime} compact />
          <RuntimeStatusBanner
            status={latestRuntime.status}
            onAction={() => onNavigate("journey")}
          />
          <div className="copilot-history" aria-live="polite">
            {messages.length === 0 && <p className="muted">{t("copilot.empty")}</p>}
            {messages.map((message) => (
              <article
                key={message.id}
                className={`bubble ${message.role}`}
                data-testid={testIds.copilotMessage}
                data-role={message.role}
              >
                <small>{message.role === "user" ? "You" : "CityNexus"}</small>
                <p>{message.text}</p>
                <div className="bubble__chips">
                  {message.intent && <span className="chip" data-testid="semantic-interpretation">{message.intent}</span>}
                  {message.whatIf && <span className="chip">{message.whatIf.status}</span>}
                  {message.runtime && (
                    <span className="chip" data-testid={testIds.runtimeExecution}>
                      {message.runtime.execution}
                    </span>
                  )}
                </div>
                {message.whatIf && (
                  <>
                    <button type="button" className="btn" onClick={() => onNavigate("recovery")}>
                      {t("pulse.openRecovery")}
                    </button>
                    <dl className="whatif">
                      <div>
                        <dt>Changed</dt>
                        <dd>{message.whatIf.changed_activity}</dd>
                      </div>
                      <div>
                        <dt>Protected</dt>
                        <dd>{message.whatIf.unchanged_commitments} C4 commitment unchanged</dd>
                      </div>
                    </dl>
                  </>
                )}
              </article>
            ))}
          </div>
          {activeFixture && (
            <div className="mission-strip" data-testid="copilot-mission">
              <small>{t("copilot.currentMission")}</small>
              <b>{activeFixture.scenario}</b>
              {approvalNeeded && <span className="chip warn">{t("copilot.approvalNeeded")}</span>}
            </div>
          )}
          {activeFixture && (
            <div className="fixture-switcher" role="group" aria-label={t("timeline.scenarios")}>
              <span className="muted small">{t("timeline.scenarios")}</span>
              {(["completed", "approved", "failed", "stopped"] as HermesFixtureKey[]).map((key) => (
                <button
                  key={key}
                  type="button"
                  className={`chip-btn${activeFixture.run_id === HERMES_FIXTURES[key].run_id ? " active" : ""}`}
                  data-testid={`fixture-${key}`}
                  onClick={() => onFixtureChange(HERMES_FIXTURES[key])}
                >
                  {t(`timeline.scenario.${key}`)}
                </button>
              ))}
            </div>
          )}
          {activeFixture && (
            <AgentRunTimeline
              fixture={activeFixture}
              compact={isMobile && !showFullTimeline}
              onStop={() => {
                setStopped(true);
                onFixtureChange(null);
              }}
            />
          )}
          {stopped && (
            <p className="fixture-banner stopped" role="status">
              {t("timeline.stoppedLocally")}
            </p>
          )}
          {activeFixture && isMobile && (
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
            <button type="button" className="chip-btn" data-testid="copilot-quick-fallback" onClick={sendFallback}>
              {t("runtime.fallback")}
            </button>
            <button type="button" className="chip-btn" data-testid="copilot-quick-unavailable" onClick={sendUnavailable}>
              {t("runtime.unavailable")}
            </button>
          </div>
          <form className="copilot-form" onSubmit={submit}>
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setDraft(event.target.value)}
              placeholder={t("copilot.placeholder")}
              aria-label={t("copilot.placeholder")}
              rows={2}
              data-testid={testIds.copilotInput}
            />
            <button type="submit" className="btn btn--primary" data-testid={testIds.copilotSend}>
              {t("copilot.send")}
            </button>
          </form>
        </div>
      )}
    </aside>
  );
}
