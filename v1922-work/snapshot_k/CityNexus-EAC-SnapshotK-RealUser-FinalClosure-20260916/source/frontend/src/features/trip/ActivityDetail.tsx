/**
 * Activity detail — reference screen 08.
 *
 * Shows only provider-backed facts.  Anything the backend did not supply is
 * omitted rather than invented: there is no fabricated rating, ticket price,
 * opening time or "why we recommend this" copy.
 */

import { useLocale } from "../../i18n/LocaleContext";

type ActivityLike = {
  id: string;
  title: string;
  type?: string | null;
  start_at: string;
  end_at: string;
  place_id?: string | null;
  protected?: boolean;
  travel_from_prev_min?: number | null;
  estimated_cost?: { amount_minor?: number; currency?: string } | null;
  metadata?: {
    latitude?: number | null;
    longitude?: number | null;
    crs?: string | null;
    category?: string | null;
    opening_hours?: { status?: string; raw?: string | null } | null;
    cost_evidence?: { status?: string; source?: string | null } | null;
    price_known?: boolean | null;
    semantic_key?: string | null;
  } | null;
};

function clock(iso: string, timeZone: string): string {
  try {
    return new Intl.DateTimeFormat("en-GB", {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).format(new Date(iso));
  } catch {
    return iso.slice(11, 16);
  }
}

function dayLabel(iso: string, locale: string, timeZone: string): string {
  try {
    return new Intl.DateTimeFormat(locale.startsWith("zh") ? "zh-CN" : "en-GB", {
      timeZone,
      weekday: "long",
      month: "short",
      day: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso.slice(0, 10);
  }
}

function minutesBetween(start: string, end: string): number | null {
  const a = Date.parse(start);
  const b = Date.parse(end);
  if (Number.isNaN(a) || Number.isNaN(b)) return null;
  return Math.max(0, Math.round((b - a) / 60000));
}

export function ActivityDetail({
  activity,
  timeZone,
  onBack,
  onShowOnMap,
  onAskCopilot,
  nearby,
  onOpenNearby,
}: {
  activity: ActivityLike;
  timeZone: string;
  onBack: () => void;
  onShowOnMap: () => void;
  onAskCopilot: () => void;
  nearby: ActivityLike[];
  onOpenNearby: (id: string) => void;
}) {
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");
  const meta = activity.metadata ?? {};
  const duration = minutesBetween(activity.start_at, activity.end_at);
  const hasCoords = meta.latitude != null && meta.longitude != null;
  const opening = meta.opening_hours ?? null;
  const openingKnown = opening?.status && opening.status !== "UNKNOWN";
  const cost = activity.estimated_cost;
  const costKnown = (cost?.amount_minor ?? 0) > 0;

  const durationText =
    duration == null
      ? null
      : duration >= 60
        ? zh
          ? `${Math.floor(duration / 60)} 小时${duration % 60 ? ` ${duration % 60} 分` : ""}`
          : `${Math.floor(duration / 60)}h${duration % 60 ? ` ${duration % 60}m` : ""}`
        : zh
          ? `${duration} 分钟`
          : `${duration} min`;

  return (
    <section className="v8-page activity-detail" data-testid="activity-detail">
      <button type="button" className="activity-back" data-testid="activity-back" onClick={onBack}>
        ← {zh ? "返回行程" : "Back to itinerary"}
      </button>

      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">
            {dayLabel(activity.start_at, locale, timeZone)} ·{" "}
            {clock(activity.start_at, timeZone)}–{clock(activity.end_at, timeZone)}
          </p>
          <h1 data-testid="activity-title">{activity.title}</h1>
          <p className="v8-lede">
            {activity.protected
              ? zh
                ? "这是已确认的安排，不会因为其他调整被移动。"
                : "This is a confirmed booking and will not be moved by other changes."
              : zh
                ? "这是你行程中的一个停靠点。"
                : "This is one stop on your itinerary."}
          </p>
        </div>
      </div>

      <dl className="trial-review activity-facts">
        {durationText && (
          <div>
            <dt>{zh ? "停留时长" : "Duration"}</dt>
            <dd data-testid="activity-duration">{durationText}</dd>
          </div>
        )}
        {activity.travel_from_prev_min != null && activity.travel_from_prev_min > 0 && (
          <div>
            <dt>{zh ? "从上一站出发" : "Travel from previous stop"}</dt>
            <dd>
              {zh
                ? `${activity.travel_from_prev_min} 分钟`
                : `${activity.travel_from_prev_min} min`}
            </dd>
          </div>
        )}
        <div>
          <dt>{zh ? "费用" : "Cost"}</dt>
          <dd data-testid="activity-cost">
            {costKnown
              ? `${cost?.currency ?? ""} ${Math.round((cost?.amount_minor ?? 0) / 100)}`
              : zh
                ? "暂无价格"
                : "Price unavailable"}
          </dd>
        </div>
        <div>
          <dt>{zh ? "营业时间" : "Opening hours"}</dt>
          <dd data-testid="activity-hours">
            {openingKnown
              ? opening?.raw || (zh ? "已提供" : "Provided")
              : zh
                ? "暂无数据"
                : "Not available"}
          </dd>
        </div>
        {meta.category && (
          <div>
            <dt>{zh ? "类型" : "Category"}</dt>
            <dd>{meta.category}</dd>
          </div>
        )}
        <div>
          <dt>{zh ? "位置" : "Location"}</dt>
          <dd data-testid="activity-location">
            {hasCoords
              ? `${Number(meta.latitude).toFixed(4)}, ${Number(meta.longitude).toFixed(4)}`
              : zh
                ? "暂无坐标"
                : "No coordinates"}
          </dd>
        </div>
      </dl>

      <div className="activity-actions">
        <button
          type="button"
          className="v8-primary-button"
          data-testid="activity-map"
          onClick={onShowOnMap}
          disabled={!hasCoords}
        >
          {zh ? "在地图上查看" : "Show on map"}
        </button>
        <button
          type="button"
          className="v8-outline-button"
          data-testid="activity-ask"
          onClick={onAskCopilot}
        >
          {zh ? "问问 Copilot" : "Ask Copilot"}
        </button>
      </div>

      {nearby.length > 0 && (
        <section className="activity-nearby" data-testid="activity-nearby">
          <h2>{zh ? "附近的建议" : "Nearby suggestions"}</h2>
          <p className="v8-muted">
            {zh
              ? "来自同一城市的真实地点数据，可按需加入行程。"
              : "Real places from the same city; add one if you want."}
          </p>
          <ul>
            {nearby.slice(0, 5).map((item) => (
              <li key={item.id}>
                <button type="button" onClick={() => onOpenNearby(item.id)}>
                  {item.title}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}
