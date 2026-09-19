import { useLocale, useT } from "../i18n";
import type { JourneyActivity, LocalizedCopy } from "../types";
import { pick } from "../experience/locale";

export interface TodayTimelineItem {
  id: string;
  time: string;
  title: LocalizedCopy;
  environment: JourneyActivity["environment"];
  protected: boolean;
  status: JourneyActivity["status"];
}

export function TodayTimeline({ items }: { items: TodayTimelineItem[] }) {
  const t = useT();
  const { locale } = useLocale();
  return (
    <section className="today-timeline" data-testid="today-timeline">
      <header>
        <span className="kicker">{t("today.timeline")}</span>
        <h2>{t("today.timeline")}</h2>
      </header>
      <ol>
        {items.map((item) => (
          <li key={item.id} className={`${item.status}${item.protected ? " protected" : ""}`}>
            <time>{item.time}</time>
            <div>
              <b>{pick(item.title, locale)}</b>
              <small>
                {t(`environment.${item.environment}`)} · {t(`status.${item.status}`)}
              </small>
            </div>
            {item.protected && <em>{t("recovery.protectedList")}</em>}
          </li>
        ))}
      </ol>
    </section>
  );
}
