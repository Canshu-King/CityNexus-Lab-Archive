import type { LocalizedCopy } from "../types";

/** UI copy only. Runtime facts come from the adapter, never from this file. */
export const PULSE_COPY = {
  nowNote: {
    en: "Recorded fixture · on the route, 12 min ahead of the next anchor.",
    zh: "录制快照 · 已在路线上，比下一个锚点提前 12 分钟。",
  } satisfies LocalizedCopy,
  nextNote: {
    en: "Protected commitment. Do not trade this buffer for a market stop.",
    zh: "受保护约定。不要用这段缓冲去换取市场停留。",
  } satisfies LocalizedCopy,
  riskTitle: { en: "Rain band arriving 11:20", zh: "11:20 降雨带到达" } satisfies LocalizedCopy,
  riskDetail: {
    en: "Recorded forecast fixture shows a 68% shower band during the outdoor market window.",
    zh: "录制的天气快照显示，户外市场时间窗内有 68% 的阵雨概率。",
  } satisfies LocalizedCopy,
  actionLabel: { en: "Review rain-safe recovery", zh: "查看防雨恢复方案" } satisfies LocalizedCopy,
  actionReason: {
    en: "One outdoor stop can move to an indoor window without touching the protected cruise.",
    zh: "可以把一个户外停留移到室内时间窗，同时不影响受保护的游船。",
  } satisfies LocalizedCopy,
  recoveryTrigger: {
    en: "Recorded rain band · outdoor market window exposure",
    zh: "录制降雨带 · 户外市场时间窗暴露",
  } satisfies LocalizedCopy,
} as const;
export const ACTIVITY_TITLES: Record<string, LocalizedCopy> = {
  "act-morning-walk": { en: "Five Great Avenues morning walk", zh: "五大道晨间步行" },
  "act-river-cruise": { en: "Haihe River cruise", zh: "海河游船" },
  "act-market-window": { en: "Ancient Culture Street market window", zh: "古文化街市场时间窗" },
  "act-lunch": { en: "Lunch reservation · Nanshi Food Street", zh: "午餐预订 · 南市食品街" },
  "act-museum": { en: "Tianjin Museum indoor window", zh: "天津博物馆室内时间窗" },
  "act-museum-early": { en: "Tianjin Museum indoor window", zh: "天津博物馆室内时间窗" },
  "act-hotel": { en: "Hotel check-in and luggage drop", zh: "酒店入住与行李寄存" },
  "act-departure": { en: "Departure transfer buffer", zh: "返程交通缓冲" },
};

export const WALLET_COPY = [
  { id: "res-cruise", type: { en: "River cruise", zh: "海河游船" }, confirmation: "CNX-RECORDED-CRUISE-0930", status: "protected" },
  { id: "res-lunch", type: { en: "Lunch reservation", zh: "午餐预订" }, confirmation: "CNX-RECORDED-LUNCH-1240", status: "confirmed" },
  { id: "res-hotel", type: { en: "Hotel check-in", zh: "酒店入住" }, confirmation: "CNX-RECORDED-HOTEL-1700", status: "protected" },
] satisfies Array<{ id: string; type: LocalizedCopy; confirmation: string; status: string }>;
