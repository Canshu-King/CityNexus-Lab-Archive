# Mobile consumer gate

Required default-surface behavior:

## Booking
No raw:
- STRUCTURED_JSON
- CONFIRMED enum
- UNKNOWN
- MID_TRIP
- DEPARTURE enum
- manual-entry
unless under Advanced.

## Copilot
Default mission rail:
- human step labels
- human status
- no raw tool_name

## Trips / Activity Detail
Common role/category values are localized:
- check_out -> 退房
- departure -> 出发 / 离开
- museum -> 博物馆
- food -> 美食
- hotel -> 住宿

## Live
If >1 pending proposal:
- visually distinguish alternatives;
OR
- dedupe equivalent proposals.

## Copilot dock
Must not cover:
- AI planning CTA
- booking confirm
- Live proposal
- sheet footer

Test viewports:
- 390x844
- 412x915
- 430x932
