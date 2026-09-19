# F. Desktop / Mobile / A11y Truth — DSH-EAC V18.3 Validation Lab

**Status: SOURCE-VERIFIED (live screenshot capture blocked this window).**

> **Why no live screenshots:** capturing `evidence/screenshots/` at the four
> required viewports (1440×900, 1280×720, 390×844, 430×932) needs the frontend
> served against a live backend. The backend `:8022` was brought down by the same
> upstream "Service is too busy" condition that stalled the live harness, so the
> running UI was unavailable. Every check below was therefore performed against the
> **frontend source** (`source-snapshot/frontend/src`) and is fully reproducible
> via the capture harness shipped in `tests/capture_a11y_screenshots.py`.

## 1. Checks (Matrix F)

| Check | Method | Result |
|---|---|---|
| DIRECT vs Hermes truth | read `runtime_identity` / `native_mcp_proven` | truthful: `HERMES_NATIVE_MCP`, `native_mcp_proven=false` (not over-claimed) ✅ |
| Run timeline | `.v8-timeline-track`, `AgentRunRail.tsx` | renders event timeline from SSE ✅ (source) |
| stopped / failed / offline | `.v8-status-pill`, `.v8-live-label` (coral) | distinct visual states ✅ (source) |
| Approval | `AgentComposer.tsx`, `JourneyInboxWorkbench.tsx` | approval gate present ✅ (source) |
| Keyboard | `:focus-visible` outline + `onKeyDown`/`tabIndex` across ~18 components | operable by keyboard ✅ |
| Focus | `.v8-product-shell :focus-visible { outline: 3px solid #9aa8ff }` | visible focus ring ✅ |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` blocks | animations + smooth-scroll disabled ✅ |
| Long bilingual text | `overflow-wrap: anywhere`, `white-space: pre-wrap` | wraps, no overflow ✅ |
| No horizontal overflow | `max-width:1370px` content; `min()` widths; `@media 960/680px` collapse grids; `.v8-mobile-nav` fixed | layout contained at all 4 viewports ✅ (source) |

## 2. Keyboard / focus / ARIA evidence (real hits)

ARIA/keyboard handlers are present in the actual component tree:

```
V8Experience.tsx, main.tsx, JourneyMap.tsx, MapPanel.tsx, CopilotDock.tsx,
AgentRunRail.tsx, AgentComposer.tsx, V10LiveExecutionPanel.tsx,
V12AuthoritativeJourneyPanel.tsx, StayExplorer.tsx, MobilitySheet.tsx,
BookingArtifactScanner.tsx, V14RecoveryTruthPanel.tsx, JourneyInboxWorkbench.tsx,
JourneyTrialSetup.tsx, RealCityDiscoveryPanel.tsx, Icon.tsx, viewTransition.ts
```

- `styles.css:244` — `.v8-product-shell button:focus-visible,
  [role="button"]:focus-visible, textarea:focus-visible { outline: 3px solid #9aa8ff; outline-offset: 3px }`
- `styles.css:209` — `.v8-sr-only` screen-reader-only utility present.
- `styles.css:255` & `:385` — `prefers-reduced-motion` blocks (`.v8-page` animation
  none; `* { scroll-behavior: auto !important }`).
- `styles.css:348` — `.cn-agent-event-detail { overflow-wrap: anywhere }`.
- `styles.css:351` — raw event code `white-space: pre-wrap`.

## 3. Defect F3 — `.v8-runtime-card` missing CSS (OPEN)

**Location:** `source-snapshot/frontend/src/features/intelligence/ControlTowerPanel.tsx:47`

```tsx
<div className="v8-runtime-card" data-testid="v17-runtime-status">
```

**Problem:** the class `v8-runtime-card` has **no rule** in `styles.css` or
`v10.css` (verified by exact-string search — zero matches). Its children
(`<b>` label, value, `<small>` disclaimer) therefore render with default
`display:inline`, collapsing the label/value/disclaimer onto a single line across
**all three viewports** (desktop and mobile alike). This is a layout/legibility
defect on the runtime-status card.

**Recommended one-line fix** (mirrors the sibling `.v8-intel-facts` pattern that
already does this correctly):

```css
.v8-runtime-card { display: block; }
.v8-runtime-card b, .v8-runtime-card small { display: block; }
```

**Verdict: OPEN** — confirmed by exact string search; not a false positive
(the earlier `.v8-runtime` match at `styles.css:154` is a *different* class).

## 4. Reproduction / capture harness

`tests/capture_a11y_screenshots.py` boots the frontend (Vite) against a live
`:8022` backend and snapshots the four viewports into `evidence/screenshots/`.
Run it once the stack is healthy:

```bash
python tests/_run_backend_foreground.py          # :8022
cd source-snapshot/frontend && npm run dev        # :5173
python tests/capture_a11y_screenshots.py          # writes evidence/screenshots/*.png
```

Until then, `evidence/screenshots/README.md` records this gap so Codex can close
it on the next responsive window.

## 5. Verdict

**Source-verified PASS** on keyboard, focus, reduced-motion, long-text wrapping,
and no-horizontal-overflow. One real defect found (**F3**, trivial CSS fix).
Live screenshot evidence is the single outstanding item, blocked solely by the
upstream LLM stall.
