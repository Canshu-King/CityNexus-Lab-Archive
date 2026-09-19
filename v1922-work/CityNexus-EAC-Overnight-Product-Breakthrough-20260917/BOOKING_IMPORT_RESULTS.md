# BOOKING_IMPORT_RESULTS.md

## Before

Trips → 预订 rendered the **raw structured-JSON workbench** on the golden path.
A normal traveller was asked to paste reservation JSON.

## After

The consumer flow is now the primary experience:

| Entry | Behaviour |
| --- | --- |
| 粘贴确认信息 | paste a confirmation; deterministic parsing extracts reference and times, then shows a draft |
| 手动填写 | **new** manual form: type / title / confirmation number / from / to / departs / arrives / amount |
| 确认截图 | image upload (existing scanner) feeding the same draft flow |
| Preview | draft with extracted fields, plus editable anchor role / departure / arrival |
| Confirm | commit only after explicit confirmation |
| Raw JSON | moved behind a **高级 / 开发者** disclosure |

Both entries post through the same authoritative
`POST /journeys/{id}/inbox/import` path, so manual entry lands in the identical
preview → confirm flow rather than a parallel shortcut.

## Manual form fields

```
type         航班 / 火车 / 酒店 / 门票 / 预订
title        e.g. 厦门航空 MF8102
reference    confirmation number
from / to    origin and destination
departs      local datetime
arrives      local datetime
amount       CNY, optional
```

Unknown values stay `null` and surface as unresolved fields in the draft, so the
traveller sees exactly what still needs attention before confirming.

## Verified in a real browser

390x844, Chinese locale, one Xiamen journey:

```
open-bookings-tab   200
manual-tab-present  yes
manual-form-open    opened
preview-draft       shown
ERRORS: 0
```

Backend confirmation (same journey):

```
POST /inbox/import -> 201
extracted: {reservation_type: FLIGHT, title: 厦门航空 MF8102,
            confirmation_ref: MF8102ABC, origin: 厦门, destination: 北京,
            scheduled_departure_at: 2026-11-06T14:00:00+08:00,
            scheduled_arrival_at:   2026-11-06T16:30:00+08:00,
            amount_minor: 128000, currency: CNY}
```

Screenshots: `screenshots/after/B1_manual_form.png`,
`screenshots/after/B2_manual_preview.png`.

## Honest limitations

* The commit step was exercised through the existing confirm endpoint; a full
  browser-driven **confirm → booking appears in Trips** assertion was not
  completed in this round.
* Screenshot/OCR extraction depends on the existing scanner and a live AI
  provider; when unavailable the UI keeps the deterministic text/manual paths
  and does not fabricate an extraction.
