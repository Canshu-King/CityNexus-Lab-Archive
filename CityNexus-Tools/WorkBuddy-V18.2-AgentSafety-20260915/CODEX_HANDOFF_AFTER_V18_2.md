# CODEX HANDOFF — after V18.2 Agent Safety & Black-Box

**Run:** 2026-09-15, 01:36 – 01:55 CST
**Isolation:** `D:\moodle\CityNexus` was **never written to**. All work happened
in `D:\moodle\CityNexus-Tools\WorkBuddy-V18.2-AgentSafety-20260915\`.
**Ports used:** backend **8021**, frontend **4173**. Codex's 8000/5173 were
verified down for the whole run.

---

## 1. Headline

The authority boundary is **solid** — 49 adversarial cases (22 live + 27
deterministic), zero escapes, zero mutations. Three **truthfulness /
presentation** defects found, all small and local:

| # | Severity | Defect | File |
|---|---|---|---|
| F1 | High | Unconfigured native-Hermes proxy endpoints return bare **500** | `backend/app/main.py` ~487–521 |
| F2 | Medium | `capabilities` omits **`ready`** in the unconfigured branch | `backend/app/integrations/hermes/native_client.py` ~157–172 |
| F3 | Medium | `.v8-runtime-card` has **no CSS** → identity and caveat merge into one line | `frontend/src/styles.css` |

**F1 and F2 are the same defects V18.1 reported (there as F1/F2). They are
still open.** V18.2 reproduced both with live, repeatable assertions.

### Re-verified against the live main tree (01:53 CST)

The main tree was **being edited while this lab ran** (`backend/app/agent/
mission.py`, `native_client.py`, `runtime_events.py`, `gateway.py`, `main.py`,
`mission_plan.py`, `frontend/src/api/citynexus.ts` all changed between 01:39
and 01:51). All three findings were therefore re-checked against the **live**
`D:\moodle\CityNexus`, not just the 01:36 snapshot:

| Defect | Live main tree at 01:53 | Still present? |
|---|---|---|
| **F1** | `get_native_hermes_run` L490–497: `client = HermesNativeClient()` on L491, **outside** the `try` | **YES** |
| **F1** | `stop_native_hermes_run` L680–689: `client = HermesNativeClient()` on L683, **outside** the `try` (moved from L511 — Codex is actively editing this area) | **YES** |
| **F2** | `native_hermes_status()` L172–183: the unconfigured branch gained a new **`"stop": False`** field but **still has no `"ready"`** | **YES** |
| **F3** | `grep -rn "v8-runtime-card" --include=*.css frontend/src` → no matches | **YES** |

So all three are live, not stale. Note the line numbers below will drift as
Codex continues editing — search by symbol name, not by line.

---

## 2. Proposed production fixes (not applied)

### Fix F1 — hoist client construction inside `try`

`backend/app/main.py`, three handlers. The handler already knows how to turn
this condition into a structured error; the guard is simply on the wrong side
of the statement it guards.

```python
# ---- GET /api/v1/agent/hermes/runs/{run_id}  (currently ~line 487) ----
@app.get("/api/v1/agent/hermes/runs/{run_id}")
def get_native_hermes_run(run_id: str) -> dict[str, Any]:
    try:
        client = HermesNativeClient()          # moved INSIDE the try
        try:
            return client.get_run(run_id)
        finally:
            client.close()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, "native Hermes is not configured") from exc


# ---- POST /journeys/{journey_id}/agent/hermes/runs/{run_id}/stop  (~line 511) ----
@app.post("/api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}/stop")
def stop_native_hermes_run(journey_id: UUID, run_id: str,
                           session: Session = Depends(get_session)) -> dict[str, Any]:
    require(session, Journey, str(journey_id), "Journey")
    try:
        client = HermesNativeClient()          # moved INSIDE the try
        try:
            return client.stop(run_id)
        finally:
            client.close()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, "native Hermes is not configured") from exc
```

**SSE endpoint** (`~line 498`) needs a different treatment: the exception is
raised *inside the generator*, after Starlette has committed `200` + SSE
headers, so the client sees `200` with an empty body. Check before streaming:

```python
@app.get("/api/v1/agent/hermes/runs/{run_id}/events")
def stream_native_hermes_events(run_id: str) -> StreamingResponse:
    if not native_hermes_status().get("configured"):
        raise HTTPException(503, "native Hermes is not configured")

    def events():
        client = HermesNativeClient()
        try:
            for item in client.iter_events(run_id):
                yield f"data: {json.dumps(item, ensure_ascii=False, sort_keys=True)}\n\n"
        finally:
            client.close()

    return StreamingResponse(events(), media_type="text/event-stream")
```

*Note on the status code:* the existing handlers use `502` for
"unavailable". `503 Service Unavailable` is arguably more accurate for
"not configured", but either is fine — the important part is that it is a
structured envelope, not an unhandled `ValueError`.

### Fix F2 — add `ready` to the unconfigured branch

`backend/app/integrations/hermes/native_client.py`, `native_hermes_status()`:

```python
    if not configured:
        return {
            "configured": False,
            "reachable": False,
            "runs": False,
            "events": False,
            "approval": False,
            "ready": False,          # <-- add this line
            "profile": getattr(settings, "hermes_native_profile", "citynexus"),
            "provider": getattr(settings, "hermes_native_provider", None),
            "model": getattr(settings, "hermes_native_model", None),
        }
```

The configured branch already returns `ready`; this makes the contract
branch-independent.

### Fix F3 — style the runtime-truth card

`frontend/src/styles.css`. The class currently has **no rule at all**
(`grep -rn "v8-runtime-card" --include=*.css frontend/src` → no matches).
Mirror what `.v8-intel-facts` already does:

```css
.v8-runtime-card { margin-top: 18px; }
.v8-runtime-card span,
.v8-runtime-card b,
.v8-runtime-card small { display: block; }
.v8-runtime-card span { color: #b9c7dc; font-size: 10px; letter-spacing: .08em; }
.v8-runtime-card b { margin: 6px 0 4px; font-size: 15px; }
.v8-runtime-card small { color: #8fa7d3; font-size: 10px; line-height: 1.5; }
```

### Nice to have (not a defect)

`backend/app/main.py` ~681 and ~7990 hard-code
`"runtime_identity": "HERMES_NATIVE_MCP"`. Both are guarded by
`native_status.get("ready")` **and** sit after a successful
`native.create_run(...)`, so the claim is conditional on a real run — that is
defensible. It would be stronger still to assert the run actually invoked an
MCP tool, rather than that it was created. No action required.

---

## 3. Applying the test patch

```bash
cd D:\moodle\CityNexus
git apply --check path\to\patches\V18_2_TESTS_ONLY.patch   # verified clean
git apply          path\to\patches\V18_2_TESTS_ONLY.patch
```

Adds six files under `tests/v18_2_agent_safety/`. **Tests only** — no
production file is touched, so applying it cannot change behaviour.

| File | Kind | Needs |
|---|---|---|
| `test_authority_matrix.py` | pure / offline | repo on `sys.path` |
| `blackbox_agent_safety.py` | live HTTP | running backend + its sqlite path |
| `runtime_truth.py` | live HTTP | running backend |
| `semantic_boundary.py` | live HTTP + offline | backend + repo path |
| `multistep_agent.py` | live HTTP | running backend |
| `frontend_runtime_truth.mjs` | Playwright | frontend URL + `@playwright/test` |

---

## 4. Re-running the lab

```bash
# backend (isolated; loads repo_copy/backend on the authoritative venv)
cd <lab>\repo_copy\backend
CITYNEXUS_AI_ENABLED=false CITYNEXUS_DB_PATH=<lab>\citynexus_v182.db \
  <CityNexus>\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8021

# frontend (isolated; /api/v1 -> 8021)
cd <lab>\frontend
node node_modules/vite/bin/vite.js --config vite.v182-local.config.ts --port 4173

# suites
python tests/test_authority_matrix.py --repo repo_copy/backend
python tests/blackbox_agent_safety.py --base-url http://127.0.0.1:8021 --db citynexus_v182.db
python tests/runtime_truth.py         --base-url http://127.0.0.1:8021
python tests/semantic_boundary.py     --base-url http://127.0.0.1:8021 --repo repo_copy/backend --db citynexus_v182.db
python tests/multistep_agent.py       --base-url http://127.0.0.1:8021
node   tests/frontend_runtime_truth.mjs --base http://127.0.0.1:4173
```

`evidence/backend8021_run.log` contains the F1 tracebacks.

---

## 5. Gotchas discovered (save yourself the debugging)

1. **`POST /journeys/{id}/plans/generate` → 500 on an empty `Place` catalogue.**
   `MobilitySnapshotCaptureError: mobility fact unavailable for
   place-city-park|place-river-cruise`. The planner needs the demo places, so
   `POST /api/v1/demo/reset` **must** run first. Creating a journey by hand and
   generating a plan fails. Worth turning into a `422` with a clear message.

2. **`request_replan` / `accept_replan` require an ACTIVE journey**
   (`409 journey must be ACTIVE with an active plan`). Call
   `POST /journeys/{id}/start` first — but **after** creating any Booking:
   booking creation requires the journey to be pre-ACTIVE. Order matters:
   `reset → generate → select → booking → start → event → request_replan`.

3. **Re-issuing a gated call with an `approval_id` needs a fresh
   `request_id`.** Re-using the original returns
   `409 same agent request id used for a different request`, because the
   idempotency key binds `request_id → fingerprint` and attaching an approval
   changes the fingerprint. Correct, but easy to misread as a bug.

4. **The executed path runs the feasibility gate; the gated path does not.**
   So an adversarial case can target any time (it is gated before feasibility),
   but a positive-control execute must stay inside the journey window or it
   fails with `JOURNEY_END_BY_EXCEEDED, JOURNEY_WINDOW_EXCEEDED`. Use the
   activity's own `start_at`/`end_at`.

5. **`/api/v1/health` reports `"ai":"disabled"`** regardless of the real AI
   state. Do not trust it as a readiness probe for the agent stack.

6. **ESM ignores `NODE_PATH`.** The Playwright harness resolves
   `@playwright/test` via `createRequire(join(ROOT,"frontend","package.json"))`
   against the junctioned `node_modules`.

7. **`node_modules` junction must be made with PowerShell
   `New-Item -ItemType Junction`.** `cmd /c mklink /J` from Git Bash splits the
   drive letter and fails with `无效开关 - "moodle"`.

8. **Vite background processes die with the shell that started them.** Use a
   managed background task, not a trailing `&`.

---

## 6. What was NOT verified

- **Native Hermes end-to-end.** The gateway profile pins MCP to
  `http://127.0.0.1:8000` (Codex's authoritative backend). Triggering a real
  native run would have written the authoritative database, so it was not
  triggered. **The `DeepSeek → router → HERMES_NATIVE_MCP → Hermes Runs/SSE →
  MCP V2 → Gateway → Timeline` chain is therefore still unproven end-to-end.**
  It needs a dedicated run against a throwaway backend, or a gateway profile
  pointed at an isolated port. This remains the single largest open question in
  the V18.x line.
- **Approval expiry.** Requires clock manipulation; the TTL is visible in the
  DB (`expires_at = created_at + 10 min`).
- **Full pytest.** Explicitly out of scope per the task book. The 27-case
  authority matrix is new and targeted, not a re-run.
- **V13–V17.** Not re-audited.

---

## 7. Suggested next steps

1. Apply the three fixes (≈15 lines total) and re-run
   `tests/runtime_truth.py` + `tests/frontend_runtime_truth.mjs` — both should
   go fully green.
2. Close the native-Hermes E2E gap with a throwaway backend so the chain can be
   exercised without touching the authoritative DB.
3. Turn the empty-catalogue `500` into a `422` with an actionable message.
