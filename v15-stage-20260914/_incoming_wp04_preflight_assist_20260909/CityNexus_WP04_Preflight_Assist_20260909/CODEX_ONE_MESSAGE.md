# One-message handoff for Codex

Finish your current pre-WP04 WP03 repair first and make its stop gate fully green. Then use this assist package; do **not** redesign WP04 and do **not** repeat analysis already captured here.

Read only:

1. `CODEX_WP04_START_INSTRUCTION.md`
2. `10_WP04_WORK_PACKAGE.md`
3. `11_INTEGRATION_PATCH_MAP.md`

Then execute WP04A -> WP04G with the supplied scaffold/reference code/tests.

Mandatory first WP04 action: one read-only lookup of the frozen v0.4.2 YAML for exact `commitment_strength` and `commitment_source_type`; do not guess values. Use `tools/extract_wp04_domain_enums.py` / `tools/apply_wp04_scaffold.py` where applicable.

Do not spend quota on SHA/file/package hash checking. Do not start frontend, real providers, AI, JourneyTwin, events/replanning, Visio, or WP05. First full WP04 green checkpoint -> STOP and package repo-relative code/tests/results for GPT review.
