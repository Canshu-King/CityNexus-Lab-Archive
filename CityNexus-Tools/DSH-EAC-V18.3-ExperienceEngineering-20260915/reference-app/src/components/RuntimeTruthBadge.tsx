import { useT } from "../i18n";
import { testIds } from "../testids";
import type { DataSource, RuntimeIdentity, RuntimeStatus, RuntimeTruth } from "../types";

export function runtimeTruthFor(
  execution: RuntimeIdentity,
  source: DataSource,
  status: RuntimeStatus = "ready",
): RuntimeTruth {
  return { semantic: "DeepSeek", execution, truth: "CityNexus", source, status };
}

export function sourceLabel(source: DataSource): string {
  if (source === "LIVE") return "LIVE";
  if (source === "OFFLINE") return "OFFLINE";
  return "RECORDED_FIXTURE";
}

export function executionLabel(execution: RuntimeIdentity, t: (key: string) => string): string {
  switch (execution) {
    case "DIRECT":
      return t("runtime.direct");
    case "HERMES_NATIVE_MCP":
      return t("runtime.hermes");
    case "FALLBACK":
      return t("runtime.fallback");
    case "UNAVAILABLE":
      return t("runtime.unavailable");
    default:
      return execution;
  }
}

export function RuntimeTruthBadge({
  truth,
  compact = false,
}: {
  truth: RuntimeTruth;
  compact?: boolean;
}) {
  const t = useT();
  const isFixture = truth.source === "RECORDED_FIXTURE";
  return (
    <div
      className={`runtime-truth${isFixture ? " is-fixture" : ""}${compact ? " is-compact" : ""}`}
      data-testid={testIds.runtimeTruth}
      data-source={truth.source}
      data-execution={truth.execution}
      data-runtime-status={truth.status}
      title={isFixture ? t("runtime.fixtureNote") : truth.execution === "DIRECT" ? t("runtime.directNote") : undefined}
    >
      <span className="runtime-truth__item">
        <small>{t("runtime.semantic")}</small>
        <b>{truth.semantic}</b>
      </span>
      <span className="runtime-truth__item">
        <small>{t("runtime.execution")}</small>
        <b data-testid={testIds.runtimeExecution}>{executionLabel(truth.execution, t)}</b>
      </span>
      <span className="runtime-truth__item">
        <small>{t("runtime.truth")}</small>
        <b>{truth.truth}</b>
      </span>
      {truth.status !== "ready" && (
        <span className="runtime-truth__status" data-testid="runtime-status-chip">
          {t(`runtime.status.${truth.status}`)}
        </span>
      )}
      <span
        className={`runtime-truth__source${isFixture ? " is-fixture" : ""}`}
        data-testid={testIds.runtimeSource}
      >
        {sourceLabel(truth.source)}
      </span>
    </div>
  );
}

export function RuntimeStatusBanner({
  status,
  onAction,
}: {
  status: RuntimeStatus;
  onAction?: () => void;
}) {
  const t = useT();
  if (status === "ready") return null;
  return (
    <section className="runtime-banner" data-testid="runtime-status-banner" data-status={status} role="status">
      <div>
        <b>{t(`runtime.status.${status}.title`)}</b>
        <p>{t(`runtime.status.${status}.detail`)}</p>
      </div>
      <button type="button" className="btn" onClick={onAction}>
        {t(`runtime.status.${status}.action`)}
      </button>
    </section>
  );
}
