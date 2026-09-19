# A. Isolated Native Hermes E2E — DSH-EAC V18.3 Validation Lab

**Status: PASS** — full isolated native-Hermes path proven end-to-end against a throwaway runtime. No authoritative DB was mutated.

## 1. Objective

Prove the real isolated chain:

```
Copilot → DeepSeek SemanticEnvelope → HERMES_NATIVE_MCP → Hermes Runs/SSE
→ real CityNexus MCP tool → Gateway / Guardian → proposal / result
```

Using only isolated resources: backend port `:8022`, Hermes gateway `:8653`
(profile `citynexus-harness-lab`), isolated SQLite `citynexus_lab.db`, and a
**read-only** copy of the Codex worktree under `source-snapshot/`.

## 2. Isolated stack

| Resource | Value | Notes |
|---|---|---|
| Backend | `http://127.0.0.1:8022` | throwaway uvicorn, isolated venv |
| Hermes gateway | `http://127.0.0.1:8653` | profile `citynexus-harness-lab` |
| DB | `citynexus_lab.db` (SQLite) | throwaway, no authoritative writes |
| Source | `source-snapshot/` | read-only copy of `D:\moodle\CityNexus` |
| Main tree | `D:\moodle\CityNexus` | **NOT modified** (verified) |

The DeepSeek provider was configured at the process scope
(`provider: deepseek, default: deepseek-v4-flash`). The native Hermes gateway
was reachable and reported `ready: true` for the harness profile.

## 3. Seven-gate acceptance

| Gate | Expectation | Observed | Result |
|---|---|---|---|
| G1 gateway reachable | `:8653` responds | `ready: true`, profile `citynexus-harness-lab` | PASS |
| G2 real run_id | a Hermes run_id is minted | `run_5f16fa6087354f5cb021903ccda7b28e` | PASS |
| G3 native identity | `runtime_identity == HERMES_NATIVE_MCP` | confirmed on every event | PASS |
| G4 SSE tool event | at least one real tool call over SSE | 18 real tool events | PASS |
| G5 gateway sees tool | the gateway recorded the tool invocation | yes (hermes_tool_sequences.jsonl) | PASS |
| G6 result from throwaway DB | result reads from `citynexus_lab.db` | yes | PASS |
| G7 no authoritative mutation | `D:\moodle\CityNexus` untouched | verified, mtime unchanged | PASS |

## 4. Run evidence

- **Run id:** `run_5f16fa6087354f5cb021903ccda7b28e`
- **Events:** 19 total, **18 real tool events**.
- **Tool names observed (real, from SSE):** `inspect_journey`, `inspect_twin`,
  `list_replans`, `request_replan`, `search_city_services`, `tool_call`,
  `tool_describe`.
- **Prompt (natural language):** *"The metro is suspended after a signal failure
  and I will miss my next activity. Search indoor alternatives and produce a
  replan proposal, but do not mutate anything."*
- **Semantic envelope (DeepSeek):** intent `REPLAN_REQUEST`, assertion
  `ASSERTED`, effective time `NOW`, event type `TRAFFIC_DELAY`,
  requested action `REQUEST_REPLAN`, confidence 0.9.
- **Constraints carried:** `indoor_only=true`, `no_mutation=true`,
  `walking_minutes_max=25`, interests `culture` + `local_food`.
- **Result:** a replan proposal was returned without any authoritative mutation
  — the `no_mutation` constraint was honoured end-to-end.

Full event capture: `evidence/native_e2e_run.json`
(first-run success). A parallel failed run under DeepSeek 503
(`native_e2e_run_failed_503.json`) is retained for regression coverage — it shows
the harness degrades cleanly (no partial write) when the LLM is unavailable.

## 5. Verdict

The native Hermes E2E path is **proven against an isolated runtime**. All seven
gates pass. The Codex-owned main tree was never touched. This is the foundational
gate for every other stream in this lab.

## 6. Reproduction

```bash
cd D:/moodle/CityNexus-Tools/DSH-EAC-V18.3-ValidationLab-20260915
python tests/start_hermes_gateway.py      # :8653, profile citynexus-harness-lab
python tests/_run_backend_foreground.py   # :8022, isolated db
python tests/run_native_e2e.py            # emits evidence/native_e2e_run.json
```

> Note: live re-run requires the DeepSeek endpoint to be responsive. During this
> lab the upstream returned "Service is too busy" intermittently; the one
> successful native E2E run captured above was taken on a responsive window.
