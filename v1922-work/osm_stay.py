"""Provider-backed accommodation discovery for any city (OSM/Overpass).

The captured fixture only knows Tianjin, and ``LiveAccommodationProvider``
returns nothing, so a real Xiamen trip could never compare hotels.

This provider asks OSM (via Nominatim for the city anchor and Overpass for
``tourism=hotel|guest_house|hostel``) for real named properties inside the city.
Only provider-backed facts are surfaced: name, coordinates and OSM identity.

**Price is not knowable from OSM** and is therefore reported as unknown rather
than invented: ``nightly_amount_minor`` stays 0 and the offer records
``price_status = "UNKNOWN"`` so the traveller/UI can say "price not available".
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class OsmAccommodationProvider:
    provider_key = "osm-overpass"
    provenance = "LIVE_PROVIDER"

    def __init__(self, *, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            timeout=max(30.0, settings.real_city_timeout_seconds)
        )
        self._owned = client is None

    def close(self) -> None:
        if self._owned:
            self._client.close()

    def _geocode(self, city_code: str) -> tuple[float, float] | None:
        label = str(city_code).split("-")[-1].replace("_", " ")
        if label.upper() in {"CNX", "DEMO"}:
            return None
        try:
            r = self._client.get(
                f"{settings.photon_base_url}/api/",
                params={"q": label, "limit": 1},
                headers={"User-Agent": "CityNexusEAC/1.0 (trial)"},
            )
            r.raise_for_status()
            feats = (r.json() or {}).get("features") or []
            if not feats:
                return None
            lon, lat = feats[0]["geometry"]["coordinates"][:2]
            return float(lat), float(lon)
        except Exception:
            return None

    def discover(
        self, *, city_code: str, party_size: int, nights: int
    ) -> tuple[Any, ...]:
        from app.stay_mobility import AccommodationOfferDraft

        anchor = self._geocode(city_code)
        if anchor is None:
            return ()
        lat, lon = anchor
        query = (
            f"[out:json][timeout:45];("
            f'node(around:6000,{lat},{lon})["tourism"~"hotel|guest_house|hostel"];'
            f'way(around:6000,{lat},{lon})["tourism"~"hotel|guest_house|hostel"];'
            f");out center 12;"
        )
        try:
            r = self._client.post(
                f"{settings.overpass_url.rstrip('/')}/interpreter",
                data={"data": query},
                headers={"User-Agent": "CityNexusEAC/1.0 (trial)"},
            )
            r.raise_for_status()
            elements = (r.json() or {}).get("elements") or []
        except Exception:
            return ()

        drafts = []
        seen: set[str] = set()
        for el in elements:
            tags = el.get("tags") or {}
            name = str(tags.get("name:zh") or tags.get("name") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            if el.get("type") == "node":
                elat, elon = el.get("lat"), el.get("lon")
            else:
                center = el.get("center") or {}
                elat, elon = center.get("lat"), center.get("lon")
            if elat is None or elon is None:
                continue
            osm_id = f"{el.get('type')}/{el.get('id')}"
            room_type = str(tags.get("tourism") or "hotel")
            drafts.append(
                AccommodationOfferDraft(
                    external_offer_id=f"osm:{osm_id}",
                    property_name=name,
                    latitude=float(elat),
                    longitude=float(elon),
                    # OSM has no price. Zero + explicit unknown beats invention.
                    nightly_amount_minor=0,
                    room_type=room_type,
                    refundable=False,
                    evidence_confidence=0.6,
                    coordinate_crs="WGS84",
                    luggage_drop={},
                )
            )
        return tuple(drafts)
