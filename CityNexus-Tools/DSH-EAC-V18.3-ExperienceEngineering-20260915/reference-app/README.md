# CityNexus V18.2 Experience Reference App

Self-contained React 19 + TypeScript + Vite + MapLibre reference implementation for
the CityNexus DeepSeek + Native Hermes product experience.

## Run the built reference

```bash
node scripts/serve-dist.mjs
# http://127.0.0.1:4179
```

`dist/` is committed so no dependency installation is required just to view the
reference. Deep links use hash routes, e.g.:

- `/#/journey`
- `/#/map`
- `/#/copilot`
- `/#/recovery`
- `/?locale=zh#/journey`
- `/?runtime=hermes_unavailable#/journey`

## Rebuild

`node_modules` is a local junction to the read-only Codex worktree
`D:\moodle\CityNexus\frontend\node_modules` used only for local build/test. It is
excluded from the delivery zip.

```bash
./node_modules/.bin/tsc --noEmit   # uses local minimal react shims
./node_modules/.bin/vite build
```

## Test

```bash
./node_modules/.bin/playwright test tests/acceptance.spec.ts
./node_modules/.bin/playwright test tests/visual.spec.ts
```

Three projects: 1440×900 desktop, 390×844 mobile, 430×932 mobile-large.

## Honesty

All recorded runs/proposals/recovery scenarios are labelled `RECORDED_FIXTURE`.
Agent progress is event-derived; replay uses `requestAnimationFrame`, never
`setTimeout`/`setInterval`. No backend or main worktree mutation occurs.
