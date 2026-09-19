# CityNexus V18.3 Test Results

Current convergence evidence is recorded in `reports/product-v18-3/`.

| Gate | Result |
| --- | --- |
| V18.3 focused correctness and experience tests | **9 passed** |
| V18.2/V18.1/V17/V16/V15/V14 regression gates | **Passed** |
| Broad backend regression | **429 passed, 2 skipped, 2 warnings** |
| Frontend production build | **PASS; MapLibre isolated into lazy chunk** |
| Desktop/mobile Playwright | **PASS; 1280/1440 desktop, 390/430 mobile, 320 sanity** |
| Native Hermes proof | **PROVEN; real MCP tool events and truthful Stop/unavailable states** |

No test result is inferred from a fixture run, and no credential value is
printed, persisted, or packaged.
