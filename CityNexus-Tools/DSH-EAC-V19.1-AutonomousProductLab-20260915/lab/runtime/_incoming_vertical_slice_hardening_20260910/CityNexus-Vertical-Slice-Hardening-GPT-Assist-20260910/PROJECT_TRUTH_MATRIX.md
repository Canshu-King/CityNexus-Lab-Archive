# CityNexus Project Truth Matrix after 2026-09-10 Vertical Slice Review

| Area | Current truth | Evidence / qualification | Next bounded action |
|---|---|---|---|
| Prior 5 Post-Goal defects | Repaired in checkpoint | Existing 5-test gate passes; full backend replays after fixture reconstruction | Keep regression tests |
| Backend Golden Scenario | Real backend/database flow | Plan -> booking -> CAPTURE -> C4 -> start -> Event -> replan -> accept -> Twin | Harden execution progression to actual disrupted Activity |
| React backend connection | Real | `/api/v1` API client and backend reload exist | Merge hardening and rerun build/E2E |
| Playwright | Backend-connected, not mere UI smoke | Watches Event/Replan/Accept/Twin calls | Add semantic assertions for current Activity and F3 evidence |
| localStorage | Acceptable | Journey ID only | Keep Domain truth server-side |
| F3 Event time | Prior naive-time defect repaired | Existing test passes | Also normalize aware UTC to Journey timezone |
| F3 origin | Incorrect in checkpoint | Previous slot used instead of current execution Activity | Merge current-execution origin patch |
| Currency display | Incorrect in checkpoint UI | Minor units formatted as major units | Convert minor -> major before display |
| Idempotency scope | Too broad in frontend demo | Journey-scoped keys can conflict across multiple operations | Scope by booking/event/proposal |
| Checkpoint reproducibility | Incomplete | Fresh extraction lacks required backend-relative schema/fixtures | Package exact repo-relative support files and fresh-extract test |
| MobilitySnapshot core | Good foundation | Frozen snapshot accepted by deterministic gate | Thread sourced snapshot into runtime operations |
| Valhalla runtime authority | Not yet integrated | Adapter/smoke foundation exists; product runtime still uses Mock directly | Next provider gate after hardening freeze |
| Open-Meteo adapter | Good foundation | Unix/UTC parsing repaired | Map provider risk deterministically to Journey Activity/time interval |
| OR-Tools | Foundation/optional | Must remain candidate generator only | Defer until provider/runtime gate is frozen |
| AI / LiteLLM / DeepSeek | Optional | Deterministic fallback foundation exists | Defer; verified facts only |
| Visio | Historical advanced work | Not current highest-value blocker | Do not reopen routing now |
| Software Engineering coursework | On track conceptually | Real product can now generate stronger implementation/test evidence | Feed software evidence into PPT/SRS later |
