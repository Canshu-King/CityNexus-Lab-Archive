# CityNexus V18.2 DeepSeek Harness EAC Experience Build Lab

Isolated Web + Mobile reference experience for the CityNexus DeepSeek + Native
Hermes product. **No file under `D:\moodle\CityNexus` was modified.**

## Deliverables

| Path | Purpose |
| --- | --- |
| `reference-app/` | Self-contained React 19 + TypeScript + Vite + MapLibre reference app (source + production `dist/`) |
| `docs/` | Experience report and design/merge handoff documents |
| `patches/V18_2_EXPERIENCE_REFERENCE.patch` | Reference merge patch: new `frontend/src/features/experience-lab/**` subtree plus illustrative `v8Routes.ts` / `main.tsx` hunks |
| `tests/` | Mirrored focused Playwright specs (runnable from `reference-app/`) |
| `evidence/screenshots/` | Desktop / mobile / Chinese / reduced-motion / approval screenshots |
| `evidence/build_results.txt` | Typecheck + production build evidence |
| `evidence/playwright_results.txt` | Full three-viewport acceptance run |

## What the reference demonstrates

- Journey Pulse: NOW / NEXT / RISK / PRIMARY ACTION, with technical detail collapsed.
- Traveler-first desktop shell: TODAY / PLAN / TRAVEL / SYSTEM, SYSTEM secondary and collapsible.
- Persistent Copilot Dock with semantic interpretation, runtime truth, agent activity, proposal and approval.
- Reusable `AgentRunTimeline` supporting semantic → mission → run → tools → gateway → guardian → proposal → approval → completion/failure/stop, with `RECORDED_FIXTURE` honesty.
- Runtime identities `DIRECT`, `HERMES_NATIVE_MCP`, `FALLBACK`, `UNAVAILABLE` plus failure/offline status states.
- Recovery before/after diff with WHY, protected commitments, time/cost/walking deltas and evidence state.
- Mobile Today / Map / Copilot / Wallet / Me, persistent mini composer, Copilot bottom sheet, map sheet 24% / 55% / 90%.
- Motion tokens (90/160/220/420/650 ms), View Transition API, MapLibre camera contract, reduced-motion support.
- Chinese / English layout stress, keyboard access, focus-visible, 44px touch targets, safe-area insets.

## Run locally

`reference-app/node_modules` is a local junction to the read-only Codex worktree
`D:\moodle\CityNexus\frontend\node_modules` used only for local build/test. The
deliverable also contains `reference-app/dist`, so the built app can be served
without installing dependencies:

```bash
cd reference-app
node scripts/serve-dist.mjs
# open http://127.0.0.1:4179
```

## Honesty rules

Every recorded run, proposal and recovery scenario is marked `RECORDED_FIXTURE`.
The UI never displays a fixture as `LIVE`. Agent progress is derived from events;
replay uses `requestAnimationFrame` and never `setTimeout`/`setInterval`.
