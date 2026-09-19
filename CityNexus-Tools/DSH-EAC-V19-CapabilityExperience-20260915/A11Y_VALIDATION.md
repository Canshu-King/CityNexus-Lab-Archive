# A11Y Validation — V19 Capability Experience

Date: 2026-09-15
Reference app: `reference-app/`
Test config: `tests/playwright.config.ts`
Test spec: `tests/capability-experience.spec.ts`

## 1. Automated gates

| Gate | Result | Evidence |
| --- | --- | --- |
| TypeScript feature package | PASS | `evidence/build_results.txt` |
| Production Vite build | PASS | `evidence/build_results.txt` |
| Playwright suite | 7/7 passed | `evidence/playwright-results.txt` |
| Axe automated scan | 0 violations at 1280×900 | `evidence/playwright-results.txt` |
| Patch apply check against main tree | PASS for all four patches | `evidence/patch_apply_check.txt` |

## 2. Coverage

The Playwright spec covers:

1. Desktop surfaces, source honesty, and unknown-evidence language.
2. Mobile 390×844 and 430×932 capability shield with a reachable primary
   action and an explicit evidence gap.
3. Keyboard operation: quick chip toggle with Space, advanced disclosure with
   Enter, scenario switching with Enter.
4. HARD conflict and no-capability honesty: known stairs conflict, unverified
   Candidate B, no protected-capability claim when there are no needs.
5. 320px narrow viewport, 200% CSS zoom shell, English locale switch, and
   reduced-motion computed duration.
6. Live adapter honesty: selecting `LIVE_ADAPTER` and running the live check
   reports `unavailable`/`error` and does not silently substitute fixture data.
7. Axe accessibility scan of the full lab surface at 1280×900.

## 3. Specific checks

- **Unknown evidence**: every `[data-evidence-state="NEEDS_LIVE_EVIDENCE"]`
  badge is asserted not to contain `✓`.
- **Focus**: interactive elements use visible `:focus-visible` outlines.
- **Wide desktop/1440**: the first desktop test additionally renders and
  screenshots at 1440×900 after the 1280×720 pass.
- **Touch targets**: mobile primary action is asserted to be at least 44px high
  and contained within the viewport.
- **Reduced motion**: after `page.emulateMedia({ reducedMotion: "reduce" })`,
  transition duration is asserted to be effectively zero.
- **200% stress**: body zoom is set to 200% and horizontal document overflow is
  asserted to be at most 4px.
- **Non-color distinction**: evidence states use glyphs, border styles, and text,
  not colour alone.

## 4. Honest limits

- Automated axe findings are necessary but not sufficient. Manual screen reader
  validation with NVDA/VoiceOver/JAWS, real zoom, and low-bandwidth mobile
  testing remain recommended before production release.
- The reference app is a fixture lab; live backend responses may introduce
  additional state combinations not represented by the five scenarios.
- The copied frontend snapshot does not include `@types/react`. The feature
  package is therefore type-checked with a typecheck-only ambient React shim
  (`reference-app/src/types/react-shims.d.ts`). The production Vite build does
  not use the shim.
