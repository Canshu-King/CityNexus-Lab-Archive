# Phone Trial Flow — 390×844 and 430×932

Isolated lab: backend `127.0.0.1:8060`, frontend `127.0.0.1:4213`, built from `snapshot_a`
(V19.2). Distinct ports from Codex (8000/5173), the V19 lab (8040/4193) and the V19.1 lab
(8050/4203). The frontend's `node_modules` is a junction to the main tree — no copy, nothing
written.

Driver: `tools/v191_web_mobile.mjs`, system Chrome via Playwright, proxy forced direct.
Evidence: `evidence/web_mobile_results.json`, `web_mobile_summary.json`,
`web_mobile_zoom200.json`, `web_mobile_focus.json`, `web_mobile_capability.json`,
`evidence/screenshots/` (64 PNGs).

Coverage: 8 routes (`hub`, `live`, `map`, `studio`, `bookings`, `agent`, `authoritative`, `twin`)
× 4 viewports (`mobile-390x844`, `mobile-430x932`, `desktop-1280x720`, `desktop-1440x900`)
× reduced-motion on/off = **64 cells**.

---

## Summary

| Metric | Value |
|---|---|
| Cells loaded | **64 / 64** |
| Screenshots captured | 64 |
| Distinct screens | 16 |
| **Page errors** | **0** |
| **Horizontal overflow cells** | **0** |
| 200 % zoom horizontal overflow | **0** (all 8 routes; `scrollWidth == clientWidth == 640`) |
| Colour-only status nodes | **0** |
| Cells rendering capability vocabulary | 32 |
| Keyboard focus visible | ✅ `outline: 3px solid` on every focused control |
| Nameless status nodes | 248 (≈1 per cell) |
| Unlabelled controls | 40 (≈0.6 per cell) |
| Clipped text nodes | 24 |

**The phone shell itself is in good shape.** At both mandated viewports the layout is clean, no
route overflows horizontally at 100 % or 200 % zoom, no route raises a page error, status is
never conveyed by colour alone, and keyboard focus is visibly indicated.

## Live-authority check

The probe drives the real backend, not fixtures:

```
clear                        → 200   items=0 hard=0
declare_hard_unknown_evidence → 200   items=1 hard=1
anyRouteShowsCapability      → true
anyRouteShowsEvidenceState   → true
```

A declared HARD capability is persisted through the real API and **some route renders both the
capability and its evidence state** — the phone is not fabricating a happy path. This is the
V19.1 round's `UNKNOWN != ACCESSIBLE` requirement holding on the client side.

## Accessibility gaps (not trial-blocking)

| Gap | Count | Note |
|---|---|---|
| Nameless status nodes | 248 | status regions without an accessible name |
| Unlabelled controls | 40 | interactive controls without an accessible label |
| Clipped text nodes | 24 | text truncated without an affordance |

These are quality items, not blockers. They should be fixed before a public release, not before
a supervised shadow trial.

## What this does *not* cover

The phone shell renders correctly, but the flows it drives are the same backend flows measured in
the rest of this round. The three blocking defects therefore propagate to the phone unchanged:

1. **No plan can be generated for a journey with a confirmed reservation** — `generate` returns
   422 (`C4_ANCHOR_AND_IDEMPOTENCY_RESULTS.md`). On a phone this looks like "no plans available"
   with no explanation.
2. **A HARD accessibility need declared mid-trip changes nothing** — no replan, no review prompt
   (`MIDTRIP_AND_STALE_LIFECYCLE_RESULTS.md`). The phone shows a healthy running trip.
3. **A journey can be started and kept running on expired provider evidence**, and
   `/experience` does not flag it (`MIDTRIP_AND_STALE_LIFECYCLE_RESULTS.md`).

A real-phone shadow trial would therefore be walking around a city with a phone that:
cannot produce a plan if the traveller has a ticket, does not react when they declare a need,
and does not warn when its mobility facts have expired.

## Not attempted (out of scope for this round)

- Real payment. Explicitly excluded by the road-prep.
- Native Android packaging / APK.
- PWA secure-context install check — the lab serves over plain HTTP on `127.0.0.1`, which Chrome
  treats as a secure context, so a service-worker install path is available but was not exercised.
- SSE reconnect under a real flaky network.

## Reproduction

```
cd D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915
# servers must be running first (two independent background tasks)
python tools/start_web_lab.py          # writes the vite config and the node_modules junction
# then, if the launcher's children have exited:
#   backend : uvicorn app.main:app --host 127.0.0.1 --port 8060   (cwd snapshot_a/backend)
#   frontend: node node_modules/vite/bin/vite.js --config vite.v192-local.config.ts --port 4213
node tools/v191_web_mobile.mjs
```

Note: the host runs a system proxy, so `curl` to `127.0.0.1` needs `--noproxy '*'`, and the
browser is launched with the proxy disabled.
