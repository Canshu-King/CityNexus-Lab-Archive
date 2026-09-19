# CityNexus Autonomous City Intelligence V3 Test Results

Captured on 2026-09-11 from `D:\moodle\CityNexus` using the repository
`.venv`, serial execution where the shared SQLite demo database is involved.

| Gate | Result |
| --- | --- |
| Backend full regression | **308 passed, 2 skipped, 2 warnings** in 51.57s |
| Focused V3 / Agent / Impact / Solver suites | **87 passed, 2 warnings** in 23.60s |
| Solver V2 pure + integrated gates | **36 passed, 2 warnings** in the combined Solver run |
| MCP V1/V2 unit and real stdio protocol | **6 passed** |
| OpenAPI formal/runtime parity | **52 / 52**, missing 0, extra 0 |
| `python -m compileall -q backend agent-mcp` | PASS |
| Ruff check (backend and MCP) | PASS |
| Ruff format check (backend and MCP) | PASS; 147 files formatted |
| frontend `npm run build` | PASS; existing large MapLibre chunk warning |
| frontend `npm run test:e2e` | **4 passed** with one worker |
| Secret-shaped assignment scan | PASS; no matches in package scope |
| DeepSeek model-backed CityNexus loop | **PASS**; transient credential only |
| Literal Hermes CLI model E2E | **EXTERNAL_BOUNDARY**; Hermes binary/provider not installed |
| Fresh final-ZIP extraction | **PASS**; 2,173 files, forbidden entries 0, backend 308/2, MCP 6, OpenAPI 52/52 |

Intentional skips:

- The optional OR-Tools-missing boundary is skipped because OR-Tools is
  installed in this environment.
- The live Valhalla smoke is skipped because
  `CITYNEXUS_LIVE_VALHALLA_URL` is not configured.

The two backend warnings are dependency deprecations from the installed
FastAPI/Starlette/httpx test stack. The frontend build warning is the existing
large bundle advisory and is not a test failure.

## Live model evidence

The supplied temporary DeepSeek credential was loaded into a child process
environment for the real smoke only. It was not printed, persisted, copied to
the frontend, written to audit payloads, or included in the final ZIP.

The model selected its own CityNexus inspection, planning, search, replan, and
acceptance calls for the Chinese mission. The AgentRun/tool trace persisted and
reloaded, and the protected Commitment remained intact. The run is reported as
`MODEL_BACKED` CityNexus orchestration plus `PROTOCOL_VERIFIED` MCP V2; it is
not labeled Hermes CLI E2E.
