# AUTONOMOUS CYCLE 5 — Extreme input and repeated dock toggling never break the surface

## Hypothesis
Extreme input and repeated dock toggling never break the surface

## Method
Submit a very long Copilot question, then toggle the Copilot dock eight times.
Driver: `D:\moodle\_v1922_work\lab5.cjs` (Playwright + Chrome, 390x844, locale zh-CN).
Raw probe output: `evidence/LAB_PROBE_RESULTS.json`.

## Evidence
The long input survived and the dock stayed mounted after 8 rapid toggles, with 0 page errors.

## Verdict
NOT_REPRODUCIBLE

## Fix
No code change required — the product already behaves correctly.

## Residual risk / what a real user trial should watch
Emoji-only and mixed-script input is worth a dedicated pass.
