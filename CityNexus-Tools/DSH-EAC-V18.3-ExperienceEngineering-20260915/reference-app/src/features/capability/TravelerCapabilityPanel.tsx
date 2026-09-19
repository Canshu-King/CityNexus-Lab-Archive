import {
  useCallback,
  useEffect,
  useState,
  type ChangeEvent,
  type ReactNode,
} from "react";
import { useLocale } from "../../i18n";
import {
  CAPABILITY_DEFINITIONS,
  CAPABILITY_KEYS,
  CAPABILITY_NO_SCHEMA_NOTE,
  CATEGORY_META,
  CATEGORY_ORDER,
  pickLocalized,
  type Capabilities,
  type CapabilityKey,
  type CapabilityLocale,
  type CapabilityValue,
  type LocalizedText,
} from "./capabilityTypes";
import { loadCapabilities, saveCapabilities } from "./capabilityStore";
import { CapabilitySummary } from "./CapabilitySummary";

const PANEL_KICKER: LocalizedText = { en: "JOURNEY SETUP", zh: "行程设置" };
const PANEL_TITLE: LocalizedText = { en: "Traveler capabilities", zh: "旅行者能力" };
const PANEL_LEDE: LocalizedText = {
  en: "Recognize what must be respected before options are ranked. Hard needs and protected commitments are kept out of automatic trade-offs.",
  zh: "在排序方案前，先识别必须被尊重的条件。硬性需求与受保护承诺不会进入自动取舍。",
};
const LEGEND_LABEL: LocalizedText = { en: "Category legend", zh: "类别图例" };
const MINUTES_LABEL: LocalizedText = { en: "min", zh: "分钟" };
const SENSITIVITY_LABEL: LocalizedText = { en: "Sensitivity level", zh: "敏感等级" };
const UNSPECIFIED_LABEL: LocalizedText = { en: "Not specified", zh: "未指定" };

function useCapabilityLocale(): CapabilityLocale {
  try {
    const context = useLocale();
    return context.locale === "zh-CN" ? "zh-CN" : "en";
  } catch {
    // Standalone reference rendering outside LocaleProvider defaults to English.
    return "en";
  }
}

export function TravelerCapabilityPanel({
  mode,
  value,
  onChange,
  className,
}: {
  mode: "setup" | "summary";
  value?: Capabilities | null;
  onChange?: (next: Capabilities) => void;
  className?: string;
}) {
  const locale = useCapabilityLocale();
  const [internal, setInternal] = useState<Capabilities>(() => value ?? loadCapabilities());

  useEffect(() => {
    if (value) setInternal(value);
  }, [value]);

  const capabilities: Capabilities = value ?? internal;

  const update = useCallback(
    (key: CapabilityKey, nextValue: CapabilityValue) => {
      const next: Capabilities = { ...capabilities, [key]: nextValue };
      if (!value) setInternal(next);
      saveCapabilities(next);
      onChange?.(next);
    },
    [capabilities, onChange, value],
  );

  if (mode === "summary") {
    return <CapabilitySummary capabilities={capabilities} compact className={className} />;
  }

  const controlId = (key: CapabilityKey) => `cnx-capability-${key}`;
  const descriptionId = (key: CapabilityKey) => `cnx-capability-${key}-description`;
  const thresholdId = (key: CapabilityKey) => `cnx-capability-${key}-threshold`;
  const describedBy = (key: CapabilityKey) =>
    CAPABILITY_DEFINITIONS[key].hardThresholdNote
      ? `${descriptionId(key)} ${thresholdId(key)}`
      : descriptionId(key);

  const renderControl = (key: CapabilityKey): ReactNode => {
    const definition = CAPABILITY_DEFINITIONS[key];
    const controlValue = capabilities[key];

    if (definition.control === "toggle" && controlValue.kind === "toggle") {
      return (
        <label className="cnx-capability__switch" htmlFor={controlId(key)}>
          <input
            id={controlId(key)}
            type="checkbox"
            checked={controlValue.enabled}
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              update(key, { kind: "toggle", enabled: event.target.checked })
            }
            aria-describedby={describedBy(key)}
            data-testid={`capability-input-${key}`}
          />
          <span className="cnx-capability__switch-track" aria-hidden="true" />
        </label>
      );
    }

    if (definition.control === "number" && controlValue.kind === "number") {
      return (
        <div className="cnx-capability__control-group">
          <input
            id={controlId(key)}
            type="number"
            min={definition.min ?? 5}
            max={definition.max ?? 240}
            step={definition.step ?? 5}
            value={controlValue.value}
            onChange={(event: ChangeEvent<HTMLInputElement>) => {
              const parsed = Number(event.target.value);
              const min = definition.min ?? 5;
              const max = definition.max ?? 240;
              const nextValue = Number.isFinite(parsed)
                ? Math.min(max, Math.max(min, Math.round(parsed)))
                : controlValue.value;
              update(key, {
                kind: "number",
                enabled: true,
                value: nextValue,
                unit: "minutes",
              });
            }}
            aria-describedby={describedBy(key)}
            data-testid={`capability-input-${key}`}
          />
          <span className="cnx-capability__unit">{pickLocalized(MINUTES_LABEL, locale)}</span>
        </div>
      );
    }

    if (definition.control === "select" && controlValue.kind === "choice") {
      const options = definition.options ?? [];
      return (
        <select
          id={controlId(key)}
          value={controlValue.value}
          onChange={(event: ChangeEvent<HTMLSelectElement>) => {
            const option = options.find((candidate) => candidate.value === event.target.value);
            if (option) update(key, { kind: "choice", value: option.value });
          }}
          aria-describedby={describedBy(key)}
          data-testid={`capability-input-${key}`}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {pickLocalized(option.label, locale)}
            </option>
          ))}
        </select>
      );
    }

    if (definition.control === "sensitivity" && controlValue.kind === "sensitivity") {
      const options = definition.sensitivityOptions ?? [];
      return (
        <div className="cnx-capability__control-group">
          <label className="cnx-capability__switch" htmlFor={controlId(key)}>
            <input
              id={controlId(key)}
              type="checkbox"
              checked={controlValue.enabled}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                update(key, {
                  kind: "sensitivity",
                  enabled: event.target.checked,
                  level: controlValue.level,
                })
              }
              aria-describedby={describedBy(key)}
              data-testid={`capability-input-${key}`}
            />
            <span className="cnx-capability__switch-track" aria-hidden="true" />
          </label>
          <select
            aria-label={pickLocalized(SENSITIVITY_LABEL, locale)}
            value={controlValue.level ?? ""}
            disabled={!controlValue.enabled}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              const selected = event.target.value;
              if (selected === "") {
                update(key, {
                  kind: "sensitivity",
                  enabled: true,
                  level: null,
                });
                return;
              }
              const option = options.find((candidate) => candidate.value === selected);
              if (option) {
                update(key, {
                  kind: "sensitivity",
                  enabled: true,
                  level: option.value,
                });
              }
            }}
            data-testid={`capability-level-${key}`}
          >
            <option value="">{pickLocalized(UNSPECIFIED_LABEL, locale)}</option>
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {pickLocalized(option.label, locale)}
              </option>
            ))}
          </select>
        </div>
      );
    }

    return null;
  };

  const renderRow = (key: CapabilityKey): ReactNode => {
    const definition = CAPABILITY_DEFINITIONS[key];
    return (
      <div
        key={key}
        className="cnx-capability__row"
        data-testid={`capability-row-${key}`}
        data-category={definition.category}
      >
        <div className="cnx-capability__row-text">
          <label
            className="cnx-capability__label"
            htmlFor={controlId(key)}
            title={pickLocalized(definition.categoryRationale, locale)}
          >
            {pickLocalized(definition.label, locale)}
          </label>
          <p className="cnx-capability__hint" id={descriptionId(key)}>
            {pickLocalized(definition.description, locale)}
          </p>
          {definition.hardThresholdNote && (
            <p
              className="cnx-capability__hint cnx-capability__hint--threshold"
              id={thresholdId(key)}
            >
              {pickLocalized(definition.hardThresholdNote, locale)}
            </p>
          )}
        </div>
        <div className="cnx-capability__control">{renderControl(key)}</div>
      </div>
    );
  };

  return (
    <section
      className={`cnx-capability cnx-capability--setup${className ? ` ${className}` : ""}`}
      data-testid="capability-panel"
      data-mode="setup"
      aria-label={pickLocalized(PANEL_TITLE, locale)}
    >
      <header className="cnx-capability__header">
        <span className="cnx-capability__kicker">{pickLocalized(PANEL_KICKER, locale)}</span>
        <h2 className="cnx-capability__title">{pickLocalized(PANEL_TITLE, locale)}</h2>
        <p className="cnx-capability__lede">{pickLocalized(PANEL_LEDE, locale)}</p>
      </header>

      <div
        className="cnx-capability__legend"
        role="group"
        aria-label={pickLocalized(LEGEND_LABEL, locale)}
      >
        {CATEGORY_ORDER.map((category) => {
          const meta = CATEGORY_META[category];
          return (
            <div
              key={category}
              className={`cnx-capability__legend-item cnx-capability__legend-item--${meta.tone}`}
            >
              <span className={`cnx-capability__badge cnx-capability__badge--${meta.tone}`}>
                {pickLocalized(meta.badge, locale)}
              </span>
              <span className="cnx-capability__legend-desc">
                {pickLocalized(meta.description, locale)}
              </span>
            </div>
          );
        })}
      </div>

      {CATEGORY_ORDER.map((category) => {
        const meta = CATEGORY_META[category];
        const categoryKeys = CAPABILITY_KEYS.filter(
          (key) => CAPABILITY_DEFINITIONS[key].category === category,
        );
        return (
          <fieldset
            key={category}
            className={`cnx-capability__group cnx-capability__group--${meta.tone}`}
          >
            <legend className="cnx-capability__group-legend">
              <span className={`cnx-capability__badge cnx-capability__badge--${meta.tone}`}>
                {pickLocalized(meta.badge, locale)}
              </span>
              <span>{pickLocalized(meta.label, locale)}</span>
            </legend>
            <p className="cnx-capability__group-desc">{pickLocalized(meta.description, locale)}</p>
            <div className="cnx-capability__rows">
              {categoryKeys.map((key) => renderRow(key))}
            </div>
          </fieldset>
        );
      })}

      <p className="cnx-capability__note">{pickLocalized(CAPABILITY_NO_SCHEMA_NOTE, locale)}</p>
    </section>
  );
}
