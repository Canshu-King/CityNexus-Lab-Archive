# Shadow Integration Contract

Create a timestamped isolated snapshot of the current main tree.

Recommended lab runtime:

- backend: 8052
- frontend: 4202
- isolated SQLite DB
- isolated Vite cache
- no writes to main worktree

The goal is to integrate the EAC capability experience against the ACTUAL current
V19 API rather than only recorded fixtures.

Required source modes:

- `LIVE_SHADOW`
- `RECORDED_FIXTURE`
- `OFFLINE_STALE`

Rules:

- `LIVE_SHADOW` can only display data returned by the isolated live backend.
- `RECORDED_FIXTURE` must be visibly labelled.
- `OFFLINE_STALE` must preserve last-known data plus freshness timestamp.
- No source may silently fall through to another source while retaining the old label.
- Unknown evidence remains unknown.
- The selected Journey ID comes from actual application state, never a hardcoded demo ID.

If the current backend contract differs from the previous EAC proposed routes,
adapt to the current contract rather than forcing the product to match the lab.

Produce a mapping document:
`LIVE_CAPABILITY_CONTRACT_MAP.md`
