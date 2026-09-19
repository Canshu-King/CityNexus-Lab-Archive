from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import CityService, Journey, Place, ProviderCall, RealPlaceCandidate


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _external_id(provider: str, value: str) -> str:
    return f"{provider}:{value}"[:180]


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class DiscoveryCandidate:
    provider_key: str
    external_id: str
    name: str
    category: str
    latitude: float
    longitude: float
    tags: tuple[str, ...]
    opening_hours: dict[str, Any]
    metadata: dict[str, Any]
    distance_m: float | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "provider_key": self.provider_key,
            "external_id": self.external_id,
            "name": self.name,
            "category": self.category,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "tags": list(self.tags),
            "opening_hours": self.opening_hours,
            "metadata": self.metadata,
            "distance_m": round(self.distance_m, 1) if self.distance_m is not None else None,
        }


class NominatimGeocoder:
    """Small, identified Nominatim client for bounded discovery calls."""

    provider_key = "nominatim"

    def __init__(self, *, client: httpx.Client | None = None, base_url: str | None = None):
        self.client = client or httpx.Client(timeout=settings.real_city_timeout_seconds)
        self.base_url = (base_url or settings.nominatim_url).rstrip("/")
        self._owned_client = client is None

    def search(self, query: str, *, city: str, limit: int) -> list[DiscoveryCandidate]:
        response = self.client.get(
            f"{self.base_url}/search",
            params={
                "q": f"{query}, {city}",
                "format": "jsonv2",
                "limit": min(limit, 10),
                "addressdetails": 1,
            },
            headers={"User-Agent": "CityNexus/6.0 (+https://citynexus.local/real-city)"},
        )
        response.raise_for_status()
        rows = response.json()
        candidates: list[DiscoveryCandidate] = []
        for row in rows:
            try:
                lat = float(row["lat"])
                lon = float(row["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            osm_type = str(row.get("osm_type") or "place")
            osm_id = str(
                row.get("osm_id")
                or row.get("place_id")
                or hashlib.sha1(str(row).encode()).hexdigest()
            )
            category = str(row.get("type") or row.get("class") or "service")
            candidates.append(
                DiscoveryCandidate(
                    provider_key=self.provider_key,
                    external_id=_external_id(self.provider_key, f"{osm_type}/{osm_id}"),
                    name=str(row.get("display_name") or query).split(",")[0],
                    category=category,
                    latitude=lat,
                    longitude=lon,
                    tags=(category, "real_city"),
                    opening_hours={},
                    metadata={"display_name": row.get("display_name"), "osm_type": osm_type},
                )
            )
        return candidates

    def close(self) -> None:
        if self._owned_client:
            self.client.close()


class OverpassPOIProvider:
    """Bounded OSM POI query with a provider-owned, auditable request."""

    provider_key = "overpass"

    def __init__(self, *, client: httpx.Client | None = None, base_url: str | None = None):
        self.client = client or httpx.Client(timeout=settings.real_city_timeout_seconds)
        self.base_url = (base_url or settings.overpass_url).rstrip("/")
        self._owned_client = client is None

    def search(
        self,
        query: str,
        *,
        latitude: float,
        longitude: float,
        radius_m: int,
        limit: int,
    ) -> list[DiscoveryCandidate]:
        requested = query.casefold()
        tags = '"amenity"~"cafe|restaurant|library|arts_centre|theatre|museum"'
        if any(token in requested for token in ("park", "outdoor", "garden")):
            tags = '"leisure"~"park|garden"'
        query_text = (
            f"[out:json][timeout:10];nwr[{tags}](around:{min(radius_m, 5000)},{latitude},{longitude});"
            "out center tags;"
        )
        response = self.client.post(
            f"{self.base_url}/interpreter",
            content=query_text,
            headers={"User-Agent": "CityNexus/6.0 (+https://citynexus.local/real-city)"},
        )
        response.raise_for_status()
        elements = response.json().get("elements", [])
        candidates: list[DiscoveryCandidate] = []
        for row in elements[:limit]:
            tags_data = row.get("tags") or {}
            center = row.get("center") or row
            try:
                lat = float(center["lat"])
                lon = float(center["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            category = str(
                tags_data.get("amenity")
                or tags_data.get("leisure")
                or tags_data.get("tourism")
                or "service"
            )
            name = str(tags_data.get("name") or f"OSM {category}")
            osm_id = f"{row.get('type', 'n')}/{row.get('id')}"
            candidates.append(
                DiscoveryCandidate(
                    provider_key=self.provider_key,
                    external_id=_external_id(self.provider_key, osm_id),
                    name=name,
                    category=category,
                    latitude=lat,
                    longitude=lon,
                    tags=tuple(
                        sorted(
                            {
                                category,
                                "real_city",
                                "indoor" if category not in {"park", "garden"} else "outdoor",
                            }
                        )
                    ),
                    opening_hours={"raw": tags_data.get("opening_hours")}
                    if tags_data.get("opening_hours")
                    else {},
                    metadata={"osm_id": osm_id, "tags": tags_data},
                    distance_m=_distance_m(latitude, longitude, lat, lon),
                )
            )
        return candidates

    def close(self) -> None:
        if self._owned_client:
            self.client.close()


_TIANJIN_REPLAY = (
    DiscoveryCandidate(
        provider_key="openstreetmap-replay",
        external_id="node/281001",
        name="Tianjin Italian Style Town Indoor Gallery",
        category="arts_centre",
        latitude=39.1315,
        longitude=117.2050,
        tags=("culture", "indoor", "real_city", "tianjin"),
        opening_hours={"open": "10:00", "close": "21:00"},
        metadata={"source": "captured_replay", "city": "Tianjin"},
    ),
    DiscoveryCandidate(
        provider_key="openstreetmap-replay",
        external_id="node/281002",
        name="Haihe Riverside Design Library",
        category="library",
        latitude=39.1226,
        longitude=117.1964,
        tags=("culture", "quiet", "indoor", "real_city", "tianjin"),
        opening_hours={"open": "09:30", "close": "20:00"},
        metadata={"source": "captured_replay", "city": "Tianjin"},
    ),
    DiscoveryCandidate(
        provider_key="openstreetmap-replay",
        external_id="node/281003",
        name="Tianjin Ancient Culture Street Tea House",
        category="cafe",
        latitude=39.1530,
        longitude=117.1908,
        tags=("local_food", "indoor", "real_city", "tianjin"),
        opening_hours={"open": "09:00", "close": "22:00"},
        metadata={"source": "captured_replay", "city": "Tianjin"},
    ),
)


def _replay_candidates(query: str, *, limit: int) -> list[DiscoveryCandidate]:
    needle = query.casefold()
    ranked = sorted(
        _TIANJIN_REPLAY,
        key=lambda item: (
            0
            if any(
                token in f"{item.name} {item.category} {' '.join(item.tags)}".casefold()
                for token in needle.split()
            )
            else 1,
            item.name,
        ),
    )
    return list(ranked[:limit])


def materialize_candidates(
    session: Session,
    journey: Journey,
    candidates: list[DiscoveryCandidate],
    *,
    captured_at: str,
    mode: str,
) -> list[dict[str, Any]]:
    expires_at = (
        datetime.fromisoformat(captured_at)
        + timedelta(seconds=settings.real_city_cache_ttl_seconds)
    ).isoformat()
    result: list[dict[str, Any]] = []
    for candidate in candidates:
        distance = candidate.distance_m
        external_id = candidate.external_id
        row = session.scalar(
            select(RealPlaceCandidate).where(
                RealPlaceCandidate.provider_key == candidate.provider_key,
                RealPlaceCandidate.external_id == external_id,
            )
        )
        if row is None:
            row = RealPlaceCandidate(
                id=f"rpc-{hashlib.sha1(f'{candidate.provider_key}|{external_id}'.encode()).hexdigest()[:24]}",
                provider_key=candidate.provider_key,
                external_id=external_id,
            )
            session.add(row)
        row.journey_id = journey.id
        row.city_code = journey.city_code
        row.name = candidate.name
        row.category = candidate.category
        row.latitude = candidate.latitude
        row.longitude = candidate.longitude
        row.tags_json = _json(list(candidate.tags))
        row.opening_hours_json = _json(candidate.opening_hours)
        row.metadata_json = _json({**candidate.metadata, "discovery_mode": mode})
        row.captured_at = captured_at
        row.expires_at = expires_at
        row.distance_m = distance
        row.evidence_json = _json(
            {
                "provider": candidate.provider_key,
                "captured_at": captured_at,
                "ttl_seconds": settings.real_city_cache_ttl_seconds,
                "provenance": "REPLAY" if mode == "replay" else "LIVE_PROVIDER",
            }
        )
        row.status = "DISCOVERED"

        place = session.scalar(
            select(Place).where(
                Place.provider_key == candidate.provider_key,
                Place.external_id == external_id,
            )
        )
        if place is None:
            place = Place(
                id=f"real-place-{hashlib.sha1(f'{candidate.provider_key}|{external_id}'.encode()).hexdigest()[:24]}",
                provider_key=candidate.provider_key,
                external_id=external_id,
                city_code=journey.city_code,
                name=candidate.name,
                category=candidate.category,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                opening_hours_json=_json(candidate.opening_hours),
                tags_json=_json(list(candidate.tags)),
                metadata_json=_json({**candidate.metadata, "discovery_mode": mode}),
                updated_at=captured_at,
            )
            session.add(place)
        else:
            place.city_code = journey.city_code
            place.name = candidate.name
            place.category = candidate.category
            place.latitude = candidate.latitude
            place.longitude = candidate.longitude
            place.opening_hours_json = _json(candidate.opening_hours)
            place.tags_json = _json(list(candidate.tags))
            place.metadata_json = _json({**candidate.metadata, "discovery_mode": mode})
            place.updated_at = captured_at
        session.flush()
        row.materialized_place_id = place.id
        service = session.scalar(
            select(CityService).where(
                CityService.provider_key == candidate.provider_key,
                CityService.external_id == f"service:{external_id}",
            )
        )
        if service is None:
            session.add(
                CityService(
                    id=f"service-{hashlib.sha1(f'{candidate.provider_key}|{external_id}'.encode()).hexdigest()[:24]}",
                    provider_key=candidate.provider_key,
                    external_id=f"service:{external_id}",
                    place_id=place.id,
                    city_code=journey.city_code,
                    service_type=candidate.category,
                    name=candidate.name,
                    availability_json=_json(candidate.opening_hours),
                    metadata_json=_json(candidate.metadata),
                    updated_at=captured_at,
                )
            )
        result.append({**candidate.payload(), "id": place.id, "materialized_place_id": place.id})
    session.flush()
    return result


def capture_real_city_candidates(
    session: Session,
    journey: Journey,
    *,
    query: str,
    radius_m: int = 2500,
    limit: int = 8,
    mode: str = "replay",
) -> dict[str, Any]:
    captured_at = _now()
    mode = mode.lower()
    requested_mode = mode
    provider_status: dict[str, Any]
    candidates: list[DiscoveryCandidate]
    if mode == "live":
        live_error: str | None = None
        candidates = []
        if not settings.real_city_enabled:
            live_error = "REAL_CITY_DISABLED"
        else:
            geocoder = NominatimGeocoder()
            poi = OverpassPOIProvider()
            try:
                candidates = geocoder.search(query, city=journey.city_code, limit=limit)
                if not candidates:
                    candidates = poi.search(
                        query,
                        latitude=39.12,
                        longitude=117.20,
                        radius_m=radius_m,
                        limit=limit,
                    )
                provider_status = {
                    "nominatim": "CAPTURED",
                    "overpass": "CAPTURED"
                    if candidates and candidates[0].provider_key == "overpass"
                    else "NOT_NEEDED",
                }
            except (httpx.HTTPError, KeyError, TypeError, ValueError, AttributeError) as exc:
                live_error = type(exc).__name__
            finally:
                geocoder.close()
                poi.close()
        if live_error or not candidates:
            candidates = _replay_candidates(query, limit=limit)
            mode = "replay-fallback"
            provider_status = {
                "nominatim": "REPLAY_FALLBACK",
                "overpass": "REPLAY_FALLBACK",
                "fallback_reason": live_error or "LIVE_NO_RESULTS",
            }
    else:
        candidates = _replay_candidates(query, limit=limit)
        provider_status = {
            "nominatim": "REPLAY_NOT_CALLED",
            "overpass": "REPLAY_NOT_CALLED",
            "openstreetmap_replay": "CAPTURED",
        }
    request_payload = {
        "query": query,
        "city_code": journey.city_code,
        "radius_m": radius_m,
        "limit": limit,
        "mode": mode,
        "requested_mode": requested_mode,
    }
    session.add(
        ProviderCall(
            id=f"pc-{hashlib.sha1(f'real-city|{journey.id}|{_json(request_payload)}'.encode()).hexdigest()[:24]}",
            provider_key=(
                "openstreetmap-replay"
                if mode in {"replay", "replay-fallback"}
                else "real-city-provider-mesh"
            ),
            operation="discover_city_services",
            request_json=_json(request_payload),
            response_json=_json({"providers": provider_status, "count": len(candidates)}),
            status="SUCCESS",
            latency_ms=0,
            created_at=captured_at,
        )
    )
    materialized = materialize_candidates(
        session, journey, candidates, captured_at=captured_at, mode=mode
    )
    return {
        "journey_id": journey.id,
        "city_code": journey.city_code,
        "city_context": "Tianjin-oriented replay"
        if mode in {"replay", "replay-fallback"}
        else journey.city_code,
        "mode": mode,
        "captured_at": captured_at,
        "expires_at": (
            datetime.fromisoformat(captured_at)
            + timedelta(seconds=settings.real_city_cache_ttl_seconds)
        ).isoformat(),
        "provider_status": provider_status,
        "provenance": "REPLAY" if mode in {"replay", "replay-fallback"} else "LIVE_PROVIDER",
        "candidates": materialized,
    }
