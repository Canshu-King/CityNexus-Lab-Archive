import { useT } from "../i18n";
import { testIds } from "../testids";
import type { DataSource, RuntimeIdentity, RuntimeTruth } from "../types";

export function runtimeTruthFor(execution: RuntimeIdentity, source: DataSource): RuntimeTruth {
  return { semantic: "DeepSeek", execution, truth: "CityNexus", source };
}

export function sourceLabel(source: DataSource): string {
  if (source === "LIVE") return "LIVE";
  if (source === "OFFLINE") return "OFFLINE";
  return "RECORDED_FIXTURE";
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
  const executionLabel =
    truth.execution === "DIRECT"
      ? t("runtime.direct")
      : truth.execution === "HERMES_NATIVE_MCP"
        ? t("runtime.hermes")
        : truth.execution;
  return (
    <div
      className={`runtime-truth${isFixture ? " is-fixture" : ""}${compact ? " is-compact" : ""}`}
      data-testid={testIds.runtimeTruth}
      data-source={truth.source}
      data-execution={truth.execution}
      title={isFixture ? t("runtime.fixtureNote") : truth.execution === "DIRECT" ? t("runtime.directNote") : undefined}
    >
      <span className="runtime-truth__item">
        <small>{t("runtime.semantic")}</small>
        <b>{truth.semantic}</b>
      </span>
      <span className="runtime-truth__item">
        <small>{t("runtime.execution")}</small>
        <b data-testid={testIds.runtimeExecution}>{executionLabel}</b>
      </span>
      <span className="runtime-truth__item">
        <small>{t("runtime.truth")}</small>
        <b>{truth.truth}</b>
      </span>
      <span
        className={`runtime-truth__source${isFixture ? " is-fixture" : ""}`}
        data-testid={testIds.runtimeSource}
      >
        {sourceLabel(truth.source)}
      </span>
    </div>
  );
}
