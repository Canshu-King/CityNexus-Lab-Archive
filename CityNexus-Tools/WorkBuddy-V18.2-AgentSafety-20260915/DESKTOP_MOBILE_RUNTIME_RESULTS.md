# DESKTOP / MOBILE RUNTIME RESULTS — V18.2 Family F

**Harness:** `tests/frontend_runtime_truth.mjs` (Playwright, system Chrome, headless)
**Target:** the real frontend — isolated Vite dev server on **4173**, `/api/v1`
proxied to the isolated backend on **8021** (never Codex's 8000)
**Raw results:** `evidence/results_frontend.json`
**Screenshots:** `evidence/screenshots/`
**Result:** **12 PASS / 3 FAIL**

| Viewport | Type |
|---|---|
| 1440 × 900 | desktop |
| 390 × 844 | iPhone |
| 430 × 932 | iPhone Pro Max |

The question: *does the mobile/desktop layout change what the product claims
about its agent runtime?*

---

## Setup

The app renders its setup screen unless a journey id is already stored. The
harness therefore seeds one through the proxied API and injects it before
navigation:

```js
POST /api/v1/demo/reset                      -> journey 22222222-…
POST /journeys/{id}/plans/generate           -> 1 plan
POST /journeys/{id}/plans/{pid}/select
POST /journeys/{id}/start
context.addInitScript -> localStorage["citynexus.v8.journey_id"] = <id>
```

Routes walked: `/v8/intelligence` (Control Tower, hosts the runtime card) and
`/v8/agent` (Copilot). Each viewport gets a fresh context; `pageerror`,
`console.error` and any `>=500` response are captured for the whole walk.

---

## Results

| ID | Assertion | 1440×900 | 390×844 | 430×932 |
|---|---|---|---|---|
| F1 | runtime card shows the computed identity | PASS | PASS | PASS |
| F2 | no native-Hermes run rail / Stop button | PASS | PASS | PASS |
| F3 | layout does not alter the claim | PASS | PASS | PASS |
| F4 | no page errors, no 5xx | PASS | PASS | PASS |
| **F5** | value/caveat are block-level (no run-on line) | **FAIL** | **FAIL** | **FAIL** |

---

## F1 — the runtime card tells the truth · PASS (all viewports)

The Control Tower renders, on every viewport:

```
Agent runtime source
NOT_CONFIGURED
Native Hermes MCP is not claimed without a verified proof run
```

with the chain `Deterministic fallback → CityNexus Direct → Gateway`.

Three things are right here:

1. the identity is the **computed** value (`NOT_CONFIGURED`), matching
   `GET /agent/runtime-status` exactly — no client-side hard-coding;
2. the chain drawn is the **fallback** chain, not the Hermes chain
   (`ControlTowerPanel.tsx` branches on `runtime_identity`);
3. the caveat is present and specific.

`F-desktop_intelligence.png` shows this rendered correctly.

## F2 — the copilot shows no native-Hermes chrome · PASS (all viewports)

`CopilotDock.tsx` gates both the run rail and the Stop button on
`activeRun?.runtime_identity === "HERMES_NATIVE_MCP"`:

```tsx
{activeRun?.runtime_identity === "HERMES_NATIVE_MCP" && steps.length > 0 && <AgentRunRail steps={steps} />}
{activeRun?.runtime_identity === "HERMES_NATIVE_MCP" && !/completed|…/i.test(runState ?? activeRun.status) && <button className="cn-copilot-stop" …>Stop</button>}
```

Measured: `rail=0 stop=0` on all three viewports. The gate is correct and the
gating is driven by the same honest identity the backend reports.

This is the front-end half of the A4 result: the backend does not fabricate a
native run, and the UI does not render one.

## F3 — layout does not alter the claim · PASS

The runtime text read from the DOM is identical across all three viewports.
No responsive branch changes the identity string, and no mobile-only component
re-states it from a different source.

## F4 — no page errors, no 5xx · PASS

`pageErrors=0` and no `>=500` responses on any viewport, across both routes.
Notable given that F1 of Family A proves the backend *does* return 500 for
`GET /agent/hermes/runs/{id}` — the frontend simply never calls it while the
runtime is `NOT_CONFIGURED`, so the defect is latent rather than visible. **A
UI that started polling native run state on mount would surface the 500
immediately.**

---

## F5 — the runtime-truth card is unstyled · **FAIL** (defect F3)

This is the defect. Measured live:

| Viewport | `<span>` / `<b>` / `<small>` computed `display` | bounding-box tops |
|---|---|---|
| 1440×900 | `["inline","inline","inline"]` | `[587, 587, 589]` |
| 390×844 | `["inline","inline","inline"]` | `[680, 700, 702]` |
| 430×932 | `["inline","inline","inline"]` | `[650, 670, 672]` |

Rendered text:

```
Agent runtime sourceNOT_CONFIGUREDNative Hermes MCP is not claimed without a verified proof run
```

**Root cause.** `ControlTowerPanel.tsx` emits:

```tsx
<div className="v8-runtime-card" data-testid="v17-runtime-status">
  <span>{t("intel.runtimeSource")}</span>
  <b>{runtimeStatus?.runtime_identity ?? t("intel.runtimeUnknown")}</b>
  <small>{runtimeStatus?.native_mcp_proven ? … : t("intel.nativeMcpNotProven")}</small>
</div>
```

But:

```
$ grep -rn "v8-runtime-card" --include=*.css frontend/src
(no matches)
```

The class has **no CSS rule anywhere**. `<b>` and `<small>` are inline by
default, so the label, the identity and the caveat concatenate into one line.
The sibling block in the same file gets it right —
`.v8-intel-facts b, .v8-intel-facts small { display: block; }` — the runtime
card just never received the equivalent rule.

**Why it matters.** This card exists for one reason: to stop the product
over-claiming. Its caveat — *"Native Hermes MCP is not claimed without a
verified proof run"* — is the sentence that makes the `NOT_CONFIGURED` state
honest. Rendering it glued to the identity value produces

> `Agent runtime sourceNOT_CONFIGUREDNative Hermes MCP is not claimed…`

which a reader can parse as *"Agent runtime source: NOT_CONFIGURED Native
Hermes MCP"* — i.e. as naming Hermes as the source. The one UI element whose
job is to prevent that misreading is the one element that invites it.

The defect is present on desktop too; it is simply more obvious on mobile,
where the wrapped text produces a longer run-on block (see
`F-iphone_intelligence.png` and `F-iphone-max_intelligence.png`).

**Why the assertion checks `display`, not line offsets.** An earlier version of
this check compared the three elements' vertical offsets. On the two mobile
viewports that spuriously **passed**, because the text wrapped and the
wrapped fragments landed at different `top` values. Checking the computed
`display` tests the cause, not a symptom, and fails consistently on all three
viewports.

**Proposed fix** (handoff §2): one rule, e.g.

```css
.v8-runtime-card span,
.v8-runtime-card b,
.v8-runtime-card small { display: block; }
.v8-runtime-card b { margin: 6px 0 4px; font-size: 15px; }
.v8-runtime-card small { color: #8fa7d3; font-size: 10px; line-height: 1.5; }
```

---

## Summary

| ID | Property | Result |
|---|---|---|
| F1 | runtime card reports the computed identity on every viewport | PASS ×3 |
| F2 | no native-Hermes run chrome while not on Hermes | PASS ×3 |
| F3 | layout does not change the claim | PASS ×3 |
| F4 | no page errors / no 5xx | PASS ×3 |
| F5 | value and caveat render on their own lines | **FAIL ×3** |

**The product tells the truth on mobile and desktop alike.** The one defect is
purely typographic — but it lands on the single most load-bearing sentence in
the runtime-honesty surface.
