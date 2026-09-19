import { useState } from "react";
import { useLocale, useT } from "../i18n";
import { testIds } from "../testids";

export const DESKTOP_GROUPS = [
  {
    key: "TODAY",
    labelKey: "nav.today",
    items: [
      { route: "journey", labelKey: "nav.journey", icon: "◎" },
      { route: "live", labelKey: "nav.live", icon: "◈" },
      { route: "map", labelKey: "nav.map", icon: "⌖" },
    ],
  },
  {
    key: "PLAN",
    labelKey: "nav.plan",
    items: [
      { route: "studio", labelKey: "nav.studio", icon: "▤" },
      { route: "stay", labelKey: "nav.stay", icon: "⌂" },
      { route: "discover", labelKey: "nav.discover", icon: "✦" },
    ],
  },
  {
    key: "TRAVEL",
    labelKey: "nav.travel",
    items: [
      { route: "wallet", labelKey: "nav.wallet", icon: "▭" },
      { route: "copilot", labelKey: "nav.copilot", icon: "✧" },
    ],
  },
  {
    key: "SYSTEM",
    labelKey: "nav.system",
    items: [
      { route: "recovery", labelKey: "nav.recovery", icon: "⟲" },
      { route: "intelligence", labelKey: "nav.intelligence", icon: "◍" },
      { route: "twin", labelKey: "nav.twin", icon: "☺" },
    ],
  },
] as const;

export const MOBILE_ITEMS = [
  { route: "journey", labelKey: "nav.today", icon: "◎" },
  { route: "map", labelKey: "nav.map", icon: "⌖" },
  { route: "copilot", labelKey: "nav.copilot", icon: "✧" },
  { route: "wallet", labelKey: "nav.wallet", icon: "▭" },
  { route: "me", labelKey: "nav.me", icon: "☺" },
] as const;

export function DesktopNav({ active, onNavigate }: { active: string; onNavigate: (route: string) => void }) {
  const t = useT();
  const [systemOpen, setSystemOpen] = useState(false);
  return (
    <nav className="desktop-nav" data-testid={testIds.desktopNav} aria-label="Primary">
      {DESKTOP_GROUPS.map((group) => {
        const isSystem = group.key === "SYSTEM";
        const collapsed = isSystem && !systemOpen;
        return (
          <div className={`desktop-nav__group${isSystem ? " desktop-nav__group--system" : ""}`} key={group.key}>
            {isSystem ? (
              <button
                type="button"
                className="desktop-nav__group-toggle"
                aria-expanded={systemOpen}
                onClick={() => setSystemOpen((value) => !value)}
              >
                <span>{t(group.labelKey)}</span>
                <span aria-hidden="true">{systemOpen ? "▾" : "▸"}</span>
              </button>
            ) : (
              <span className="desktop-nav__group-label">{t(group.labelKey)}</span>
            )}
            {!collapsed &&
              group.items.map((item) => (
                <button
                  key={item.route}
                  type="button"
                  className={`desktop-nav__item${active === item.route ? " active" : ""}`}
                  data-testid={`nav-${item.route}`}
                  onClick={() => onNavigate(item.route)}
                  aria-current={active === item.route ? "page" : undefined}
                >
                  <span aria-hidden="true">{item.icon}</span>
                  {t(item.labelKey)}
                </button>
              ))}
          </div>
        );
      })}
    </nav>
  );
}

export function MobileNav({ active, onNavigate }: { active: string; onNavigate: (route: string) => void }) {
  const t = useT();
  return (
    <nav className="bottom-nav" data-testid={testIds.bottomNav} aria-label="Mobile primary">
      {MOBILE_ITEMS.map((item) => (
        <button
          key={item.route}
          type="button"
          className={`bottom-nav__item${active === item.route ? " active" : ""}`}
          data-testid={testIds.bottomNavItem}
          onClick={() => onNavigate(item.route)}
          aria-current={active === item.route ? "page" : undefined}
        >
          <span aria-hidden="true">{item.icon}</span>
          <small>{t(item.labelKey)}</small>
        </button>
      ))}
    </nav>
  );
}

export function LocaleToggle() {
  const { locale, setLocale } = useLocale();
  const t = useT();
  return (
    <button
      type="button"
      className="locale-toggle"
      data-testid={testIds.localeToggle}
      onClick={() => setLocale(locale === "en" ? "zh-CN" : "en")}
      aria-label={t("me.locale")}
    >
      {t("nav.language")}
    </button>
  );
}
