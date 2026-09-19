# Traveler Capability UX — CityNexus V18.3

**Status:** isolated reference feature module · no backend schema change
**Scope:** `reference-app/src/features/capability/` only
**中文摘要：** 本模块定义旅行者能力的体验层类型、localStorage 存储、设置面板与 Copilot 摘要，不修改后端或主工作树。

---

## 1. Purpose and scope

The traveler capability module gives the experience layer a small, explicit
vocabulary for the constraints a traveler recognizes. It exists so journey
setup and Copilot can answer three questions consistently:

1. What did the traveler tell us? (recognized reference)
2. How strongly must CityNexus respect it? (three categories)
3. What may never be silently traded away? (hard needs and protected commitments)

The module is deliberately experience-layer only. It does not add fields to
`src/types.ts`, does not write to PlanVersion, and does not change any backend
schema. It can be merged into a host UI without requiring a migration.

### Design rationale

- **Separate recognition from authority.** The panel records what the traveler
  recognizes. CityNexus remains the authority for what the plan can actually do.
- **Make trade-off policy visible.** The three-category model lets the UI say
  *why* something is not part of an automatic trade-off.
- **Keep hard needs small and legible.** `wheelchair_step_free` and
  `avoid_stairs` are mandatory hard needs. `stroller` is added as a third hard
  need because a stroller changes which routes are physically usable.
- **Promote delicate logistics.** `elderly_rest`, `infant_nap`, and
  `toilet_rest_stop` are protected commitments: they need explicit approval to
  change. `luggage` remains a logistics preference.
- **Keep preferences soft.** `max_walking`, `pace`, and `quiet_sensory` shape
  ranking and timing, but they do not override hard needs or protected
  commitments.

---

## 2. The three-category model

Every capability has exactly one category. The category is stored in
`CAPABILITY_DEFINITIONS` in `capabilityTypes.ts`, not persisted separately, so
the UI and summary can never disagree about it.

| Category | Meaning | Trade-off policy | UI treatment |
| --- | --- | --- | --- |
| `HARD_ACCESSIBILITY_NEED` | Physically non-negotiable access requirement | Never placed into automatic trade-offs | Red badge, prominent hard label |
| `PROTECTED_COMMITMENT` | A declared commitment that must not be silently compressed | Can change only through explicit approval | Amber badge, separate group |
| `USER_PREFERENCE` | A soft signal used to rank alternatives | May change in a preview or trade-off | Quiet chip, preference group |

**中文说明：** `HARD_ACCESSIBILITY_NEED` 不参与自动取舍；`PROTECTED_COMMITMENT`
需要明确批准；`USER_PREFERENCE` 可用于排序与试算。

### Capability matrix

| Key | Category | Control | Default | Rationale / notes |
| --- | --- | --- | --- | --- |
| `wheelchair_step_free` | `HARD_ACCESSIBILITY_NEED` | Toggle | Off | Mandatory hard need. Every leg must be step-free. |
| `avoid_stairs` | `HARD_ACCESSIBILITY_NEED` | Toggle | Off | Mandatory hard need. Stairs are a route blocker. |
| `max_walking` | `USER_PREFERENCE` | Number, unit `minutes` | Off, 30 min | Numeric preference with a visible hard threshold note. If a candidate exceeds the number, surface the conflict instead of silently trading it away. |
| `elderly_rest` | `PROTECTED_COMMITMENT` | Toggle | Off | Chosen category. Declared rest windows are protected from automatic compression. |
| `infant_nap` | `PROTECTED_COMMITMENT` | Toggle | Off | Chosen category. The nap window anchors the day and needs explicit approval to move. |
| `stroller` | `HARD_ACCESSIBILITY_NEED` | Toggle | Off | Chosen as a third hard need beyond the mandatory two: a stroller changes which routes are physically usable. |
| `toilet_rest_stop` | `PROTECTED_COMMITMENT` | Toggle | Off | Logistics need promoted to protected commitment: a missed stop affects health, dignity, and downstream timing. |
| `luggage` | `USER_PREFERENCE` | Toggle | Off | Logistics preference: shapes vehicle, storage, and transfer choices, but may be traded in a preview. |
| `pace` | `USER_PREFERENCE` | Select | `balanced` | Allowed values: `relaxed`, `balanced`, `fast`. |
| `quiet_sensory` | `USER_PREFERENCE` | Toggle + optional level | Off, level `null` | Optional sensitivity level: `low`, `medium`, `high`. |

---

## 3. Setup flow (`mode="setup"`)

`TravelerCapabilityPanel` with `mode="setup"` is the journey-setup surface.

1. **Recognize first.** The panel asks what the traveler needs before any
   alternatives are ranked.
2. **Group by category.** Three `<fieldset>` groups render in this order:
   hard accessibility needs, protected commitments, then preferences. Each
   group has a `<legend>`, a category badge, and a one-line explanation.
3. **Use the right control per capability.**
   - Toggles for binary needs and commitments.
   - A number input for `max_walking`, always labelled `minutes`.
   - A select for `pace`.
   - A toggle plus an optional sensitivity-level select for `quiet_sensory`.
4. **Show the hard threshold note.** `max_walking` displays its
   `hardThresholdNote` directly under the control. The note is never hidden in
   a tooltip only.
5. **Provide a legend.** The three-category legend is visible above the groups,
   so the policy is understandable without opening documentation.
6. **Persist locally.** Every change calls `saveCapabilities()` against
   `citynexus.v18.3.capabilities`. `onChange` also receives the next state for
   controlled hosts.
7. **State the boundary.** The footer says the panel is experience-layer only
   and does not change backend schema or PlanVersion.

### Suggested host copy

- Kicker: `JOURNEY SETUP` / `行程设置`
- Title: `Traveler capabilities` / `旅行者能力`
- Lede: recognize what must be respected before options are ranked.

---

## 4. Copilot summary flow (`mode="summary"`)

`TravelerCapabilityPanel` with `mode="summary"` renders the compact
`CapabilitySummary`.

- **Recognized constraints only.** Unrecognized toggles are omitted; the
  summary is a reference, not a full inventory.
- **Chips grouped by category.** Hard needs, protected commitments, and
  preferences each get their own section. Protected commitments are rendered
  separately from preferences.
- **Hard badge.** Hard items carry a distinct `HARD ACCESSIBILITY NEED` badge
  in addition to the group badge, so they are recognizable even in a compact
  Copilot column.
- **Protected badge.** Protected commitments carry a `PROTECTED COMMITMENT`
  badge and a separate group heading.
- **Authority line.** The summary always shows:
  *"Recognized reference, not a backend authority."* / *"已识别参考，而非后端权威。"*
- **Trade-off sentence.** The summary always shows this exact sentence:

> CityNexus keeps hard needs and protected commitments out of automatic
> trade-offs, but this reference UI does not mutate backend schema.

> 中文：CityNexus 不会将硬性需求与受保护承诺放入自动取舍，但此参考界面不会修改
> 后端 schema。

- **No schema note.** A second line repeats that values are stored in
  localStorage and no PlanVersion or backend schema changes.

### Recognized vs. persisted

`summarizeCapabilities()` normalizes any partial or corrupt input against
`createDefaultCapabilities()`. A capability is "recognized" when:

| Control | Recognized when |
| --- | --- |
| Toggle | `enabled === true` |
| Number | `enabled === true` |
| Select (`pace`) | Always; the value is always a valid pace |
| Sensitivity | `enabled === true`; level may be `null` |

---

## 5. Accessibility implications

The capability module is intentionally small, but it carries several
accessibility contracts that the host must preserve.

- **44 px touch targets.** Toggles, number inputs, selects, and select levels
  are at least 44 px tall. Informational chips are allowed to be shorter
  because they are not interactive.
- **Focus-visible.** Every interactive control gets a 3 px
  `--accent-strong` outline with a 2 px offset. The custom switch mirrors the
  focus ring onto its visible track.
- **Semantic grouping.** Setup uses `<fieldset>` + `<legend>` so screen readers
  announce the category when entering each group.
- **Label and description.** Each control is associated with its label. The
  longer description and the `max_walking` hard-threshold note are referenced
  through `aria-describedby`.
- **No color-only meaning.** Category badges carry text, not just tone. The
  hard group and hard chips say `HARD ACCESSIBILITY NEED`.
- **Reduced motion.** Transitions are disabled under
  `prefers-reduced-motion: reduce`.
- **Long Chinese/English strings.** Labels and chips use
  `overflow-wrap: anywhere` and `word-break: break-word`.
- **320 px width.** The legend, rows, and controls stack to one column; native
  inputs become full width.
- **200% zoom.** The layout uses `minmax(0, 1fr)` and `min-width: 0`, so text
  reflows instead of forcing horizontal scroll.

More detail, including keyboard and screen-reader test matrices, lives in
`ACCESSIBILITY_DEEP_DIVE.md`.

---

## 6. i18n notes

- `i18n.tsx` is **not modified**. Existing keys are owned by the host.
- The capability feature keeps a small feature-local bilingual dictionary
  (`LocalizedText = { en, zh }`) in `capabilityTypes.ts` and the components.
- Components read the active locale through `useLocale()` and fall back to
  English when rendered outside `LocaleProvider` (useful for isolated tests).
- Category badges and the two required policy sentences have stable English
  text in the `en` dictionary; the `zh-CN` dictionary carries the Chinese
  equivalent.
- **中文备注：** 新增文案只放在能力模块内部词典，避免与主工作树 `i18n.tsx`
  冲突。合并时若宿主已有等价 key，可优先使用宿主 key，并保留英文 fallback。

---

## 7. Store API

`capabilityStore.ts` uses the localStorage key
`citynexus.v18.3.capabilities` and exports:

| Export | Behavior |
| --- | --- |
| `loadCapabilities(storage?)` | Reads JSON, validates every key, falls back to defaults on missing/corrupt data or unavailable storage. Never throws. |
| `saveCapabilities(capabilities, storage?)` | Writes JSON, returns `true` on success and `false` when storage is unavailable. Never throws. |
| `summarizeCapabilities(capabilities?)` | Normalizes input and returns all ten items plus the three recognized groups, counts, disclaimer, authority note, and no-schema note. |
| `CAPABILITY_STORAGE_KEY` | The stable persistence key. |

The store is SSR-safe: when `window`/`localStorage` is unavailable it returns
defaults and no-ops saves.

---

## 8. Merge boundaries

This feature is additive and isolated. The merge boundary is:

```text
src/features/capability/capabilityTypes.ts
src/features/capability/capabilityStore.ts
src/features/capability/TravelerCapabilityPanel.tsx
src/features/capability/CapabilitySummary.tsx
src/features/capability/capability.css
```

Rules for the host merge:

1. Do **not** edit `src/types.ts` to add capability fields. The capability
   types are experience-layer reference types.
2. Do **not** add capability keys to `i18n.tsx` for this reference module. The
   feature carries its own bilingual dictionary and uses `useLocale()`.
3. Import the stylesheet once at the host entry or feature boundary:
   `import "./features/capability/capability.css";`
4. Render the panel where journey setup already renders traveler preferences.
5. Pass the same state into `mode="summary"` for the Copilot column. A host may
   pass `capabilities` and handle `onChange`; otherwise the component owns
   localStorage state.
6. Keep `wheelchair_step_free` and `avoid_stairs` as
   `HARD_ACCESSIBILITY_NEED`. Do not move them into a preference bucket.

### Host integration example

```tsx
const [capabilities, setCapabilities] = useState(loadCapabilities());

<TravelerCapabilityPanel
  mode="setup"
  value={capabilities}
  onChange={(next) => setCapabilities(next)}
/>

<TravelerCapabilityPanel mode="summary" value={capabilities} />
```

---

## 9. Explicit: no backend schema change

> **No backend schema change.**
> This module does not add database columns, API fields, contract fields,
> PlanVersion fields, Gateway/Guardian inputs, or MCP tool payloads. All types
> in `capabilityTypes.ts` are experience-layer reference types. Persistence is
> limited to browser `localStorage` under
> `citynexus.v18.3.capabilities`. The UI must not present localStorage state as
> backend truth; it is a recognized reference.

**中文：** 本模块不修改任何后端 schema、数据库、API 契约或 PlanVersion。所有类型
均为体验层参考类型，持久化仅使用浏览器 `localStorage`。

---

## 10. Acceptance checklist

- [ ] All ten keys exist exactly once in `CAPABILITY_KEYS`.
- [ ] `wheelchair_step_free` and `avoid_stairs` are `HARD_ACCESSIBILITY_NEED`.
- [ ] `max_walking` is numeric with unit `minutes` and a visible hard threshold
      note.
- [ ] `pace` accepts only `relaxed | balanced | fast`.
- [ ] `quiet_sensory` has an optional level and can be recognized without one.
- [ ] Setup groups controls by category and shows the three-category legend.
- [ ] Summary puts hard needs in their own group with a distinct badge.
- [ ] Summary renders protected commitments separately from preferences.
- [ ] Summary always shows the required trade-off sentence and the
      "recognized reference, not a backend authority" line.
- [ ] localStorage key is `citynexus.v18.3.capabilities`.
- [ ] No existing file was modified for this feature.
- [ ] CSS selectors are scoped under `.cnx-capability`.
- [ ] Controls are at least 44 px tall and have `:focus-visible` styling.
- [ ] Long English and Chinese strings wrap at 320 px without horizontal scroll.

## 11. 中文速记

- 三类：硬性无障碍需求、受保护承诺、用户偏好。
- 硬性：`wheelchair_step_free`、`avoid_stairs`，以及本次选择的 `stroller`。
- 受保护：`elderly_rest`、`infant_nap`、`toilet_rest_stop`。
- 偏好：`max_walking`、`luggage`、`pace`、`quiet_sensory`。
- 存储 key：`citynexus.v18.3.capabilities`。
- Copilot 摘要必须明确：已识别参考，而非后端权威；不修改后端 schema。
