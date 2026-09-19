import { useLocale, useT } from "../i18n";
import { TODAY_TIMELINE, pick } from "../data/journey";

export function TodayTimeline() {
  const t = useT();
  const { locale } = useLocale();
  return (
    <section className="today-timeline" data-testid="today-timeline">
      <header>
        <span className="kicker">{t("today.timeline")}</span>
        <h2>{t("today.timeline")}</h2>
      </header>
      <ol>
        {TODAY_TIMELINE.map((item) => (
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
