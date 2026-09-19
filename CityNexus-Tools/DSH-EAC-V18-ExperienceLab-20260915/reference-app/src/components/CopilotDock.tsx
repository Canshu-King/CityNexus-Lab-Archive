import { useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { useT } from "../i18n";
import { testIds } from "../testids";
import type { AgentRunFixture, CopilotMessage, RuntimeTruth } from "../types";
import { HERMES_FIXTURES, HERMES_RECORDED_RUN, type HermesFixtureKey } from "../data/hermesFixture";
import { AgentRunTimeline } from "./AgentRunTimeline";
import { RuntimeTruthBadge } from "./RuntimeTruthBadge";

const DIRECT_TRUTH: RuntimeTruth = {
  semantic: "DeepSeek",
  execution: "DIRECT",
  truth: "CityNexus",
  source: "RECORDED_FIXTURE",
};

const HERMES_TRUTH: RuntimeTruth = {
  semantic: "DeepSeek",
  execution: "HERMES_NATIVE_MCP",
  truth: "CityNexus",
  source: "RECORDED_FIXTURE",
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
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigate: (route: string) => void;
  activeFixture: AgentRunFixture | null;
  onFixtureChange: (fixture: AgentRunFixture | null) => void;
}) {
  const t = useT();
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [stopped, setStopped] = useState(false);

  const latestRuntime = useMemo(() => {
    const latest = [...messages].reverse().find((message) => message.runtime)?.runtime;
    return latest ?? DIRECT_TRUTH;
  }, [messages]);

  const sendWhatIf = () => {
    const userText = t("copilot.quickWhatIf");
    setMessages((current) => [
      ...current,
      { id: nextMessageId(), role: "user", text: userText },
      {
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
      },
    ]);
    onFixtureChange(null);
    setStopped(false);
  };

  const sendHermes = () => {
    const userText = t("copilot.quickHermes");
    setMessages((current) => [
      ...current,
      { id: nextMessageId(), role: "user", text: userText },
      {
        id: nextMessageId(),
        role: "assistant",
        text: t("copilot.hermesResult"),
        intent: t("copilot.intent.replan"),
        runtime: HERMES_TRUTH,
        fixture: HERMES_RECORDED_RUN,
      },
    ]);
    onFixtureChange(HERMES_RECORDED_RUN);
    setStopped(false);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = draft.trim();
    if (!value) return;
    setDraft("");
    const isHermes = /replan|替代|rain|雨|alternative|change/i.test(value);
    setMessages((current) => [
      ...current,
      { id: nextMessageId(), role: "user", text: value },
      isHermes
        ? {
            id: nextMessageId(),
            role: "assistant",
            text: t("copilot.hermesResult"),
            intent: t("copilot.intent.replan"),
            runtime: HERMES_TRUTH,
            fixture: HERMES_RECORDED_RUN,
          }
        : {
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
          },
    ]);
    onFixtureChange(isHermes ? HERMES_RECORDED_RUN : null);
    setStopped(false);
  };

  return (
    <aside
      className={`copilot${open ? " is-open" : " is-collapsed"}`}
      data-testid={testIds.copilotDock}
      aria-label={t("copilot.title")}
    >
      {!open && (
        <>
          <button
            type="button"
            className="copilot-edge"
            onClick={() => onOpenChange(true)}
            aria-label={t("copilot.open")}
          >
            <span aria-hidden="true">✦</span>
            <span>{t("copilot.title")}</span>
            <i className={`copilot-dot ${latestRuntime.source === "LIVE" ? "live" : "fixture"}`} />
          </button>
          <form
            className="copilot-mini"
            data-testid={testIds.copilotMiniComposer}
            onSubmit={(event: FormEvent) => {
              submit(event);
              onOpenChange(true);
            }}
          >
            <input
              value={draft}
              onChange={(event: ChangeEvent<HTMLInputElement>) => setDraft(event.target.value)}
              placeholder={t("copilot.mini")}
              aria-label={t("copilot.mini")}
            />
            <button type="submit" className="btn btn--primary" aria-label={t("copilot.send")}>
              {t("copilot.send")}
            </button>
          </form>
        </>
      )}
      {open && (
        <div className="copilot-panel">
          <header className="copilot-head">
            <div>
              <span className="kicker">{t("copilot.kicker")}</span>
              <b>{t("copilot.title")}</b>
              <small>{t("copilot.subtitle")}</small>
            </div>
            <button
              type="button"
              className="icon-btn"
              onClick={() => onOpenChange(false)}
              aria-label={t("copilot.close")}
            >
              ×
            </button>
          </header>
          <RuntimeTruthBadge truth={latestRuntime} compact />
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
                  {message.intent && <span className="chip">{message.intent}</span>}
                  {message.whatIf && <span className="chip">{message.whatIf.status}</span>}
                  {message.runtime && (
                    <span className="chip" data-testid={testIds.runtimeExecution}>
                      {message.runtime.execution}
                    </span>
                  )}
                </div>
                {message.whatIf && (
                  <button type="button" className="btn" onClick={() => onNavigate("recovery")}>
                    Review recovery
                  </button>
                )}
                {message.whatIf && (
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
                )}
              </article>
            ))}
          </div>
          {activeFixture && (
            <div className="fixture-switcher" role="group" aria-label={t("timeline.scenarios")}>
              <span className="muted small">{t("timeline.scenarios")}</span>
              {(["completed", "failed", "stopped"] as HermesFixtureKey[]).map((key) => (
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
              onStop={() => {
                setStopped(true);
                onFixtureChange(null);
              }}
            />
          )}
          {stopped && (
            <p className="fixture-banner stopped" role="status">
              Recorded run stopped locally · no server mutation.
            </p>
          )}
          <div className="copilot-quick">
            <button type="button" className="chip-btn" data-testid={testIds.copilotQuickWhatIf} onClick={sendWhatIf}>
              {t("copilot.quickWhatIf")}
            </button>
            <button type="button" className="chip-btn" data-testid={testIds.copilotQuickHermes} onClick={sendHermes}>
              {t("copilot.quickHermes")}
            </button>
          </div>
          <form className="copilot-form" onSubmit={submit}>
            <textarea
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
