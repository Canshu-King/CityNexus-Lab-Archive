import { useMemo } from "react";
import { useLocale } from "../../i18n";
import {
  CATEGORY_META,
  pickLocalized,
  type Capabilities,
  type CapabilityCategory,
  type CapabilityLocale,
  type CapabilitySummaryItem,
  type LocalizedText,
} from "./capabilityTypes";
import { loadCapabilities, summarizeCapabilities } from "./capabilityStore";
import "./capability.css";

const SUMMARY_KICKER: LocalizedText = { en: "TRAVELER CAPABILITY", zh: "旅行者能力" };
const SUMMARY_TITLE: LocalizedText = { en: "Recognized capability summary", zh: "已识别的能力摘要" };
const EMPTY_LABEL: LocalizedText = { en: "None recognized", zh: "未识别" };

const SECTION_ORDER: readonly CapabilityCategory[] = [
  "HARD_ACCESSIBILITY_NEED",
  "PROTECTED_COMMITMENT",
  "USER_PREFERENCE",
];

function useCapabilityLocale(): CapabilityLocale {
  try {
    const context = useLocale();
    return context.locale === "zh-CN" ? "zh-CN" : "en";
  } catch {
    // Standalone reference rendering outside LocaleProvider defaults to English.
    return "en";
  }
}

export function CapabilitySummary({
  capabilities,
  value,
  compact = false,
  className,
}: {
  capabilities?: Capabilities | null;
  /** Alias for `capabilities`, useful for controlled hosts. */
  value?: Capabilities | null;
  compact?: boolean;
  className?: string;
}) {
  const locale = useCapabilityLocale();
  const provided = capabilities ?? value;
  const model = useMemo(
    () => summarizeCapabilities(provided ?? loadCapabilities()),
    [provided],
  );

  const itemsByCategory: Record<CapabilityCategory, CapabilitySummaryItem[]> = {
    HARD_ACCESSIBILITY_NEED: model.hardAccessibilityNeeds,
    PROTECTED_COMMITMENT: model.protectedCommitments,
    USER_PREFERENCE: model.preferences,
  };

  return (
    <section
      className={`cnx-capability cnx-capability--summary${
        compact ? " cnx-capability--compact" : ""
      }${className ? ` ${className}` : ""}`}
      data-testid="capability-summary"
      data-compact={compact ? "true" : "false"}
      aria-label={pickLocalized(SUMMARY_TITLE, locale)}
    >
      <header className="cnx-capability__header">
        <span className="cnx-capability__kicker">{pickLocalized(SUMMARY_KICKER, locale)}</span>
        <h2 className="cnx-capability__title">{pickLocalized(SUMMARY_TITLE, locale)}</h2>
        <p className="cnx-capability__lede">{pickLocalized(model.authorityNote, locale)}</p>
      </header>

      {SECTION_ORDER.map((category) => {
        const meta = CATEGORY_META[category];
        const items = itemsByCategory[category];
        return (
          <div
            key={category}
            className={`cnx-capability__summary-section cnx-capability__summary-section--${meta.tone}`}
            data-category={category}
          >
            <div className="cnx-capability__section-head">
              <span className={`cnx-capability__badge cnx-capability__badge--${meta.tone}`}>
                {pickLocalized(meta.badge, locale)}
              </span>
              <b className="cnx-capability__section-title">{pickLocalized(meta.label, locale)}</b>
            </div>
            {items.length === 0 ? (
              <p className="cnx-capability__empty">{pickLocalized(EMPTY_LABEL, locale)}</p>
            ) : (
              <ul
                className="cnx-capability__chips"
                aria-label={pickLocalized(meta.label, locale)}
              >
                {items.map((item) => (
                  <li
                    key={item.key}
                    className={`cnx-capability__chip cnx-capability__chip--${meta.tone}`}
                    data-capability-key={item.key}
                    data-category={item.category}
                  >
                    {item.category === "HARD_ACCESSIBILITY_NEED" && (
                      <span className="cnx-capability__badge cnx-capability__badge--hard">
                        {pickLocalized(CATEGORY_META.HARD_ACCESSIBILITY_NEED.badge, locale)}
                      </span>
                    )}
                    <span className="cnx-capability__chip-label">
                      {pickLocalized(item.definition.label, locale)}
                    </span>
                    <span className="cnx-capability__chip-value">
                      {pickLocalized(item.displayValue, locale)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}

      <p className="cnx-capability__note" data-testid="capability-summary-disclaimer">
        {pickLocalized(model.disclaimer, locale)}
      </p>
      <p className="cnx-capability__hint" data-testid="capability-summary-no-schema">
        {pickLocalized(model.noSchemaNote, locale)}
      </p>
    </section>
  );
}
