# V18.3 Patch Contract

The merge contract requires four independently reviewable patches. Each patch
adds files under a new, self-contained subtree and avoids replacing the main
router, `main.tsx`, `LocaleProvider`, or the app shell wholesale.

| Patch | Contents | Depends on | Conflict risk | Optional |
| --- | --- | --- | --- | --- |
| `01_RUNTIME_ADAPTERS.patch` | `frontend/src/features/experience-lab/adapters/**` | none (pure TS, no React DOM) | low — new directory | no |
| `02_EXPERIENCE_COMPONENTS.patch` | components, routes, capability/a11y features, types, i18n additions, `App.tsx` reference wiring | 01 | medium — duplicate i18n keys, `.card`/`.timeline` class overlaps, CSS module scope | no |
| `03_MOTION_TOKENS.patch` | `motion.ts`, motion tokens, scoped experience CSS, reduced-motion rules | none | low — tokens are `--cn-*` namespaced; CSS is `@scope(.citynexus-experience)` | no |
| `04_PWA_MOBILE_OPTIONAL.patch` | `public/manifest.webmanifest`, `public/v18.3-sw.js`, `src/pwa/**`, optional Vite config, optional Playwright viewports | none, but only useful with 02 | low — new files + opt-in `VITE_ENABLE_PWA=1` | yes |

Recommended order:
1. `01_RUNTIME_ADAPTERS.patch`
2. `03_MOTION_TOKENS.patch`
3. `02_EXPERIENCE_COMPONENTS.patch`
4. `04_PWA_MOBILE_OPTIONAL.patch` (only if the product wants PWA registration now)

Do not apply all four blindly if the host worktree has diverged; use
`CODEX_MERGE_GUIDE_V18_3.md` to decide what is directly portable, what needs a
manual port, and what should not be merged.

Honesty rules are non-negotiable: recorded data is always `RECORDED_FIXTURE`,
offline data is always `OFFLINE`, and only real backend responses may show
`LIVE`.
