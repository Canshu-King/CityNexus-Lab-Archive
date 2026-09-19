export function formatV8Money(minor: number | null | undefined, currency = "CNY", locale = "en") {
  return minor == null ? "Provider price unavailable" : new Intl.NumberFormat(locale === "zh-CN" ? "zh-CN" : "en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(minor / 100);
}

export function formatV8Date(value?: string, locale = "en") {
  return value ? new Intl.DateTimeFormat(locale === "zh-CN" ? "zh-CN" : "en-GB", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(value)) : "—";
}
