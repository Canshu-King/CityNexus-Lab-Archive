# REMAINING_PRODUCT_GAPS.md

## Blocking a READY verdict

1. **The full same-Xiamen visible-browser chain was not completed.**
   `docs/CONSUMER_SHIP_GATE.md` requires create → AI request → candidates →
   select plan → multi-day itinerary → activity detail → hotel compare/select →
   itinerary still preserves day structure → booking import → Copilot → map →
   start/live → explicit mutable POI disruption → material replan → accept,
   all through visible UI with no API substitution.
   `VISIBLE_UI_TRACE.json` is therefore absent.
2. **Consumer booking import is not built.** Trips → 预订 still exposes a JSON
   workbench. Required: paste booking text / manual form → parsed preview with
   editable fields → explicit confirm, with raw JSON behind Advanced.
3. **Today / Live / Me cleanup is partial.** `/v8/me` still shows 权限边界 and
   ADVISORY as primary content; Today still leads with generic copy
   ("你的下一座城市，已被充分考虑") rather than current-trip state.
4. **Material implementation of the ten reference screens remains partial.**
5. **Budget advisory is missing.**

## Important, not blocking

6. **Live hotel → recovery acceptance not driven.** The calendar and identity
   work is verified offline; the live run needs a stable provider.
7. **Public Overpass reliability.** Mirrors time out under load. The provider now
   honours the environment proxy by default, which should help on the user's
   Mihomo network, but a self-hosted endpoint would be more reproducible.
8. **Stay price unknown** (OSM has no rates) and **Chinese stay names often
   generic**.
9. **Map tiles blocked on this network**; the map renders real coordinates and
   degrades to a readable canvas.

## Closed this round

* **Stay Calendar V2** — all three independent findings fixed:
  transition travel to/from pinned boundaries is reserved; an activity keeps its
  original local date (no silent cross-day compaction); overlapping pinned truth
  is rejected explicitly as `STAY_PINNED_CONFLICT`.
* **Superseded-property structural operations** — switching hotel no longer runs
  the previous property's luggage-drop / check-in / night / check-out alongside
  the new one.
* **Configurable public-provider network policy** — `trust_env=False` replaced by
  `CITYNEXUS_PROVIDER_NETWORK_MODE` (`auto` / `env_proxy` / `direct`), defaulting
  to proxy-aware, suitable for the user's Mihomo environment.
* **Activity Detail truthfulness** — "附近" is now only used when a stop is
  actually within 1.5 km; otherwise the copy says plainly that the stops are
  other stops on the same trip and not necessarily walkable.

## Explicitly out of scope

No V19.3/V20 architecture work.
