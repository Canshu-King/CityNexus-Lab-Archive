# Activity Detail truth contract

## Coordinates

Activity Detail must use real Place coordinates when available.

Backend should expose:
- latitude
- longitude
- CRS / provenance if useful

from the related Place row.

Frontend must not invent or hard-code coordinates.

## Cost

Three distinct states:

1. KNOWN FREE
   - `amount_minor = 0`
   - explicit evidence/status says known/free
   - UI: `免费`

2. KNOWN PAID
   - positive amount
   - UI shows currency + amount

3. UNKNOWN
   - no reliable price
   - UI: `暂无价格`

Do not infer unknown merely from zero.

## Nearby

Keep Snapshot L's improvement:
- call a stop "nearby" only when actual coordinates prove it;
- otherwise call it another stop on the trip.

## Map action

If coordinates exist:
- map action enabled;
- opens/selects the exact place.

If coordinates are unavailable:
- disabled with an honest explanation.
