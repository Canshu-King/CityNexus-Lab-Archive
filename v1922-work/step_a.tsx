import { useMemo, useState } from "react";
import { useLocale, useT } from "../../i18n/LocaleContext";

export type JourneyTrialDraft = {
  cityName: string;
  countryCode: string;
  timezone: string;
  startAt: string;
  endAt: string;
  arrivalLocation: string;
  departureLocation: string;
  budgetMajor: number;
  stayBudgetMajor: number;
  currency: string;
  partySize: number;
  rooms: number;
  /** Optional planning brief captured in step 2. */
  pace?: string;
  interests?: string[];
  specialRequirements?: string;
};

/** City -> (country, timezone, currency) so a normal user never has to type them. */
const CITY_FACTS: Record<string, { country: string; timezone: string; currency: string; label: string }> = {
  "厦门": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  xiamen: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "北京": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  beijing: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "上海": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  shanghai: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "天津": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  tianjin: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "福州": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  fuzhou: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "广州": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  guangzhou: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "深圳": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  shenzhen: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "成都": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  chengdu: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  "杭州": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "中国" },
  hangzhou: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", label: "China" },
  tokyo: { country: "JP", timezone: "Asia/Tokyo", currency: "JPY", label: "Japan" },
  "东京": { country: "JP", timezone: "Asia/Tokyo", currency: "JPY", label: "日本" },
  singapore: { country: "SG", timezone: "Asia/Singapore", currency: "SGD", label: "Singapore" },
  "新加坡": { country: "SG", timezone: "Asia/Singapore", currency: "SGD", label: "新加坡" },
};

export function inferCityFacts(cityName: string) {
  const key = cityName.trim().toLowerCase();
  if (!key) return null;
  return CITY_FACTS[key] ?? CITY_FACTS[cityName.trim()] ?? null;
}

export function currencyLabel(currency: string, locale: string) {
  const zh = locale.startsWith("zh");
  const table: Record<string, [string, string]> = {
    CNY: ["人民币", "Chinese yuan"],
    JPY: ["日元", "Japanese yen"],
    SGD: ["新加坡元", "Singapore dollar"],
    USD: ["美元", "US dollar"],
    EUR: ["欧元", "Euro"],
  };
  const hit = table[currency];
  return hit ? (zh ? hit[0] : hit[1]) : currency;
}

export function timezoneLabel(timezone: string, locale: string) {
  const zh = locale.startsWith("zh");
  const table: Record<string, [string, string]> = {
    "Asia/Shanghai": ["中国标准时间", "China Standard Time"],
    "Asia/Tokyo": ["日本标准时间", "Japan Standard Time"],
    "Asia/Singapore": ["新加坡时间", "Singapore Time"],
  };
  const hit = table[timezone];
  return hit ? (zh ? hit[0] : hit[1]) : timezone;
}

export function suggestedRoomCount(partySize: number): number {
  if (partySize <= 2) return 1;
  if (partySize <= 4) return 2;
  if (partySize <= 6) return 3;
  return Math.max(3, Math.ceil(partySize / 3));
}

function futureLocalAt(dayOffset: number, hour: number) {
  const value = new Date();
  value.setDate(value.getDate() + dayOffset);
  value.setHours(hour, 0, 0, 0);
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function localDateTimeInZoneToIso(value: string, timeZone: string) {
  const [datePart, timePart] = value.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  const localMs = Date.UTC(year, month - 1, day, hour, minute);
  let instantMs = localMs;
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    calendar: "iso8601",
    numberingSystem: "latn",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const parts = Object.fromEntries(
      formatter.formatToParts(new Date(instantMs)).map(({ type, value: part }) => [type, part]),
    );
    const displayedMs = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
      Number(parts.second),
    );
    instantMs += localMs - displayedMs;
  }
  return new Date(instantMs).toISOString();
}
