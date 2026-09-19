import { useId } from "react";
import type { ProviderEvidenceItem, ProviderEvidenceResult } from "../providerEvidence";
import { capabilityCopy } from "../copy";
import { EvidenceBadge } from "./EvidenceBadge";
import "../styles/capability-experience.css";

function uiState(state: ProviderEvidenceItem["state"]): "VERIFIED" | "UNVERIFIED" | "CONFLICT" | "NEEDS_LIVE_EVIDENCE" {
  switch (state) {
    case "ACCESSIBILITY_VERIFIED":
      return "VERIFIED";
    case "ACCESSIBILITY_CONFLICT":
      return "CONFLICT";
    case "ACCESSIBILITY_UNVERIFIED":
      return "UNVERIFIED";
    default:
      return "NEEDS_LIVE_EVIDENCE";
  }
}

function stateLabel(state: ProviderEvidenceItem["state"], locale: "zh-CN" | "en"): string {
  const zh = locale === "zh-CN";
  switch (state) {
    case "ACCESSIBILITY_VERIFIED":
      return zh ? "已核实" : "Verified";
    case "ACCESSIBILITY_CONFLICT":
      return zh ? "冲突" : "Conflict";
    case "ACCESSIBILITY_UNVERIFIED":
      return zh ? "未核实" : "Unverified";
    default:
      return zh ? "需要实时证据" : "Needs live evidence";
  }
}

export function ProviderEvidencePanel({
  result,
  locale = "zh-CN",
}: {
  result: ProviderEvidenceResult;
  locale?: "zh-CN" | "en";
}) {
  const copy = capabilityCopy(locale);
  const titleId = useId();
  return (
    <section className="cne-provider-evidence" aria-labelledby={titleId} data-testid="provider-evidence-panel">
      <header className="cne-surface__head">
        <div>
          <span className="cne-kicker">{result.mode}</span>
          <h2 id={titleId}>{locale === "zh-CN" ? "无障碍 Provider 证据" : "Accessibility provider evidence"}</h2>
          <p>
            {locale === "zh-CN"
              ? "只展示 provider/冻结数据中真实存在的事实；未知不等于可通行。"
              : "Only actual provider/frozen facts are shown. Unknown is not accessible."}
          </p>
        </div>
        <span className={`cne-source-pill ${result.mode === "LIVE_SHADOW" ? "is-live" : ""}`}>{result.label}</span>
      </header>
      {result.error ? <p className="cne-blocked-note" role="status">{result.error}</p> : null}
      {result.staleAt ? <p className="cne-help">{locale === "zh-CN" ? "最后已知时间" : "Last known at"}: {result.staleAt}</p> : null}
      {result.contractGap?.length ? (
        <ul className="cne-help">
          {result.contractGap.map((gap) => <li key={gap}>{gap}</li>)}
        </ul>
      ) : null}
      <div className="cne-provider-evidence__overall">
        <span>{locale === "zh-CN" ? "总体状态" : "Overall state"}</span>
        <EvidenceBadge state={uiState(result.overallState)} locale={locale} testId="provider-overall-state" />
        <small>{stateLabel(result.overallState, locale)}</small>
      </div>
      {result.items.length === 0 ? (
        <p className="cne-rule">{locale === "zh-CN" ? "没有 provider 证据；保持 NEEDS_LIVE_EVIDENCE。" : "No provider evidence; remains NEEDS_LIVE_EVIDENCE."}</p>
      ) : (
        <ul className="cne-provider-evidence__list">
          {result.items.map((item, index) => (
            <li key={`${item.source_key}-${item.code}-${index}`} data-testid={`provider-evidence-${item.code}`}>
              <div className="cne-provider-evidence__head">
                <div>
                  <b>{item.code.replaceAll("_", " ")}</b>
                  <small>{item.subject} · {item.provider} · {item.source_key}</small>
                </div>
                <EvidenceBadge state={uiState(item.state)} locale={locale} />
              </div>
              <p>{item.summary}</p>
              <dl className="cne-provider-evidence__raw">
                <div><dt>raw tag</dt><dd>{item.raw.key ?? "—"}</dd></div>
                <div><dt>raw value</dt><dd>{item.raw.value ?? "—"}</dd></div>
                <div><dt>captured</dt><dd>{item.captured_at}</dd></div>
                <div><dt>confidence</dt><dd>{item.confidence_type}</dd></div>
              </dl>
              <p className="cne-rule">{copy.evidence.unknownIsNotAccessible}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
