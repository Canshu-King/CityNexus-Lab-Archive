# Web / Mobile Capability Results

**Question:** does the UI lie about evidence state — and does it meet the one accessibility requirement the project actually specified?
**Evidence:** `evidence/web_mobile_results.json` (64 cells), `evidence/web_mobile_focus_and_axe.json`, `evidence/web_mobile_bootstrap.json`, `evidence/screenshots/` (64 PNGs)
**Method:** Playwright driving system Chrome against the isolated Vite build (`127.0.0.1:4193` → backend `8040`), 4 viewports × reduced-motion on/off × 8 routes, plus a Tab-focus probe and an axe-core WCAG 2 A/AA scan.

---

## 1. Matrix and result

| Dimension | Values |
|---|---|
| Viewports | `390×844` (iPhone 14), `430×932` (iPhone Pro Max), `1280×720`, `1440×900` |
| Reduced motion | `no-preference`, `reduce` |
| Routes | `hub`, `live`, `map`, `studio`, `bookings`, `agent`, `authoritative`, `twin` |
| **Cells** | **64** |
| Loaded successfully | **64 / 64** |
| Screenshots captured | **64** |
| Distinct rendered content states | **16** (real per-route content, not a shared shell) |

### A methodological correction worth recording

The first pass produced **64 screenshots that collapse to 4 distinct images — one per viewport**. Within a viewport, all 16 files (8 routes × reduced-motion on/off) were byte-identical: every route rendered the same screen. Cause: `/v8/<route>` renders the **onboarding form** until a journey is selected, and the selection lives in `localStorage` under `citynexus.v8.journey_id`. Without seeding, a "runtime review" measures the onboarding page 64 times and reports nothing.

The scan now bootstraps by clicking **"Use the sealed Tianjin demo"**, then reuses `storageState` across all measurement contexts (`evidence/web_mobile_bootstrap.json`):

```json
{"seeded": true,
 "state": {"origins": [{"origin": "http://127.0.0.1:4193",
   "localStorage": [{"name": "citynexus.v8.journey_id",
                     "value": "1d434f26-aa4a-4fca-9d0c-72128137a793"}]}]}}
```

Everything below is from the corrected run. **The superseded screenshots are retained as evidence of the correction, not deleted** — a representative image plus the md5 grouping of all 64 files is in `evidence/screenshots_superseded/`, and the full set remains in the lab at `_old_shots/`.

Second environment trap, for reproducibility: the host runs a system proxy (U1S1 Cloud on `127.0.0.1:7892`). Chrome inherits it and routes loopback requests through it, which hangs or returns 502. The browser is launched with `proxy: { server: "direct://" }` and `--no-proxy-server`.

---

## 2. Does the UI lie about capability evidence? No — it says nothing at all

This is the finding, stated precisely.

**It cannot lie, because it holds no capability data.** The `experience` payload keys are:

```
active_plan, journey, mobility_facts, offers, options,
provider_mesh, selected_option_id, traveler_twin, trip
```

`mobility_facts` is the only mobility-adjacent key, and it describes the **provider** (`mock-mobility`, `deterministic-offline`), not the traveller. There is no `capability`, `accessibility`, `step_free`, `wheelchair` or `evidence_state` field anywhere in the API surface (locked by `test_v19_char_no_canonical_capability_field_anywhere_in_the_api_surface`).

Measured across all 64 cells:

| Capability pattern searched in rendered text | Cells where present |
|---|---|
| `capability` | **0** |
| `step-free` / `step_free` | **0** |
| `accessib` | **0** |
| `wheelchair` | **0** |
| `stroller` | **0** |
| `unknown evidence` / `needs evidence` | **0** |
| `verified` | **16** |

**The `verified` hits are a false positive worth documenting.** All 16 come from one i18n string:

```ts
"hub.verifiedTarget": "verified total target",      // en
"hub.verifiedTarget": "已验证总额目标",              // zh
```

rendered beside the **stay budget** metric (`V8Experience.tsx:942`). It is a budget label. So the UI does use the word "verified" — about money — and never about a traveller's body.

### The mirror-image failure

Because no surface models capability, **no surface can warn**. A traveller whose step-free requirement is unverified sees:

- a `422` from the plan endpoint that says *"No feasible plan candidates satisfy the journey constraints"* — with no mention of accessibility;
- a `feasibility_envelope` reporting `robust: true` and `risk_reason_codes: []` **while no plan exists**;
- a status pill reading **"Planning ready"** on the hub (observed in the axe scan), on a journey that cannot be planned;
- a Copilot that characterises their requirement as *"偏好请求"* (a preference request).

There is no red badge, no warning banner, no "we don't know whether this venue is accessible". The UI is silent where it should be loudest.

**Verdict: the Web/Mobile layer does not lie about evidence state — it is incapable of telling the truth, and incapable of admitting ignorance.**

---

## 3. The one accessibility requirement the project specified

`NFR-014 "Accessible Critical State and Controls"` is the only accessibility requirement in the 138-item baseline. Its acceptance criterion:

> Critical state has a non-color indicator, and each primary control has an accessible text label and keyboard operation.
> `verificationMethod: accessibility_test`

Three testable clauses. Measured:

| Clause | Result | Evidence |
|---|---|---|
| Non-colour indicator for critical state | **partially met** | text labels accompany status pills, but 248 status dots are nameless |
| Accessible text label on each primary control | **FAILS** | **40** unlabelled controls |
| Keyboard operation | **met** | 14/14 tab stops reachable with a visible 3px focus outline |

### 3.1 Keyboard operation — passes

Tab-focus probe on `/v8/hub` at 390×844:

| # | Element | Accessible name | Focus indicator |
|---|---|---|---|
| 1 | button | Open navigation | `3px solid` |
| 2 | button | Switch language | `3px solid` |
| 3 | button | **`TI`** | `3px solid` |
| 4 | button | Switch language *(duplicate)* | `3px solid` |
| 5 | button | Try another city | `3px solid` |
| 6 | button | Open Trip Studio | `3px solid` |
| 7 | button | View plan → | `3px solid` |
| 8 | button | Compare stays → | `3px solid` |
| 9–11 | button | DAY 1 / DAY 2 / DAY 3 (full text) | `3px solid` |
| 12 | button | CityNexus Copilot | `3px solid` |
| 13 | button | Today | `3px solid` |
| 14 | button | Map | `3px solid` |

All 14 stops are reachable and all have a visible focus ring. Two minor defects: stop 3 is an avatar whose accessible name is the initials **`TI`** (not descriptive), and **"Switch language" appears twice** in the tab order (stops 2 and 4) — a duplicated control.

### 3.2 Accessible text labels — fails

**40 unlabelled controls** across the 64 cells:

| Route | Unlabelled controls (across all cells) | Kinds observed |
|---|---|---|
| `bookings` | **24** | `<textarea>`, `<input>` |
| `live` | **8** | `<input>` |
| `agent` | **8** | `<input>` |
| all others | 0 | — |

These are primary controls — a bookings route's textareas and inputs are how a traveller interacts with their trip. NFR-014-AC-01 requires "each primary control has an accessible text label". **This clause fails on 3 of 8 routes.**

### 3.3 Non-colour indicator — partially met, with a caveat

`frontend/src/styles.css:138`:

```css
.status-dot { display: inline-block; width: 7px; height: 7px; margin-right: 6px;
              border-radius: 50%; background: var(--v8-green); vertical-align: 1px; }
```

and the colour is semantic:

```css
.v8-live-label .status-dot { background: var(--v8-coral); }
```

So green means one thing and coral another. The dot itself is a bare `<span class="status-dot">` with **no text and no accessible name** — measured **248 times** across the 64 cells (4–7 per cell, matching `statusChipCount`).

The detector found **0** nodes where a status is conveyed by colour *alone*, because every observed pill also carries a text label:

```html
<span class="v8-status-pill"><span class="status-dot"></span>Planning ready</span>
```

So NFR-014's letter is probably satisfied — **but the dot is a 7 px colour-only signal sitting next to the text, with no accessible name**, and a screen reader announces nothing for it. If the label is ever truncated (see §4), the colour becomes the only signal. Treat the 248 as an accessibility risk, not a pass.

### 3.4 Colour contrast — fails on 5 of 6 scanned routes

axe-core, `runOnly: [wcag2a, wcag2aa]`:

| Route | Violations | Nodes | Sample node |
|---|---|---|---|
| `hub` | 1 | **21** | `<span class="v8-status-pill"><span class="status-dot"></span>Planning ready</span>` |
| `studio` | 1 | **12** | `<small>ARRIVAL anchor · TRANSIT</small>` |
| `twin` | 1 | **7** | `<p>From this Journey request</p>` |
| `bookings` | 1 | **6** | `<span class="v8-selected-label">STAY EVIDENCE</span>` |
| `agent` | 1 | **4** | `<span class="v8-status-pill violet">Twin context ready</span>` |
| `live` | **0** | 0 | — |

**50 nodes total, all `color-contrast`, all `impact: serious`.**

The project has already attempted this fix — `styles.css:166-167`:

```css
/* Keep the quiet travel UI legible at WCAG AA contrast on the live surface. */
.v8-product-shell { --v8-muted: #5f6c80; --v8-amber: #8a4f1d; --v8-coral: #a83d36; }
```

The comment says *"on the live surface"*, and `live` is indeed the **only** route with zero violations. The fix was applied to one route's variables and not to the shared palette the other five routes use. Since `NFR-014` is verified by `accessibility_test` and colour contrast is a core part of that, **`NFR-014` would fail its own verification method today.**

---

## 4. Layout and content integrity — passes

| Check | Result |
|---|---|
| Horizontal overflow (any viewport) | **0 / 64** |
| Text clipped to zero/near-zero width | **24 nodes** — one distinct cause |
| Nameless status nodes | 248 |
| Colour-only status nodes | 0 |
| Reduced-motion honoured in 32 cells | no animation-dependent assertion failed |

The single clipped-text cause, on `mobile-390x844` `/v8/hub`:

```json
{"tag": "span", "text": "Provider-backed route · WGS84", "scrollWidth": 150, "clientWidth": 1}
```

A 150 px text node collapsed to **1 px** at the smallest viewport. Content is present in the DOM, announced by a screen reader, and invisible on screen. `scrollWidth: 150` on 24 cells means the same element on every route.

The responsive work is otherwise solid: **zero horizontal overflow at 390 px** is a real achievement, and 16 distinct content states render correctly at all four viewports.

---

## 5. What the screenshots show

64 PNGs in `evidence/screenshots/`, named `<viewport>[-reduced]-<route>.png`. Representative:

| File | Shows |
|---|---|
| `mobile-390x844-hub.png` | the seeded Journey Hub with the trip metrics, day cards, "Planning ready" pill |
| `desktop-1440x900-twin.png` | the Traveler Twin surface with explicit vs learned labels |
| `mobile-390x844-bookings.png` | the Travel Wallet — the route with the most unlabelled controls |
| `desktop-1280x720-reduced-live.png` | the live surface under `prefers-reduced-motion` |

Read the `hub` and `bookings` screenshots together: the hub is a genuinely well-built, calm, readable screen; `bookings` is where the accessibility debt lives.

---

## 6. Findings index for this document

| ID | Finding | Severity |
|---|---|---|
| F18a | The UI never names capability or evidence state — 0 hits across 64 cells (it cannot lie, and cannot warn) | **P0** |
| F18b | `verified` appears 16× — but only as the **budget** label `"verified total target"` | — (documentation) |
| F18c | `feasibility_envelope` reports `robust: true`, `risk_reason_codes: []`, and the hub shows **"Planning ready"** while no plan exists | **P0** |
| F19a | **40** unlabelled primary controls (`bookings` 24, `live` 8, `agent` 8) — **NFR-014-AC-01 fails** | P1 |
| F19b | **50** axe `color-contrast` violations (serious) across 5 of 6 scanned routes — the existing fix covers only `live` | P1 |
| F19c | **248** nameless `.status-dot` spans carrying semantic colour (green/coral) | P2 |
| F19d | `"Provider-backed route · WGS84"` clipped to **1 px** on the smallest viewport (24 cells) | P2 |
| — | Keyboard operation passes: 14/14 tab stops, all with a 3 px visible focus ring | — ✔ |
| — | Zero horizontal overflow at 390 px across all 64 cells | — ✔ |
| — | "Switch language" duplicated in the tab order; the avatar's accessible name is `TI` | P3 |

---

## 7. Acceptance criteria

1. **The UI states what it does not know.** When a journey has an unverified accessibility requirement, the hub shows a warning — not a "Planning ready" pill, and not `robust: true`.
2. `feasibility_envelope.robust` is `false` (or absent) whenever no plan exists.
3. Every primary control on `bookings`, `live` and `agent` has an accessible text label — verified by re-running this scan with 0 unlabelled controls.
4. axe-core reports **0** `color-contrast` violations on all 8 routes at all 4 viewports — the `live`-only palette fix is generalised.
5. `.status-dot` carries an accessible name, or the state it signals is expressed in text that survives truncation.
6. No text node is clipped below a readable width at 390 px.
7. `NFR-014` is marked verified only after clauses 3 and 4 pass, since `verificationMethod: accessibility_test` is exactly this scan.
