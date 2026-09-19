# Mobile Capability UX

## 1. Compact Capability Shield

`MobileCapabilityShield` is the compact Today/Active-Journey surface.

- With HARD/STRONG needs: "2 travel needs protected" (count is caller-owned).
- Without needs: "No travel needs added yet" — not "all accessible".
- With an evidence gap: "Step-free access not verified" plus an
  `EvidenceBadge` in `UNVERIFIED` or `NEEDS_LIVE_EVIDENCE`.
- The primary action is always visible and at least 44px tall.

The shield is not a red panic wall. It uses the shared evidence palette and
keeps the main operation visible.

## 2. Mobile Copilot bottom sheet

`CopilotNeedsConfirmation` supports `surface="sheet"`.

- Renders `role="dialog"` with `aria-modal="true"` and an accessible title.
- Max height is bounded (`min(88vh, 720px)`) and the body scrolls.
- The same HARD persistence guard applies: future-journey persistence requires
  explicit acknowledgement or `This Journey only`.
- Ambiguity options remain radio-button based and keyboard operable.

## 3. Responsive behaviour

Validated viewports:

| Viewport | Purpose |
| --- | --- |
| 320×720 | stress / narrow phone |
| 390×844 | reference phone |
| 430×932 | large phone |
| 1280×720 | desktop |
| 1440×900 | wide desktop |

Key responsive rules:

- Advanced setup grid and confirmation editing collapse to one column under
  720px.
- Chips and primary buttons become full-width at 360px and below.
- Map markers switch from absolute overlay positioning to a stacked list on
  narrow viewports so evidence is still readable.
- Long Chinese/English copy wraps; no critical action is truncated.

## 4. Touch targets and motion

- Buttons, chips, disclosure controls, and map markers have a minimum 44px
  target in CSS.
- `prefers-reduced-motion: reduce` disables transitions and animations.
- The reference app is tested with reduced motion enabled.

## 5. Screen-reader semantics

- Setup fields use labels and fieldset/legend.
- Quick chips use `role="checkbox"` with `aria-checked`.
- Confirmation uses headings, lists, radio groups, and a restrained
  `aria-live="polite"` status only after a decision.
- Map markers use `role="img"` with descriptive `aria-label`, or a button when
  selectable.
- Plan/recovery sections use headings and labelled regions.
