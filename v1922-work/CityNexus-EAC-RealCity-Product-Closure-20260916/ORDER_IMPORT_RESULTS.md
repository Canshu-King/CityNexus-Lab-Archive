# ORDER_IMPORT_RESULTS.md — consumer order import

## Required consumer flow

`EAC_NEXT_MISSION.md` requires order import as a **traveler** flow and says raw
Reservation JSON must move out of the ordinary Trips experience:

```
upload screenshot if supported / paste confirmation text / manual entry
-> parsed preview
-> user confirmation
-> create booking/commitment
```

with the rule: *never create a commitment from uncertain extraction without
confirmation*.

## What exists in the product now

The workflow is mounted under **Trips → 预订**, and the raw JSON path is
labelled as an advanced/developer input rather than being the primary surface:

| Capability | Status |
| --- | --- |
| Paste a confirmation / reservation payload and preview it | **present** (existing inbox workbench) |
| Explicit review step before anything is written | **present** — the draft is listed as `READY_FOR_CONFIRMATION` and only then confirmed |
| Confirm creates the booking/commitment through the existing backend path | **present** |
| Screenshot / barcode capture | **present but not driven live** — `BookingArtifactScanner` decodes into the same review flow |
| Manual entry | **via the same structured input** — a guided form was not built |
| Raw JSON moved to an advanced surface | **partially** — it is now a sub-tab (`预订`) rather than the default Trips screen, but it still exposes a JSON textbox to ordinary users |

## Honest status

**NOT CLOSED.** The mission asks for a consumer-grade entry
(paste confirmation *text*, manual entry, parsed preview, confirm) rather than a
JSON box. Today the user is still asked to paste structured JSON, and no
guided manual form exists.

What **is** true and was verified earlier in the project:

* a draft is never silently committed — the state machine requires
  `READY_FOR_CONFIRMATION` before `confirm`;
* a failed or duplicate confirmation returns a deterministic 409 and never
  creates a second commitment;
* concurrent confirmations converge on one reservation identity.

## Why it was not finished this round

The round's time went to the three gaps the audit called blocking —
same-journey Xiamen continuity, real hotel compare/select, and live
disruption → governed replan — plus the four identity/evidence defects that the
driven run exposed. Order import is genuinely *usable* but not yet
*consumer-quality*, and saying otherwise would repeat the exact over-claim this
Road-Prep was created to catch.

## Next step

Build the guided entry: paste-text parser → parsed reservation preview with the
extracted fields editable → explicit confirm. Keep the raw JSON path behind the
drawer's developer section.
