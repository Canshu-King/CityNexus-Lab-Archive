import { Icon } from "../../components/v8/Icon";
import type { V8Data } from "../../app/v8Types";
import { useT } from "../../i18n/LocaleContext";

type Policy = { mode: "ADVISORY" | "ASSISTED" | "AUTONOMOUS"; version: number } | null;

export function ControlTowerPanel({ policy, onActivate }: { policy: Policy; onActivate: () => Promise<void> }) {
  const t = useT();
  return <section className="v8-page"><div className="v8-page-intro compact"><div><p className="v8-kicker">{t("intel.kicker")}</p><h1>{t("intel.title")}</h1><p className="v8-lede">{t("intel.lede")}</p></div><button className="v8-primary" onClick={() => void onActivate()}>{policy?.mode === "AUTONOMOUS" ? t("intel.autonomyActive") : t("intel.enableRecovery")}</button></div><div className="v8-intelligence-grid"><article className="v8-intel-hero"><span className="v8-status-pill violet"><Icon name="spark" />{t("intel.guardianReady")}</span><h2>{t("intel.recoveryTitle")}</h2><p>{t("intel.recoverySub")}</p><div className="v8-chain"><span>{t("intel.deepseek")}</span><b>→</b><span>{t("intel.hermes")}</span><b>→</b><span>{t("intel.gateway")}</span><b>→</b><span>{t("intel.cpsat")}</span><b>→</b><span>{t("intel.domain")}</span></div></article><div className="v8-intel-facts"><div><span>{t("intel.policy")}</span><b>{policy?.mode ?? t("intel.advisory")}</b><small>{t("intel.versionPrefix")} {policy?.version ?? "—"} {t("intel.versionSuffix")}</small></div><div><span>{t("intel.postActionGate")}</span><b>{t("intel.feasible")}</b><small>{t("intel.gateSub")}</small></div><div><span>{t("intel.commitment")}</span><b>{t("intel.protected")}</b><small>{t("intel.commitmentSub")}</small></div></div></div></section>;
}
