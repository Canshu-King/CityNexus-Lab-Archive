# HERMES RUNTIME TRUTH — V18.2 Family A

**Harness:** `tests/runtime_truth.py` (live HTTP against the isolated backend on 8021)
**Raw results:** `evidence/results_runtime_truth.json`
**Result:** **4 PASS / 2 FAIL**

The question this family answers: *when the V18.2 chain says what runtime it is
on, is the claim earned?*

---

## A1 — `runtime_identity` is computed, never an unproven claim · **PASS**

```
GET /api/v1/agent/runtime-status
{
  "runtime_identity": "NOT_CONFIGURED",
  "native_binary_detected": false,
  "native_mcp_proven": false,
  "mcp_server": "citynexus-v2",
  "deepseek_configured": false,
  "hermes_compat_configured": false,
  "hermes_native_gateway": {
    "configured": false, "reachable": false, "runs": false,
    "events": false, "approval": false, "profile": "citynexus",
    "provider": null, "model": null
  }
}
```

The assertion is not merely "the field exists" but the **invariant**:

> `runtime_identity != "HERMES_NATIVE_MCP"` **OR** `native_mcp_proven == true`

That is the property that matters. `runtime_identity` flips to
`HERMES_NATIVE_MCP` on *reachability* (`binary AND native.ready`), while
`native_mcp_proven` is a separate, explicit flag
(`CITYNEXUS_HERMES_NATIVE_PROVEN`). A product that reported
`HERMES_NATIVE_MCP` while `native_mcp_proven` was false would be claiming a
proven native tool loop on the strength of a reachable socket. In this
environment it correctly reports `NOT_CONFIGURED`, and the invariant holds.

**Corroborating source.** The two places that hard-code
`"runtime_identity": "HERMES_NATIVE_MCP"` (`backend/app/main.py` ~681 and ~7990)
are both guarded by `native_status.get("ready")` **and** sit after a
successful `native.create_run(...)`. They are conditional on a real run being
created, not on a constant. That is defensible. (They would still be stronger
if they asserted the run actually used MCP tools — see the handoff, "nice to
have".)

---

## A2 — `capabilities` must expose `ready` in every branch · **FAIL** (defect F2)

```
GET /api/v1/agent/hermes/capabilities
-> {"configured":false,"reachable":false,"runs":false,"events":false,
    "approval":false,"profile":"citynexus","provider":null,"model":null}

keys = ['approval','configured','events','model','profile','provider','reachable','runs']
                                                                    ^^^^^^^^^
                                                                    no 'ready'
```

**Root cause — `backend/app/integrations/hermes/native_client.py`:**

```python
def native_hermes_status() -> dict[str, Any]:
    configured = bool(...)
    if not configured:
        return {                      # <- early return, NO "ready"
            "configured": False,
            "reachable": False,
            "runs": False,
            "events": False,
            "approval": False,
            "profile": ...,
            "provider": ...,
            "model": ...,
        }
    client = HermesNativeClient()
    try:
        capabilities = client.capabilities()
        return {
            ...
            "ready": capabilities.ready,   # <- "ready" exists ONLY here
            ...
        }
```

The response contract is branch-dependent. A UI or client that gates on
`capabilities["ready"]` gets a `KeyError` in the unconfigured branch, or — if
written defensively — silently treats "key absent" the same as "not ready"
without ever being told. Either way the *absence* of a field is doing the work
that an explicit `false` should do.

**Proposed fix:** add `"ready": False,` to the unconfigured branch. One line.

---

## A3 — unconfigured native proxy endpoints must degrade cleanly · **FAIL** (defect F1)

```
GET  /api/v1/agent/hermes/runs/{any-uuid}                    -> HTTP 500  Internal Server Error
POST /api/v1/journeys/{id}/agent/hermes/runs/{any}/stop      -> HTTP 500  Internal Server Error
GET  /api/v1/agent/hermes/runs/{any-uuid}/events             -> HTTP 200  (empty body, stream aborted)
```

**Root cause — `backend/app/main.py` lines 487–521.** The client is built
**outside** the `try`:

```python
@app.get("/api/v1/agent/hermes/runs/{run_id}")
def get_native_hermes_run(run_id: str) -> dict[str, Any]:
    client = HermesNativeClient()          # <-- line 489, OUTSIDE the try
    try:
        return client.get_run(run_id)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "native Hermes run status is unavailable") from exc
    finally:
        client.close()
```

and the constructor refuses to build when unconfigured
(`native_client.py` lines 36–39):

```python
def __init__(self, *, client: httpx.Client | None = None):
    base_url = getattr(settings, "hermes_native_api_url", None)
    if not base_url or not getattr(settings, "hermes_api_server_key", None):
        raise ValueError("native Hermes API is not configured")
```

So a `ValueError` is raised **before** the handler's own
`except (httpx.HTTPError, ValueError)` can catch it. The handler was written to
turn exactly this condition into a structured `502` — the guard is simply on
the wrong side of the statement it is guarding.

`stop_native_hermes_run` (line 515) has the identical shape.

The events endpoint (line 501) builds the client **inside the generator**, so
the same `ValueError` fires after Starlette has already committed the `200`
status and SSE headers. The client sees `200` with an empty body — a silent
lie rather than a loud one.

**Why it matters.** This is the failure mode the V18.2 task book calls out
directly: the UI polls native run state, Hermes is not configured, and the
product answers with a server error instead of "not configured". A 500 tells
the operator the server is broken. The truth is that the feature is simply off.

**Proposed fix** (handoff §2): hoist construction inside `try`, return
`503` with the standard error envelope, and pre-check
`native_hermes_status()["configured"]` in the SSE handler so it can answer with
a real status code instead of an aborted stream.

**Evidence.** The tracebacks are in `evidence/backend8021_run.log`.

---

## A4 — copilot must not fabricate a native run while Hermes is down · **PASS**

```
POST /api/v1/journeys/{id}/copilot/messages  {"message":"暴雨导致海河游船延误了"}
-> http=200  intent=UNKNOWN  mode=FALLBACK  agent_run=None  event=False
```

The response is honest: no `agent_run` object, no `HERMES_NATIVE_MCP` claim,
`mode: FALLBACK`. The copilot's native-run branch is gated on
`native_status.get("ready")` (`main.py` ~7972), which is false here, so the
branch is skipped entirely.

This is the behaviour that makes A3 worse by contrast: the *product logic*
handles "Hermes is down" correctly, and then a thin proxy layer turns the same
condition into a 500.

---

## A5 — catalogue honesty · **PASS**

`GET /api/v1/agent/tools/v2` declares, per tool, whether it can mutate domain
truth:

| Tool | `mutates_domain_truth` |
|---|---|
| `inspect_journey` | `false` |
| `inspect_twin` | `false` |
| `list_replans` | `false` |
| `search_city_services` | `false` |
| `replace_activity` | `true` |
| `reschedule_activity` | `true` |
| `create_booking` | `true` |
| `cancel_refundable_booking` | `true` |
| `request_commitment_change` | `true` |

All four reads declare `false`; all five typed mutators declare `true`. The
catalogue does not understate what a tool can do.

---

## A6 — unknown tool name is refused · **PASS**

`POST /api/v1/agent/tools/v2/{random-uuid}` returns an error envelope. No
silent success, no fall-through to a default handler.

---

## Summary

| ID | Assertion | Status |
|---|---|---|
| A1 | identity computed, `HERMES_NATIVE_MCP` requires `native_mcp_proven` | PASS |
| A2 | `capabilities.ready` present in every branch | **FAIL** |
| A3 | unconfigured proxies do not 500 | **FAIL** |
| A4 | copilot fabricates no native run | PASS |
| A5 | catalogue declares mutation capability truthfully | PASS |
| A6 | unknown tool refused | PASS |

Both failures are the same two defects V18.1 reported and are still open. Both
are one-to-three-line fixes with no design implications.
