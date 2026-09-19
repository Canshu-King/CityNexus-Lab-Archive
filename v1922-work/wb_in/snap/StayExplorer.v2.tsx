import { Icon } from "../../components/v8/Icon";
import { MapPanel } from "../../components/v8/MapPanel";
import type { V8Data } from "../../app/v8Types";
import { useT, useLocale } from "../../i18n/LocaleContext";
import { formatMinorMoney } from "../../lib/money";

export function StayExplorer({ data, selected, onSelect }: { data: V8Data; selected: V8Data["options"][number] | null; onSelect: (id: string) => void }) {
  const t = useT();
  const { locale } = useLocale();
  const zh = locale === "zh-CN";
  // A city label derived from the Journey, never a hard-coded demo city.
  const cityLabel = String(data.journey.city_code || "").split("-").pop() || "";
  if (!data.options.length) {
    return (
      <section className="v8-page" data-testid="v8-stay-explorer">
        <div className="v8-page-intro compact">
          <div>
            <p className="v8-kicker">{t("stay.kicker")}</p>
            <h1>{t("stay.title")}</h1>
          </div>
        </div>
        <div className="v8-empty-state" data-testid="stay-no-options">
          <b>{zh ? "还没有可用的住宿候选" : "No stay candidates yet"}</b>
          <p>
            {zh
              ? "我们还没有拿到真实住宿数据，所以不会给你看一张假的价格卡片。可以先选好行程，再回来搜索住宿。"
              : "We have no real accommodation data yet, so we will not show you an invented price card. Choose your plan first, then come back to search stays."}
          </p>
        </div>
      </section>
    );
  }
  return <section className="v8-page" data-testid="v8-stay-explorer">
    <div className="v8-page-intro compact"><div><p className="v8-kicker">{t("stay.kicker")}</p><h1>{t("stay.title")}</h1><p className="v8-lede">{t("stay.lede")}</p></div><span className="v8-evidence-label"><span className="status-dot" />{t("stay.capturedReplay")}</span></div>
    <div className="v8-stay-layout">
      <div className="v8-stay-list">{data.options.slice(0, 4).map((item) => <article data-testid="stay-offer-card" className={item.id === data.selected_option_id ? "v8-stay-card selected" : "v8-stay-card"} key={item.id} onClick={() => onSelect(item.id)} onKeyDown={(event) => { if (event.key === "Enter") onSelect(item.id); }} role="button" tabIndex={0}>
        <div className="v8-hotel-thumb large"><Icon name="bed" /><span>{cityLabel}</span></div>
        <div className="v8-stay-card-body"><div className="v8-stay-card-title"><div><span className="v8-rank">0{item.rank}</span><h3>{item.stay.property_name}</h3></div>{item.id === data.selected_option_id && <span className="v8-selected-label">{t("stay.selected")}</span>}</div><p>{item.stay.room_type} · {data.trip.party_size} travelers · {item.stay.refundable ? t("stay.freeCancel") : t("stay.nonRefundable")}</p><div className="v8-stay-price"><strong>{money(item.stay_total_minor, item.stay.currency, locale)}</strong><span>total · {money(item.stay.nightly_amount_minor, item.stay.currency, locale)}/{t("stay.nightly")}</span></div><div className="v8-stay-impact"><span>{t("stay.journeyImpact")}</span><b>{item.walking_min} min walk</b><b>{item.protected_margin_min} min slack</b><em>{item.leg_modes[0]}</em></div></div>
      </article>)}</div>
      <div className="v8-stay-detail"><MapPanel data={data} option={selected} /><div className="v8-detail-panel"><div><span>{t("stay.rateEvidence")}</span><b>{selected?.stay.property_name}</b></div><dl>
            <div>
              <dt>{t("stay.totalCurrency")}</dt>
              <dd>{priceLabel(selected?.stay.total_amount_minor, selected?.stay.currency, locale, zh)}</dd>
            </div>
            <div>
              <dt>{t("stay.checkInOut")}</dt>
              <dd>{date(selected?.stay.check_in_at, locale)} → {date(selected?.stay.check_out_at, locale)}</dd>
            </div>
            <div>
              <dt>{t("stay.cancellation")}</dt>
              <dd>{cancellationLabel(selected?.stay.cancellation_policy?.summary, zh)}</dd>
            </div>
            <div>
              <dt>{t("stay.provider")}</dt>
              <dd>{evidenceLabel(selected, zh)}</dd>
            </div>
          </dl></div></div>
    </div>
  </section>;
}

function money(minor: number | null | undefined, currency = "CNY", locale = "en") { return formatMinorMoney(minor, currency, locale === "zh-CN" ? "zh-CN" : "en-US"); }
function date(value?: string, locale = "en") { return value ? new Intl.DateTimeFormat(locale === "zh-CN" ? "zh-CN" : "en-GB", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(value)) : "—"; }

// A property with no real captured evidence must not be dressed up as an
// evidence card.  Absence is reported as absence, never as a 0% confidence
// reading that still looks like provider output.
function priceLabel(
  minor: number | null | undefined,
  currency: string | undefined,
  locale: string,
  zh: boolean,
): string {
  if (minor === null || minor === undefined) {
    return zh ? "价格未知（供应商未提供）" : "Price unknown (not provided)";
  }
  return `${money(minor, currency, locale)} · ${currency || "CNY"}`;
}

function cancellationLabel(summary: string | null | undefined, zh: boolean): string {
  const text = String(summary ?? "").trim();
  if (!text) return zh ? "退改政策未知" : "Cancellation terms unknown";
  return text;
}

function evidenceLabel(option: V8Data["options"][number] | null | undefined, zh: boolean): string {
  const confidence = option?.stay?.evidence?.confidence;
  if (typeof confidence !== "number" || confidence <= 0) {
    return zh ? "暂无供应商证据" : "No provider evidence";
  }
  return zh
    ? `供应商证据置信度 ${Math.round(confidence * 100)}%`
    : `Provider evidence confidence ${Math.round(confidence * 100)}%`;
}
