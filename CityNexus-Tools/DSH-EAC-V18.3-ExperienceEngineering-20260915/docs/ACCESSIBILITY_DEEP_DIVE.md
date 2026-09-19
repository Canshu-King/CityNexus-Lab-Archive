# Accessibility Deep Dive — CityNexus V18.3

**Status:** experience-layer reference · additive helpers only
**Scope:** `reference-app/src/features/accessibility/` plus host guidance for
`AgentRunTimeline`, `CopilotDock`, and other surfaces
**中文摘要：** 本文定义键盘流、焦点管理、对话框语义、屏幕阅读器标签与
`aria-live` 节流策略，并提供 200% 缩放、320px 宽度、减少动态效果、触控尺寸、
中英文长文本与对比度检查清单。

---

## 1. Principles

1. **Keyboard first.** Every action reachable by pointer is reachable by
   keyboard, in a predictable order.
2. **Focus is owned.** Opening a dialog moves focus in; closing restores focus
   to the invoker.
3. **Announce meaning, not machinery.** Screen readers hear lifecycle changes,
   not every tool heartbeat.
4. **Never fabricate progress.** Timers may coalesce announcements; they must
   never advance a run, a percentage, or a plan state.
5. **Zoom and width are first-class.** The layout must survive 200% zoom and a
   320px viewport without loss of content or horizontal scrolling.
6. **Chinese and English are peers.** Long strings must wrap, and live text must
   be readable at base font sizes.

---

## 2. Keyboard flow

### Global shell

| Step | Expected behavior |
| --- | --- |
| `Tab` from address bar | First focusable item is the top bar locale toggle or nav entry, depending on DOM order. |
| `Tab` through nav | Desktop nav items are real buttons; mobile bottom nav items are at least 44px tall. |
| `Shift + Tab` | Reverses the same order; focus must not disappear into the map canvas. |
| `Enter` / `Space` | Activates buttons, chips, and toggles. |
| `Escape` | Closes Copilot / sheet-style overlays and restores focus to the invoker. |

### Capability setup

1. `Tab` enters the first category legend, then the first fieldset.
2. Category fieldsets use `<legend>`; screen readers announce the category.
3. The switch input is focusable; the visible track receives the focus ring.
4. Number, select, and sensitivity-level controls are native form controls, so
   arrow keys and typing work without custom key handling.
5. After editing `max_walking`, the description and hard-threshold note remain
   associated through `aria-describedby`.

### Copilot / dialog

1. Opening the panel focuses the close button on desktop, or the composer on
   mobile.
2. `Tab` must cycle within the dialog while it is open.
3. `Escape` closes the dialog and returns focus to the launcher.
4. No keyboard trap may prevent closing or leaving the dialog.

---

## 3. Focus management

`src/features/accessibility/focus.ts` is dependency-free and exports four
helpers.

| Helper | Contract |
| --- | --- |
| `getFocusable(container)` | Returns enabled, visible, keyboard-focusable elements in DOM order. Excludes `disabled`, `hidden`, `aria-hidden="true"`, `display:none`, `visibility:hidden`, and `tabindex="-1"` (unless content-editable). |
| `focusFirst(container)` | Focuses the first focusable element and returns it, or `null` when none exist. |
| `trapFocus(container, event)` | Handles a `Tab` keydown. Wraps focus from last to first (and first to last with `Shift`). Returns `true` when it prevented default navigation. |
| `restoreFocus(element)` | Focuses a still-available element and returns `true`; safe against detached or null elements. |

### Recommended dialog wiring

```tsx
function Dialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const invokerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      invokerRef.current = document.activeElement as HTMLElement | null;
      focusFirst(panelRef.current);
      return;
    }
    restoreFocus(invokerRef.current);
  }, [open]);

  return (
    <div
      ref={panelRef}
      role="dialog"
      aria-modal="true"
      aria-label="Copilot"
      onKeyDown={(event) => trapFocus(panelRef.current, event.nativeEvent)}
    >
      {/* dialog content */}
    </div>
  );
}
```

**中文：** `focusFirst` 打开后进入焦点；`trapFocus` 维持循环；`restoreFocus`
关闭后回到触发元素。

---

## 4. Dialog semantics

- Use `role="dialog"` with an accessible name (`aria-label` or
  `aria-labelledby`). Copilot already uses `role="dialog"` and a title label.
- Add `aria-modal="true"` only when the rest of the page is actually inert.
  If the implementation is a non-modal dock, keep `role="dialog"` but omit
  `aria-modal` so screen-reader users can still explore the page.
- The dialog should own its initial focus and restore it on close.
- The close button must have a visible text label or an `aria-label`
  (for example `Close Copilot` / `关闭副驾`).
- Do not place focusable content behind a modal without `inert` or
  `aria-hidden`.

### Sheet / mobile pattern

Mobile Copilot uses a bottom-sheet presentation. The same dialog semantics
apply; add a visible close button and keep the composer reachable. If the sheet
can be dismissed by drag, also provide a keyboard-accessible close action.

---

## 5. Screen-reader labels

| Element | Label strategy |
| --- | --- |
| Brand / app shell | Visible text is enough; decorative marks use `aria-hidden="true"`. |
| Nav items | Use button text; active state must be conveyed by `aria-current="page"` or equivalent. |
| Runtime badge | Expose semantic, execution, truth, and source as text, not color alone. |
| Fixture banner | Read as text; never rely on the dashed border to say "recorded". |
| Capability toggle | Native checkbox plus visible label; description and hard note are `aria-describedby`. |
| Category badge | Text (`HARD ACCESSIBILITY NEED`) plus group heading; color is redundant. |
| Live region | `role="status"` / `aria-live="polite"` by default; `role="alert"` / `assertive` only for urgent transitions. |
| Timeline step | Human label first; technical tool name may follow as secondary text. |
| Tool events | Not announced through `aria-live`; they remain readable in the DOM/list. |

**Rule:** if a piece of information is only conveyed by color, border style, or
position, add text or an accessible label.

---

## 6. `aria-live` throttling strategy

`src/features/accessibility/useThrottledAnnouncer.ts` returns
`{ announce, message }`.

### Behavior

- **Default minimum interval:** 1500 ms between ordinary announcements.
- **Bursty ordinary events:** only the latest message is kept; a trailing timer
  flushes it once the interval allows.
- **Important transitions:** `approval_required`, `failed`, `stopped`, and
  `completed` bypass the throttle. Calls in the same React batch collapse to
  the final lifecycle message.
- **Raw event mapping:** run-level events only — `approval.required`,
  `run.failed`, `run.stopped`, and `run.completed` map to the important
  vocabulary. Technical `tool.*` events are intentionally excluded.
- **Timers are announcements only.** The hook never advances run progress.

### API

```ts
const { announce, message } = useThrottledAnnouncer({ minIntervalMs: 1500 });

announce("Searching alternatives");
announce("Approval required", { transition: "approval_required" });
announce("Run failed", "failed"); // transition shorthand
```

### Why a separate live region

Use `LiveRegion` from `LiveRegion.tsx`:

```tsx
<LiveRegion message={message} />
<LiveRegion message={urgentMessage} assertive />
```

The region is visually hidden but present in the accessibility tree. Only
meaningful lifecycle text should flow into it. Technical details such as tool
names, durations, and raw event types stay in ordinary DOM text where a screen
reader user can read them on demand.

**中文：** 普通事件 1500ms 节流并合并；`approval_required`、`failed`、`stopped`、
`completed` 立即播报。工具名称、耗时等技术细节不进入 `aria-live`。

---

## 7. How `AgentRunTimeline` should use the throttled announcer

The timeline is visually rich, but screen readers should only hear the run's
lifecycle. The merge should follow this pattern:

1. Import the hook and `LiveRegion`.
2. Keep one `message` that describes only an important lifecycle change.
3. Ignore tool-level events (`tool.started`, `tool.completed`), technical
   durations, and raw tool names for announcement purposes.
4. Announce the latest important transition when it changes.
5. Render one `LiveRegion` near the timeline.

```tsx
import { useEffect } from "react";
import { LiveRegion } from "../features/accessibility/LiveRegion";
import { useThrottledAnnouncer } from "../features/accessibility/useThrottledAnnouncer";

function TimelineAnnouncements({ runStatus }: { runStatus: string }) {
  const { announce, message } = useThrottledAnnouncer({ minIntervalMs: 1500 });

  useEffect(() => {
    if (runStatus === "approval_required") {
      announce("Approval required", { transition: "approval_required" });
    } else if (runStatus === "failed") {
      announce("Agent run failed", { transition: "failed" });
    } else if (runStatus === "stopped") {
      announce("Agent run stopped", { transition: "stopped" });
    } else if (runStatus === "success") {
      announce("Agent run completed", { transition: "completed" });
    }
  }, [announce, runStatus]);

  return <LiveRegion message={message} />;
}
```

### What to remove or narrow

If the host timeline currently puts `aria-live="polite"` on the whole section,
the merge should **remove or narrow that region**. A whole-section live region
announces every tool step and every re-render, which floods assistive
technology. The desired division is:

| Content | Live region? |
| --- | --- |
| Run status becomes `approval_required` | Yes, important |
| Run status becomes `failed` | Yes, important |
| Run status becomes `stopped` | Yes, important |
| Run status becomes `completed` | Yes, important |
| `tool.started` / `tool.completed` | No |
| Duration, sequence number, raw event type | No |
| Proposal details / approval copy | On demand, as ordinary DOM text |
| Local replay position changes (recorded fixture) | No; it is not server truth |

**中文：** 只播报运行级重要状态变化；工具事件与技术细节保留在普通文本中，不进入
`aria-live`。回放位置变化不代表服务端进度，不应播报为进展。

---

## 8. 200% zoom

At 200% zoom the effective viewport is roughly half the CSS width.

- Use `minmax(0, 1fr)` in grids so text can shrink without forcing overflow.
- Avoid fixed heights on text containers. Capability rows and timeline steps
  should grow with wrapped content.
- Do not hide labels or descriptions just to keep a grid compact.
- The map may remain visual evidence, but all actionable route and recovery
  information must also exist as text.
- Test `Ctrl/Cmd +` to 200% on the capability setup, Copilot, and timeline.

## 9. 320 px width

- Capability legend, setup rows, and summary chips stack to one column.
- Controls become full width at `max-width: 360px`.
- The Copilot composer must keep the textarea and send action reachable.
- No horizontal scroll: `document.documentElement.scrollWidth` should not exceed
  `window.innerWidth`.
- Long bilingual labels wrap instead of ellipsizing away meaning.

## 10. Reduced motion

- Honor `prefers-reduced-motion: reduce`.
- `motion.ts` collapses all duration tokens to `0ms`.
- `capability.css` disables capability transitions under the same query.
- Recorded timeline replay should jump to the final event instead of animating
  when reduced motion is requested.
- No essential status may depend on motion; the live region text is the
  accessible source of truth.

## 11. Touch targets

- Interactive controls: minimum 44 × 44 CSS px.
- The custom switch keeps a 44 × 44 label while drawing a 44 × 24 track.
- Chips that are purely informational may be smaller, but any chip used as a
  button or filter must be at least 44px tall.
- Spacing between adjacent targets should prevent accidental activation.

## 12. Long Chinese / English

- Use `overflow-wrap: anywhere` and `word-break: break-word` for labels,
  summaries, chips, and notices.
- Do not truncate category names or the two policy sentences.
- Prefer stacked layout over ellipsis when a chip label competes with its value.
- Check `zh-CN` and `en` with the longest realistic strings, not just the
  shortest defaults.

---

## 13. Contrast spot-check checklist

Run these checks for both `en` and `zh-CN` and for the three category tones.
Use a contrast checker on rendered colors; do not trust hues by eye.

- [ ] Body text (`--text`) on `--bg`, `--bg-card`, and `--bg-raised` ≥ 4.5:1.
- [ ] Muted text (`--muted`) on card backgrounds ≥ 4.5:1 for body copy; for
      incidental hints ≥ 3:1 at large/bold sizes only.
- [ ] Accent text (`--accent-strong`) on dark backgrounds ≥ 4.5:1.
- [ ] Hard badge `#ffb0a8` on its translucent red background ≥ 4.5:1.
- [ ] Protected badge `#ffd98a` on its translucent amber background ≥ 4.5:1.
- [ ] Preference badge `#bfeaff` on its translucent blue background ≥ 4.5:1.
- [ ] Focus outline `--accent-strong` against adjacent backgrounds ≥ 3:1.
- [ ] Disabled controls keep ≥ 3:1 text contrast, or are clearly marked.
- [ ] Error / stopped / failed text is not red-on-dark below 4.5:1.
- [ ] No information is conveyed by hue alone; each badge includes text.

**Spot-check method:** screenshot the component, sample foreground and
background colors, and record the ratio next to each item. Repeat with the
`prefers-color-scheme` variant if the host adds one.

---

## 14. Playwright / manual test matrix

### Playwright matrix

| # | Area | Automated check | Expected |
| --- | --- | --- | --- |
| 1 | Keyboard nav | `Tab` through capability setup; assert every control receives focus. | All 10 capabilities reachable. |
| 2 | Switch focus | Focus a switch input; assert visible focus ring on the track. | `:focus-visible` outline present. |
| 3 | Dialog focus | Open Copilot; assert focus is inside the dialog. | Focus on close/composer. |
| 4 | Dialog trap | Send `Tab` at the last control. | Focus wraps to the first control. |
| 5 | Dialog close | Press `Escape`; assert focus returns to the launcher. | Invoker focused. |
| 6 | Live region | Trigger an approval state; assert `role="status"` text. | Lifecycle message appears once. |
| 7 | Throttle | Fire several normal events quickly; assert only the latest trailing message appears. | No flood; ≤ 1 message per 1500 ms. |
| 8 | Tool events | Advance a tool step; assert live region text unchanged. | Technical events not announced. |
| 9 | 320 px | Set viewport 320×720; measure `scrollWidth - innerWidth`. | `0` horizontal overflow. |
| 10 | 200% zoom | Apply 200% page zoom or equivalent viewport; assert no clipped actions. | Content reflows, controls visible. |
| 11 | Reduced motion | `page.emulateMedia({ reducedMotion: "reduce" })`; open the capability panel. | No transition-driven state changes. |
| 12 | Touch target | Measure interactive controls. | `height >= 44` and `width >= 44`. |
| 13 | Long zh-CN | Load `?locale=zh` and inspect long labels. | Wrap, no ellipsis loss. |
| 14 | Long en | Inspect longest English policy sentences. | Wrap, no overlap. |
| 15 | Contrast | Sample badge and note colors. | Ratios from §13 pass. |

### Manual matrix

| Area | Manual steps | Pass criteria |
| --- | --- | --- |
| Screen reader | NVDA / VoiceOver: open setup, change category. | Category announced; control label + description read. |
| Screen reader | Trigger approval. | Lifecycle message announced once; tool steps not announced. |
| Keyboard only | Complete setup without a mouse. | Every control toggled and saved. |
| 200% zoom | Use browser zoom on setup + Copilot. | No horizontal scroll; all actions reachable. |
| 320 px | DevTools responsive mode. | Single-column layout; no clipped text. |
| Reduced motion | OS setting + reload. | No replay animation; status still readable. |
| Contrast | Inspect hard/protected/preference chips. | Text legible; badge text present. |
| Chinese | Switch locale to 中文. | All feature copy localized; long strings wrap. |

---

## 15. 中文速记

- 键盘：所有操作可 Tab 到达；对话框内 Tab 循环；Esc 关闭并还原焦点。
- 焦点：`focusFirst` 进入、`trapFocus` 循环、`restoreFocus` 还原。
- 播报：普通事件 1500ms 节流；`approval_required`、`failed`、`stopped`、
  `completed` 立即播报；工具事件不进 `aria-live`。
- 不伪造进度：计时器只用于合并播报。
- 布局：200% 缩放、320px 宽度、中英文长文本都必须可读且无横向滚动。
- 触控：交互控件至少 44px；`focus-visible` 必须可见。
