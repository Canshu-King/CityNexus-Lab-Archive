# Codex Merge Guide — V18.2 Experience Lab → CityNexus main tree

**Safety rule (read first):** `D:\moodle\CityNexus` is the authoritative main worktree and is **READ-ONLY**. Never overwrite, force-copy into, or `git checkout`/`reset` the main tree from this lab. Codex reviews this reference build and **selectively integrates** only what it decides to adopt. The reference app performs **no backend mutation** (no PlanVersion, Gateway, Guardian or domain write) — it is an isolated UI/reference snapshot.

> 中文：`D:\moodle\CityNexus` 为只读主工作树，禁止覆盖。Codex 审核后有选择地合并；参考实现不写后端。

Lab root: `D:\moodle\CityNexus-Tools\DSH-EAC-V18.2-ExperienceLab-20260915`
Reference app: `...\reference-app`
Mechanical copy source: `patches/V18_2_EXPERIENCE_REFERENCE.patch`

---

## 1. New low-conflict addition tree

The primary deliverable is a **self-contained subtree** that can be copied in without touching existing files. Everything under `reference-app/src` maps 1:1 to the proposed main-tree path `frontend/src/features/experience-lab/**`:

```
frontend/src/features/experience-lab/
├── App.tsx
├── main.tsx
├── motion.ts
├── i18n.tsx
├── types.ts
├── testids.ts
├── shims.d.ts
├── components/
│   ├── AgentRunTimeline.tsx
│   ├── CopilotDock.tsx
│   ├── JourneyPulse.tsx
│   ├── MapBottomSheet.tsx
│   ├── MapCanvas.tsx
│   ├── RecoveryDiff.tsx
│   ├── RuntimeTruthBadge.tsx
│   ├── TodayTimeline.tsx
│   └── TravelerNav.tsx
├── data/
│   ├── hermesFixture.ts
│   └── journey.ts
└── styles/
    ├── app.css
    └── tokens.css
```

Also keep the runnable reference app itself in the lab:

```
reference-app/          # source of truth for the subtree + Playwright runner + production dist
tests/                  # mirror of reference-app/tests (docs/runner pointer in tests/README.md)
patches/V18_2_EXPERIENCE_REFERENCE.patch
```

Because the whole subtree is new, the only unavoidable conflicts are the two existing-file hunks in §3.

> 中文：新增子树 `frontend/src/features/experience-lab/**` 与现有文件基本零冲突；`reference-app/` 保留为可运行参考与测试宿主。

---

## 2. Existing-file reference hunks (reference-only)

These hunks appear in `patches/V18_2_EXPERIENCE_REFERENCE.patch`. They are **suggestions**, not authoritative edits, and may conflict with the Codex V18.x branch. Apply by hand with review, or skip entirely.

### 2.1 `frontend/src/routes/v8Routes.ts` (route entries)

```diff
 export const desktopRoutes = [
   { key: "hub", label: "Journey Hub", icon: "map", group: "TODAY" },
+  { key: "experience", label: "Experience Lab", icon: "spark", group: "TODAY" },
   { key: "live", label: "Live Journey", icon: "spark", group: "TODAY" },
   ...
@@
 export const mobileRoutes = [
   { key: "hub", label: "Journey", icon: "map" },
+  { key: "experience", label: "Lab", icon: "spark" },
   { key: "map", label: "Map", icon: "map" },
   ...
```

- Adds one `desktopRoutes` entry (group `TODAY`) and one `mobileRoutes` entry.
- In the reference app the same effect is produced by the local `ROUTES` array and `navigate()` in `App.tsx` (`experience` route key is the proposed integration point; the lab uses `#/journey`-style hash routes).

### 2.2 `frontend/src/main.tsx` (optional mount — reference-only)

The reference mount is `reference-app/src/main.tsx`:

```tsx
createRoot(root).render(
  <StrictMode>
    <LocaleProvider>
      <App />
    </LocaleProvider>
  </StrictMode>,
);
```

- This is **optional and reference-only**. Do not blindly merge it: the main tree already has its own root/provider stack, and the lab's `LocaleProvider` is the duplicate-provider risk in §5.
- The patch file's `main.tsx` hunk header is present but the body is intentionally left as a reference pointer; use `reference-app/src/main.tsx` as the example, then adapt to the main tree's existing entry.

> 中文：这两处是参考补丁，可能与 Codex V18.x 冲突；路由项建议通过特性开关接入，`main.tsx` 挂载不要直接覆盖。

---

## 3. Runtime contract assumptions

The UI is a read-only consumer of the following shapes. If Codex's real runtime differs, adapt at the boundary (`types.ts`) rather than rewriting components.

### 3.1 `AgentRunEvent` shape (`src/types.ts`)

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `string` | Event identity |
| `sequence_no` | `number` | Ordering within the run |
| `event_type` | `AgentEventType` union | See below |
| `tool_name` | `string?` | Required for `tool.*` events |
| `timestamp` | `string` | ISO-8601 with offset (`2026-09-15T08:12:00.000+08:00`) |
| `summary` | `string` | Human-readable server-truth text |
| `source` | `DataSource` | `LIVE` \| `RECORDED_FIXTURE` \| `OFFLINE` |
| `duration_ms` | `number?` | Recorded tool duration |
| `approval_id` | `string?` | Present on `approval.required` |
| `proposal_id` | `string?` | Present on `proposal.created` |
| `run_status` | `"running" \| "success" \| "failed" \| "stopped" \| "approval_required"` | Recorded run status |

`AgentEventType` union:
`semantic.interpreted`, `mission.planned`, `run.started`, `tool.started`, `tool.completed`, `tool.failed`, `gateway.checked`, `guardian.checked`, `proposal.created`, `approval.required`, `run.completed`, `run.failed`, `run.stopped`.

`AgentRunFixture` additionally carries `fixture_label: "RECORDED_FIXTURE"`, `run_id`, `runtime_identity`, `provider_key`, `model_key`, `recorded_at`, `scenario`, `events`.

### 3.2 AgentRunStep-like tool names

The timeline humanises known tool names (`HUMAN_TOOL` / `TOOL_LABELS` in `AgentRunTimeline.tsx`) and falls back to the raw name:

- `inspect_journey` → "Checking / Checked Journey"
- `inspect_twin` → "Checking / Checked protected commitments"
- `search_city_services` → "Searching / Searched alternatives"
- `request_replan` → "Requesting / Requested replan"
- Long/unknown names are rendered as-is and clipped with ellipsis + `title` (e.g. the stress fixture `citynexus.search_city_services_for_rain_safe_indoor_activity_candidates`).

When merging, map Codex's real tool names onto this label table, or add the new names rather than renaming events.

### 3.3 `runtime_identity` values

`DIRECT`, `HERMES_NATIVE_MCP`, `HERMES_COMPAT_ENDPOINT`, `NATIVE_DEEPSEEK_TOOL_LOOP`, `FALLBACK`, `UNAVAILABLE`.

`RuntimeTruthBadge` renders `execution` (this identity), `semantic` (`DeepSeek`), `truth` (`CityNexus`) and `source` separately, so semantic provider, execution path, and truth owner are never conflated.

### 3.4 `approval.required` / `proposal.created` semantics

- `proposal.created` sets `proposal_id` and usually `run_status: "approval_required"`; the UI shows the proposal summary panel.
- `approval.required` sets `approval_id` + `proposal_id` and is the gate that makes the approval panel non-optional.
- Approval state machine: `proposal_only → approval_required → approved | rejected | review_requested`. `RecoveryDiff` starts at `approval_required` only when `evidence_state === "verified"`, otherwise `proposal_only`; "Approve" is **disabled** unless evidence is verified.
- Decisions are local to the reference app and produce no backend write; the copy states a child PlanVersion would be authoritative in the real runtime ("`Approval recorded by CityNexus · child PlanVersion became authoritative`" exists only inside the recorded fixture text).

### 3.5 Source honesty (`RECORDED_FIXTURE` vs `LIVE`)

Hard rule: **fixture data must never be labelled `LIVE`.**

- Fixtures are constructed with `fixture_label: "RECORDED_FIXTURE"` and every event carries `source: "RECORDED_FIXTURE"`.
- `AgentRunTimeline` emits `data-source` and shows the "RECORDED_FIXTURE · replaying recorded events only · progress never advances on a timer" banner.
- `AgentRunTimeline` only reports `source: "LIVE"` when it is actually driven by `liveEvents` / `liveEventsUrl`.
- `RuntimeTruthBadge` styles fixture source distinctly (amber) and exposes `data-source`.
- `App` shows the reference/isolated pills; the footer says "Isolated CityNexus V18 Experience Lab build · no main-tree mutation".

### 3.6 No backend mutation

- The reference app holds all state in React (`useState`); there is no fetch/write to a backend, no PlanVersion creation, no Gateway/Guardian call.
- What-If replies are tagged `simulation_only · no mutation`.
- Recovery approve/reject only changes local `data-approval-state`.
- The map uses a recorded GeoJSON fixture (`recorded-fixture://route-rain-001`), no tile server.

> 中文：契约以 `AgentRunEvent`、工具名映射、`runtime_identity`、审批事件语义和来源诚实为核心；参考应用只读本地状态，不改后端。

---

## 4. Recommended merge order

1. **Copy the new subtree first.**
   Copy `reference-app/src/**` → `frontend/src/features/experience-lab/**` (mechanical; no existing files touched). Prefer the patch as the transfer record, but review it — treat the patch as a proposal, not `git apply -f`.
2. **Wire the route behind a feature flag.**
   Add the `experience` route entry from §3.1 and mount the lab behind a flag/env check. Do not replace the existing `main.tsx` provider stack.
3. **Run focused Playwright.**
   Mirror `reference-app/tests/*.spec.ts` and `reference-app/playwright.config.ts`; run the acceptance suite against the built output (§6). Fix only genuine merge regressions, not fixture content.
4. **Then decide on style token adoption.**
   `styles/tokens.css` (`--cn-motion-*`, easing, colour palette) is self-contained. Only after the subtree is stable, review whether to adopt these tokens globally instead of scoping them under the feature; check for `.card` / `.timeline` / `.copilot` / `.sheet` collisions (§5) before promoting.
5. **Keep `reference-app/` as the reference.**
   It remains the runnable, screenshot-producing baseline and the source of `evidence/`.

> 中文：推荐顺序为「先拷贝新子树 → 特性开关接入路由 → 跑聚焦 Playwright → 再决定是否全局采用样式令牌」。

---

## 5. Risks & mitigations

| Risk | Why it happens | Mitigation |
| --- | --- | --- |
| **Duplicate `LocaleProvider`** | `reference-app/src/main.tsx` wraps `<App/>` in the lab's own `LocaleProvider`; mounting the subtree inside the main tree's existing i18n provider creates two providers/contexts. | Reuse the main tree provider, or mount the lab only at its own route root. Never nest two `LocaleProvider`s. |
| **Duplicate i18n keys** | The lab ships full `en` and `zh-CN` dictionaries in `i18n.tsx` with names like `pulse.*`, `copilot.*`, `map.*`, `recovery.*`. Merging into the global dictionary can shadow or duplicate existing keys. | Namespace keys under `experienceLab.*` when merging, or keep the lab dictionary internal to the subtree. Diff keys before merging. |
| **CSS class name overlap** | `.card`, `.timeline`, `.copilot`, `.sheet` (plus `.pulse`, `.recovery`, `.bubble`, `.chip`, `.btn`) are generic and may collide with Codex styles. | Scope the stylesheet under a feature root (e.g. `.experience-lab`), or convert to CSS Modules. Audit the colliding selectors before global adoption. |
| **Bundle size from `maplibre-gl`** | `maplibre-gl` is a heavy dependency; the reference build reports `dist/assets/index-*.js` = 1,324.79 kB (gzip 368.69 kB) with a >500 kB warning. | Lazy-load the `experience-lab` route and `MapCanvas`; consider `manualChunks`. Don't ship MapLibre globally for an opt-in feature. |
| **Fixture data labelled `LIVE`** | A careless merge or refactor could flip `source` / `fixture_label`, destroying the truth contract. | Keep `RECORDED_FIXTURE` everywhere except genuinely live event streams; add a regression assertion that `data-source !== "LIVE"` for fixtures. See §3.5. |
| **No `@types/react` in the main tree context** | The isolated lab typechecks with local ambient shims (`src/shims.d.ts`) for `react`, `react-dom/client` and `maplibre-gl`. Main-tree type roots may differ. | If the main tree ships real `@types/react`, **remove/avoid `shims.d.ts`** so it doesn't redeclare modules and break typecheck; otherwise keep the shims local to the subtree. |
| **Two token sources** | Motion durations exist both in `motion.ts` and `tokens.css`. | If adopting tokens globally, generate one from the other or add a test that asserts the values stay in sync. |
| **`reference-app/node_modules` is a symlink** | `reference-app/node_modules -> /d/moodle/CityNexus/frontend/node_modules`; copying the app tree must not follow it. | Copy `src/`, `tests/`, config files and `scripts/` only. Never copy `node_modules`, `dist` or `test-results` into the main tree. |

> 中文：主要风险是重复 Provider/i18n 键、通用 CSS 类名冲突、maplibre 体积、fixture 被误标 LIVE，以及主树类型环境与本地 shim 冲突。

---

## 6. Tests to merge first

Take `reference-app/tests/acceptance.spec.ts` (13 tests) and `reference-app/playwright.config.ts`. Run in the three configured projects.

### 6.1 Acceptance spec tests

| # | Test name |
| --- | --- |
| 1 | desktop shell keeps SYSTEM secondary and Journey Pulse primary |
| 2 | journey page orders Pulse → Today timeline → Live map and keeps detail collapsed |
| 3 | DIRECT What-If creates no Agent run |
| 4 | recorded Hermes run is truthful, approval-gated, and never advances on a timer |
| 5 | failed and stopped runs stay readable; long tool names stay contained |
| 6 | recovery diff explains why, protects commitments, and makes approval distinct |
| 7 | mobile mini composer and bottom sheet surface mission, step, approval |
| 8 | mobile map sheet content changes by 24/55/90 state |
| 9 | Chinese long content stays readable without horizontal overflow |
| 10 | reduced motion keeps state clarity with zero-duration motion |
| 11 | failure and offline states show a useful next action |
| 12 | Copilot is keyboard openable and Escape returns focus |
| 13 | key routes produce no console or page errors |

Tests 1 and 12 are desktop-gated; tests 7 and 8 are mobile-gated. That gating produces the 6 expected skips.

### 6.2 Viewport projects

| Project | Viewport | Device characteristics |
| --- | --- | --- |
| `desktop-chromium` | 1440 × 900 | Desktop Chrome |
| `mobile-chromium` | 390 × 844 | DSF 2, touch, `isMobile` |
| `mobile-large-chromium` | 430 × 932 | DSF 2, touch, `isMobile` |

Config: `fullyParallel: false`, `workers: 1`, `retries: 0`, `timeout: 45_000`, `expect.timeout: 8_000`, dark colour scheme, web server `node scripts/serve-dist.mjs` on `http://127.0.0.1:4179` with `/__health`.

### 6.3 How to run

```bash
cd reference-app
./node_modules/.bin/playwright test tests/acceptance.spec.ts
./node_modules/.bin/playwright test tests/visual.spec.ts
```

`tests/visual.spec.ts` is optional for merging but is what regenerates the screenshot evidence.

> 中文：先合并 acceptance.spec.ts 的 13 个用例与 desktop/mobile/mobile-large 三个视口配置；visual.spec.ts 负责截图证据。

---

## 7. Evidence paths

| Artifact | Path | Content |
| --- | --- | --- |
| Playwright results | `evidence/playwright_results.txt` | 42 executions, 36 passed, 6 skipped (30.0 s) |
| Build / typecheck | `evidence/build_results.txt` | `tsc` PASS; Vite 48 modules; JS 1,324.79 kB (gzip 368.69 kB); CSS 91.17 kB (gzip 14.61 kB) |
| Desktop screenshots | `evidence/screenshots/v18.2-desktop-*.png` | journey, copilot-approval, recovery, map, zh-journey, hermes-unavailable, reduced-motion |
| Mobile screenshots | `evidence/screenshots/v18.2-mobile-*.png` | journey, copilot-current-step, copilot-expanded, recovery, map-24/55/90, zh-journey |
| Test sources | `reference-app/tests/acceptance.spec.ts`, `reference-app/tests/visual.spec.ts` (mirrored in `tests/`) | Acceptance + screenshot generation |
| Test pointer | `tests/README.md` | Explains that the runnable runner lives in `reference-app/` |

(The `evidence/screenshots/` directory contains the 15 `v18.2-*` evidence files for this delivery.)

---

## 8. Non-goals and the explicit safety statement

- Do **not** overwrite, delete, or rewrite files in `D:\moodle\CityNexus`.
- Do **not** run the lab's provider stack or add backend writes when integrating; this is a UI reference.
- Do **not** relabel `RECORDED_FIXTURE` fixtures as `LIVE`.
- Do **not** copy `reference-app/node_modules`, `dist` or `test-results` into the main tree.
- The subtree under `frontend/src/features/experience-lab/**` is a proposal; **Codex reviews and selectively integrates** only the parts that fit the V18.x architecture, runtime contracts and design system.

> 中文：明确禁止覆盖 `D:\moodle\CityNexus`；该参考实现由 Codex 审核后按需、有选择地合并。

---

## V18.2 evidence-state test addition

The reference supports query-driven evidence demos:

- `/?evidence=unresolved#/recovery`
- `/?evidence=stale#/recovery`

Both render the recovery root with `data-evidence-state`, disable **Approve recovery**, and keep the
approval state at `proposal_only` with a clear review/refresh message. Playwright acceptance test
**14 · unresolved and stale evidence block approval with a clear next action** covers both states on
all three viewport projects.
