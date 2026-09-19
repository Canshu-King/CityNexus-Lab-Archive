import type {
  JourneyActivity,
  LocalizedCopy,
  PulseState,
  RecoveryProposal,
} from "../types";

export type LocalizedText = LocalizedCopy;

export function pick(text: LocalizedCopy, locale: "en" | "zh-CN"): string {
  return locale === "zh-CN" ? text.zh : text.en;
}

export type LocalizedActivity = Omit<
  JourneyActivity,
  "title" | "place" | "category"
> & {
  title: LocalizedText;
  place: LocalizedText;
  category: LocalizedText;
};

export const JOURNEY = {
  id: "journey-reference-tianjin-20260915",
  title: { en: "Tianjin Rain-Safe Weekend", zh: "天津防雨周末" } as LocalizedText,
  city: { en: "Tianjin", zh: "天津" } as LocalizedText,
  timezone: "Asia/Shanghai",
  traveler: { en: "Traveler", zh: "旅行者" } as LocalizedText,
  planVersion: "V18.2-reference-r1",
  generatedAt: "2026-09-15T08:12:00+08:00",
  dataSource: "RECORDED_FIXTURE" as const,
};

export const ACTIVITIES: LocalizedActivity[] = [
  {
    id: "act-morning-walk",
    title: { en: "Five Great Avenues morning walk", zh: "五大道晨间步行" },
    start_at: "2026-09-15T08:30:00+08:00",
    end_at: "2026-09-15T09:10:00+08:00",
    place: { en: "Wudadao historic district", zh: "五大道历史街区" },
    category: { en: "walk", zh: "步行" },
    environment: "outdoor",
    walking_min: 22,
    protected: false,
    status: "current",
  },
  {
    id: "act-river-cruise",
    title: { en: "Haihe River cruise", zh: "海河游船" },
    start_at: "2026-09-15T09:30:00+08:00",
    end_at: "2026-09-15T10:40:00+08:00",
    place: { en: "Haihe dock · Jinwan Plaza", zh: "海河码头 · 津湾广场" },
    category: { en: "protected C4", zh: "受保护 C4" },
    environment: "outdoor",
    walking_min: 6,
    protected: true,
    status: "upcoming",
  },
  {
    id: "act-market-window",
    title: { en: "Ancient Culture Street market window", zh: "古文化街市场时间窗" },
    start_at: "2026-09-15T11:10:00+08:00",
    end_at: "2026-09-15T12:20:00+08:00",
    place: { en: "Ancient Culture Street", zh: "古文化街" },
    category: { en: "market", zh: "市场" },
    environment: "outdoor",
    walking_min: 22,
    protected: false,
    status: "upcoming",
  },
  {
    id: "act-lunch",
    title: { en: "Lunch reservation · Nanshi Food Street", zh: "午餐预订 · 南市食品街" },
    start_at: "2026-09-15T12:40:00+08:00",
    end_at: "2026-09-15T13:40:00+08:00",
    place: { en: "Nanshi Food Street", zh: "南市食品街" },
    category: { en: "reservation", zh: "预订" },
    environment: "indoor",
    walking_min: 8,
    protected: false,
    status: "upcoming",
  },
  {
    id: "act-museum",
    title: { en: "Tianjin Museum indoor window", zh: "天津博物馆室内时间窗" },
    start_at: "2026-09-15T14:20:00+08:00",
    end_at: "2026-09-15T16:00:00+08:00",
    place: { en: "Tianjin Museum", zh: "天津博物馆" },
    category: { en: "indoor", zh: "室内" },
    environment: "indoor",
    walking_min: 8,
    protected: false,
    status: "upcoming",
  },
  {
    id: "act-hotel",
    title: { en: "Hotel check-in and luggage drop", zh: "酒店入住与行李寄存" },
    start_at: "2026-09-15T17:00:00+08:00",
    end_at: "2026-09-15T17:20:00+08:00",
    place: { en: "Riverside hotel", zh: "河畔酒店" },
    category: { en: "protected", zh: "受保护" },
    environment: "indoor",
    walking_min: 4,
    protected: true,
    status: "upcoming",
  },
  {
    id: "act-departure",
    title: { en: "Departure transfer buffer", zh: "返程交通缓冲" },
    start_at: "2026-09-15T18:30:00+08:00",
    end_at: "2026-09-15T19:45:00+08:00",
    place: { en: "Tianjin Railway Station", zh: "天津站" },
    category: { en: "protected", zh: "受保护" },
    environment: "transit",
    walking_min: 10,
    protected: true,
    status: "upcoming",
  },
];

function toActivity(activity: LocalizedActivity): JourneyActivity {
  return {
    ...activity,
    title: activity.title.en,
    place: activity.place.en,
    category: activity.category.en,
  };
}

export const PULSE: PulseState = {
  now: {
    activity: toActivity(ACTIVITIES[0]),
    time: "08:41",
    eta: "on route · 12 min ahead",
    note: "Recorded fixture · on the route, 12 min ahead of the next anchor.",
  },
  next: {
    activity: toActivity(ACTIVITIES[1]),
    time: "09:30",
    buffer_min: 37,
    note: "Protected commitment. Do not trade this buffer for a market stop.",
  },
  risk: {
    level: "watch",
    title: "Rain band arriving 11:20",
    detail: "Recorded forecast fixture shows a 68% shower band during the outdoor market window.",
    source: "RECORDED_FIXTURE",
  },
  primaryAction: {
    label: "Review rain-safe recovery",
    route: "recovery",
    reason: "One outdoor stop can move to an indoor window without touching the protected cruise.",
  },
};

export const PULSE_I18N = {
  nowNote: {
    en: "Recorded fixture · on the route, 12 min ahead of the next anchor.",
    zh: "录制快照 · 已在路线上，比下一个锚点提前 12 分钟。",
  } as LocalizedText,
  nextNote: {
    en: "Protected commitment. Do not trade this buffer for a market stop.",
    zh: "受保护约定。不要用这段缓冲去换取市场停留。",
  } as LocalizedText,
  riskTitle: { en: "Rain band arriving 11:20", zh: "11:20 降雨带到达" } as LocalizedText,
  riskDetail: {
    en: "Recorded forecast fixture shows a 68% shower band during the outdoor market window.",
    zh: "录制的天气快照显示，户外市场时间窗内有 68% 的阵雨概率。",
  } as LocalizedText,
  actionLabel: { en: "Review rain-safe recovery", zh: "查看防雨恢复方案" } as LocalizedText,
  actionReason: {
    en: "One outdoor stop can move to an indoor window without touching the protected cruise.",
    zh: "可以把一个户外停留移到室内时间窗，同时不影响受保护的游船。",
  } as LocalizedText,
};

export const RECOVERY: RecoveryProposal = {
  proposal_id: "proposal-reference-rain-002",
  trigger: {
    en: "Recorded rain band · outdoor market window exposure",
    zh: "录制降雨带 · 户外市场时间窗暴露",
  },
  severity: "minor",
  source: "RECORDED_FIXTURE",
  before: [toActivity(ACTIVITIES[2])],
  after: [
    {
      ...toActivity(ACTIVITIES[4]),
      id: "act-museum-early",
      title: "Tianjin Museum indoor window",
      start_at: "2026-09-15T11:10:00+08:00",
      end_at: "2026-09-15T12:20:00+08:00",
      place: "Tianjin Museum",
      category: "indoor",
      environment: "indoor",
      walking_min: 8,
      status: "candidate",
    },
  ],
  removed: {
    en: "Ancient Culture Street market window",
    zh: "古文化街市场时间窗",
  },
  added: {
    en: "Tianjin Museum indoor window (moved earlier)",
    zh: "天津博物馆室内时间窗（提前）",
  },
  why: [
    { en: "Heavy rain forecast during the outdoor window", zh: "户外时间窗预计有强降雨" },
    { en: "Reduced walking from 22 min to 8 min", zh: "步行从 22 分钟减少到 8 分钟" },
    { en: "Protected 17:30 hotel and departure buffer untouched", zh: "受保护的 17:30 酒店与返程缓冲不变" },
  ],
  protected_commitments: [
    { en: "Haihe River cruise · C4", zh: "海河游船 · C4" },
    { en: "Riverside hotel check-in", zh: "河畔酒店入住" },
    { en: "Departure transfer buffer", zh: "返程交通缓冲" },
  ],
  time_delta_min: 0,
  cost_delta_minor: 0,
  travel_delta_min: 6,
  walking_delta_min: -14,
  protected_commitments_preserved: true,
  evidence_state: "verified",
  verified_evidence: {
    route_provenance: "recorded-fixture://mobility/route-rain-002",
    source_provider: "recorded_provider_fixture",
    snapshot_id: "snapshot-REPLAY-20260915-002",
  },
  explanation: {
    en: "Only the outdoor market window is swapped for an indoor museum window. The protected Haihe cruise, hotel, and departure buffer are unchanged.",
    zh: "只把户外市场时间窗换成室内博物馆时间窗。受保护的海河游船、酒店和返程缓冲保持不变。",
  },
};

export const WALLET_ITEMS = [
  {
    id: "res-cruise",
    type: { en: "River cruise", zh: "海河游船" } as LocalizedText,
    confirmation: "CNX-RECORDED-CRUISE-0930",
    status: "protected",
  },
  {
    id: "res-lunch",
    type: { en: "Lunch reservation", zh: "午餐预订" } as LocalizedText,
    confirmation: "CNX-RECORDED-LUNCH-1240",
    status: "confirmed",
  },
  {
    id: "res-hotel",
    type: { en: "Hotel check-in", zh: "酒店入住" } as LocalizedText,
    confirmation: "CNX-RECORDED-HOTEL-1700",
    status: "protected",
  },
];

export type TodayTimelineItem = {
  id: string;
  time: string;
  title: LocalizedText;
  environment: JourneyActivity["environment"];
  protected: boolean;
  status: JourneyActivity["status"];
};

export const TODAY_TIMELINE: TodayTimelineItem[] = ACTIVITIES.map((activity) => ({
  id: activity.id,
  time: activity.start_at.slice(11, 16),
  title: activity.title,
  environment: activity.environment,
  protected: activity.protected,
  status: activity.status,
}));
