# C. Runtime / API Contract Findings — DSH-EAC V18.3 Validation Lab

**Status: F1 RESOLVED in current snapshot · F2 OPEN (source-confirmed)**

## 1. Checks executed (C1–C10)

| Id | Check | Result |
|---|---|---|
| C1 | `/runtime/status` | 200 — `runtime_identity=HERMES_NATIVE_MCP`, `native_binary_detected=true`, `native_mcp_proven=false` |
| C2 | `/capabilities` (configured) | 200 — `has_ready_key=true` |
| C3 | global unknown run (F1) | **502** `REQUEST_ERROR` (not 500) ✅ |
| C4 | journey unknown run (F1) | **502** `REQUEST_ERROR` ✅ |
| C5 | stop unknown run (F1) | **502** `REQUEST_ERROR` ✅ |
| C6 | SSE unknown global | peer closed, no fake terminal ✅ |
| C7 | SSE unknown journey | peer closed, no fake terminal ✅ |
| C8 | copilot contract | 200 — returns conversational envelope (no run_id injected) ✅ |
| C9 | plans generate (seeded) | 201 — `CANDIDATE` plan returned ✅ |
| C10 | `/health` | 200 — `ai=enabled` ✅ |

## 2. Defect F1 — native Hermes unconfigured → bare 500 (RESOLVED)

**Prior state (V18.2):** requesting an unknown native-Hermes run returned a bare
`500` with an unhandled exception.

**Current snapshot:** `GET`/`POST`/`STOP` on an unknown run now return **502**
with a structured envelope:

```json
{
  "error": {
    "code": "REQUEST_ERROR",
    "message": "native Hermes run status is unavailable",
    "trace_id": "2dcf3585-2a84-49fb-957c-669d89452951"
  }
}
```

**Root cause (fixed):** the Hermes native client is now constructed **inside**
the `try` block in `source-snapshot/backend/app/main.py:491`. A misconfigured/
unreachable native gateway therefore raises a caught `REQUEST_ERROR` → 502,
never an uncaught 500.

**Verdict: RESOLVED** in the current snapshot.

## 3. Defect F2 — capabilities unconfigured branch missing `ready` key (OPEN)

**Location:** `source-snapshot/backend/app/integrations/hermes/native_client.py`
:: `native_hermes_status()`.

**Symptom:** the **unconfigured** branch returns
`configured / reachable / runs / events / approval / stop / profile / provider / model`
but **omits `ready`**. Consumers that read `caps['ready']` (e.g. a UI gate or a
readiness probe) raise `KeyError` specifically in the unconfigured state, while
the configured branch (C2) correctly includes `ready: true`.

**Why it matters:** this is a latent crash path that only triggers when native
Hermes is *not* configured — exactly the state the lab exercises for isolation.

**Recommended one-line fix:**

```python
# in the unconfigured branch of native_hermes_status()
"ready": False,
```

**Verdict: OPEN** — source-confirmed, low-risk, well-isolated.

## 4. Runtime truth notes

- `runtime_identity = HERMES_NATIVE_MCP` is reported consistently across
  status, runs, and SSE — the "native" claim is declared.
- `native_mcp_proven = false` is **honest**: the stack declares the native
  identity but does not yet carry an independent proof token. This is the
  correct truthful state; it is *not* a defect, just a maturity flag the UI
  should surface rather than hide.
- SSE endpoints fail closed (peer-closed, no synthetic terminal event) on
  unknown runs — no false "completed" events can be manufactured.

## 5. Artifacts

- `evidence/api_contract.json` — raw per-check payloads.
- `tests/run_api_contract.py` — re-runnable contract checker.
- `evidence/results.json` — aggregated stream C summary.
