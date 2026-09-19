# V18.2 focused tests

These files mirror `reference-app/tests/`. The runnable Playwright project lives in
`reference-app/` because that is where `playwright.config.ts`, `scripts/serve-dist.mjs`,
and the production `dist/` are located.

```bash
cd ../reference-app
./node_modules/.bin/playwright test tests/acceptance.spec.ts
./node_modules/.bin/playwright test tests/visual.spec.ts
```

Three projects are configured:

- `desktop-chromium` — 1440×900
- `mobile-chromium` — 390×844
- `mobile-large-chromium` — 430×932

Results: `evidence/playwright_results.txt`.
