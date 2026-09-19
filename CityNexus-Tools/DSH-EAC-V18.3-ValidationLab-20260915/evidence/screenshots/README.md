# evidence/screenshots/ — capture status

**Status: PENDING live capture.**

This directory is required by `OUTPUT_CONTRACT.md` (Stream F, Web/Mobile Truth).
Live screenshots at the four required viewports could **not** be captured during
this lab because the isolated backend `:8022` was down — the same upstream
"Service is too busy" condition that stalled the live harness.

All Stream-F checks were instead performed **source-level** against
`source-snapshot/frontend/src` (see `DESKTOP_MOBILE_A11Y_RESULTS.md`):
keyboard `:focus-visible`, ARIA roles, `prefers-reduced-motion`, long-text
wrapping, and no-horizontal-overflow all verified; one defect (**F3**,
`.v8-runtime-card` missing CSS) identified.

## How to populate this directory (next responsive window)

```bash
cd D:/moodle/CityNexus-Tools/DSH-EAC-V18.3-ValidationLab-20260915
python tests/_run_backend_foreground.py            # bring :8022 up
cd source-snapshot/frontend && npm run dev          # :5173
python tests/capture_a11y_screenshots.py            # writes the 4 PNGs below
```

Expected outputs once captured:
- `desktop_1440x900.png`
- `desktop_1280x720.png`
- `mobile_390x844.png`
- `mobile_430x932.png`

Each should be inspected for: run timeline, stopped/failed/offline pills, approval
gate, keyboard focus ring, reduced-motion behaviour, long bilingual text wrapping,
and absence of horizontal overflow.
