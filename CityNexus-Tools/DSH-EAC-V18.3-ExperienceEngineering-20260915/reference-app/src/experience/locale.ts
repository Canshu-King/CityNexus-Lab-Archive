import type { LocalizedCopy } from "../types";

export type Locale = "en" | "zh-CN";

/** Pure UI helper: resolve display copy without importing fixture data. */
export function pick(copy: LocalizedCopy, locale: Locale): string {
  return locale === "zh-CN" ? copy.zh : copy.en;
}

export function isZh(locale: string): locale is "zh-CN" {
  return locale === "zh-CN";
}
