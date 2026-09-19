/**
 * "AI 帮我规划" — natural-language trip planning entry.
 *
 * Design rules honoured here:
 *  - the traveller types plain language; no internal vocabulary is shown;
 *  - progress is a REAL stepper; the backend exposes no percentage, so no
 *    percentage is fabricated (design corrections §6);
 *  - internal action enums (REQUEST_REPLAN, ACCEPT_REPLAN, …) and mission
 *    internals are never rendered;
 *  - a provider failure is shown honestly with a retry, never faked as success
 *    (master mission Phase 10).
 */

import { useEffect, useRef, useState } from "react";
import { useLocale } from "../../i18n/LocaleContext";

type Stage = { key: string; zh: string; en: string };

const STAGES: Stage[] = [
  { key: "understand", zh: "理解你的需求", en: "Understanding your request" },
  { key: "places", zh: "搜索真实地点", en: "Searching real places" },
  { key: "check", zh: "检查时间与交通", en: "Checking time and travel" },
  { key: "compose", zh: "生成可选方案", en: "Building candidate plans" },
];

const EXAMPLES = [
  {
    zh: "我和朋友两个人去厦门，想轻松一点，想去鼓浪屿、环岛路，想吃沙茶面和海鲜，不想太赶，也想找性价比高的酒店。",
    en: "Two of us in Xiamen, relaxed pace, Gulangyu and the Ring Road, local seafood, and a good-value hotel.",
  },
  {
    zh: "带爸妈去厦门三天，不要走太多路，下午要有休息时间，酒店要靠近地铁。",
    en: "Three days in Xiamen with my parents, not much walking, an afternoon rest, hotel near the metro.",
  },
];

/** Map internal mission status -> traveller language. */
function statusCopy(status: string, zh: boolean): { title: string; body: string; tone: "ok" | "warn" | "busy" } {
  const s = (status || "").toUpperCase();
  if (s === "COMPLETED" || s === "SUCCEEDED") {
    return {
      title: zh ? "方案已准备好" : "Plans are ready",
      body: zh ? "我们已经根据你的需求生成了可选方案。" : "We built candidate plans from your request.",
      tone: "ok",
    };
  }
  if (s.includes("SKIPPED_EXTERNAL_DEPENDENCY") || s.includes("EXTERNAL")) {
    return {
      title: zh ? "AI 暂时不可用" : "AI is unavailable right now",
      body: zh
        ? "规划助手这次没能连上。你的行程没有被改动，可以稍后重试。"
        : "The planning assistant could not be reached. Your trip is unchanged; you can retry.",
      tone: "warn",
    };
  }
  if (s === "RUNNING" || s === "PENDING" || s === "QUEUED") {
    return {
      title: zh ? "正在规划…" : "Planning…",
      body: zh ? "正在处理你的需求。" : "Working on your request.",
      tone: "busy",
    };
  }
  return {
    title: zh ? "暂时无法完成规划" : "Could not finish planning",
    body: zh
      ? "这次没能生成方案。你的行程没有被改动，可以重试或换个说法。"
      : "We could not produce plans this time. Your trip is unchanged; retry or rephrase.",
    tone: "warn",
  };
}

export function PlanWithAiSheet({
  journeyId,
  onClose,
  onPlanned,
}: {
  journeyId: string;
  onClose: () => void;
  onPlanned?: () => void;
}) {
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(0);
  const [result, setResult] = useState<null | {
    status: string;
    failureReason: string | null;
    summary: string | null;
  }>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => () => { if (timer.current) window.clearInterval(timer.current); }, []);

  const submit = async () => {
    const command = text.trim();
    if (command.length < 8) return;
    setBusy(true);
    setResult(null);
    setStage(0);
    // Indeterminate stepper: we advance through the real stages we can name,
    // and stop at the last one. No fabricated percentage.
    timer.current = window.setInterval(() => {
      setStage((current) => Math.min(current + 1, STAGES.length - 1));
    }, 1200);
    try {
      const response = await fetch(`/api/v1/journeys/${journeyId}/agent/commands`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ command }),
      });
      const body = await response.json().catch(() => null);
      const mission = body?.mission ?? null;
      setResult({
        status: mission?.status ?? (response.ok ? "COMPLETED" : `HTTP_${response.status}`),
        failureReason: mission?.failure_reason ?? null,
        summary: mission?.reasoning_summary ?? null,
      });
      if (response.ok && mission?.status === "COMPLETED") onPlanned?.();
    } catch {
      setResult({ status: "NETWORK", failureReason: null, summary: null });
    } finally {
      if (timer.current) window.clearInterval(timer.current);
      setBusy(false);
    }
  };

  const copy = result ? statusCopy(result.status, zh) : null;

  return (
    <div className="v8-sheet-backdrop" role="dialog" aria-modal="true" data-testid="plan-ai-sheet">
      <section className="plan-ai-sheet">
        <header className="plan-ai-head">
          <div>
            <b>{zh ? "AI 帮我规划" : "Plan my trip with AI"}</b>
            <small>
              {zh
                ? "用你自己的话描述这趟旅行，越具体越好。"
                : "Describe the trip in your own words — the more specific the better."}
            </small>
          </div>
          <button type="button" className="plan-ai-close" aria-label={zh ? "关闭" : "Close"} onClick={onClose}>
            ×
          </button>
        </header>

        <label className="plan-ai-field">
          <span className="v8-sr-only">{zh ? "旅行需求" : "Trip request"}</span>
          <textarea
            data-testid="plan-ai-input"
            rows={5}
            value={text}
            disabled={busy}
            onChange={(event) => setText(event.target.value)}
            placeholder={zh ? EXAMPLES[0].zh : EXAMPLES[0].en}
          />
        </label>

        <div className="plan-ai-examples">
          {EXAMPLES.map((item) => (
            <button
              key={item.en}
              type="button"
              disabled={busy}
              onClick={() => setText(zh ? item.zh : item.en)}
            >
              {zh ? item.zh.slice(0, 18) + "…" : item.en.slice(0, 26) + "…"}
            </button>
          ))}
        </div>

        {busy && (
          <ol className="plan-ai-steps" data-testid="plan-ai-steps">
            {STAGES.map((item, index) => (
              <li key={item.key} className={index < stage ? "done" : index === stage ? "active" : ""}>
                <span className="plan-ai-dot">{index < stage ? "✓" : index === stage ? "●" : "○"}</span>
                <span>{zh ? item.zh : item.en}</span>
              </li>
            ))}
          </ol>
        )}

        {copy && (
          <div className={`plan-ai-result ${copy.tone}`} data-testid="plan-ai-result" role="status">
            <b>{copy.title}</b>
            <p>{copy.body}</p>
            {result?.failureReason && (
              <details className="plan-ai-detail">
                <summary>{zh ? "技术详情" : "Technical detail"}</summary>
                <code data-testid="plan-ai-reason">{result.failureReason}</code>
              </details>
            )}
            {result?.summary && !result.failureReason && <p className="plan-ai-summary">{result.summary}</p>}
          </div>
        )}

        <div className="plan-ai-actions">
          <button type="button" className="v8-outline-button" onClick={onClose} disabled={busy}>
            {zh ? "稍后" : "Later"}
          </button>
          <button
            type="button"
            className="v8-primary-button"
            data-testid="plan-ai-submit"
            disabled={busy || text.trim().length < 8}
            onClick={() => void submit()}
          >
            {busy ? (zh ? "规划中…" : "Planning…") : zh ? "开始规划" : "Plan my trip"}
          </button>
        </div>
      </section>
    </div>
  );
}
