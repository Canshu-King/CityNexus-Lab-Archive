"""City planning profiles for cities without captured provider data.

The V9 stay/mobility planner reads ``data/v9/city_operations.json``, which
contains exactly two captured cities: ``CN-TIANJIN`` and ``CN-BEIJING``.  For
every other city :func:`app.stay_mobility.city_fixture` returns ``{}``, and the
consequences were severe and silent:

* ``CapturedAccommodationProvider.discover`` returned no offers, so
  ``generate_stay_options`` produced **zero** plan options.  A traveller who
  created a three-day Fuzhou journey got an empty product.
* ``_city_center`` fell back to ``(0.0, 0.0)`` — Null Island, in the Gulf of
  Guinea — so any place the planner did invent sat 12,000 km from the hotel.
* ``POST /plans/generate`` raised ``MobilitySnapshotCaptureError`` and returned
  HTTP 500, because the legacy template composer captured mobility for
  hard-coded demo place ids before checking whether those places existed.

This module makes the product degrade honestly instead of failing:

* :data:`CITY_CENTRES` holds real city centres (an objective fact) for a broad
  set of destinations, including county-level ones, so geometry is never
  invented.
* :func:`derive_generic_profile` builds a **template** city profile — generic
  POI *categories* and indicative stay rates — and marks it
  ``provenance="DERIVED_GENERIC"``.  Every synthesised place carries
  ``cost_status="UNKNOWN"`` or ``"ESTIMATED"``, never ``KNOWN``, so nothing
  downstream can mistake a template for captured provider truth.
* :func:`resolve_city_profile` prefers a captured fixture whenever one exists.

Nothing here writes to the database and nothing here is allowed to be presented
as captured evidence.
"""

from __future__ import annotations

from typing import Any, Iterable

__all__ = [
    "CITY_CENTRES",
    "DERIVED_GENERIC",
    "CAPTURED_REPLAY",
    "resolve_city_profile",
    "derive_generic_profile",
    "city_centre",
    "city_scale",
]

DERIVED_GENERIC = "DERIVED_GENERIC"
CAPTURED_REPLAY = "CAPTURED_REPLAY"

#: Real city centres.  ``scale`` drives how many template POIs are offered:
#: a county town does not have a metro and should not be given a metro-shaped
#: day.  Hong Kong, Macao and Taipei are recorded with a ``CN-`` prefix because
#: they are parts of China, not separate countries.
CITY_CENTRES: dict[str, dict[str, Any]] = {
    # ── Mainland China ────────────────────────────────────────────────────
    "CN-BEIJING": {"latitude": 39.9042, "longitude": 116.4074, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-SHANGHAI": {"latitude": 31.2304, "longitude": 121.4737, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-GUANGZHOU": {"latitude": 23.1291, "longitude": 113.2644, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-SHENZHEN": {"latitude": 22.5431, "longitude": 114.0579, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-CHENGDU": {"latitude": 30.5728, "longitude": 104.0668, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-CHONGQING": {"latitude": 29.5630, "longitude": 106.5516, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-HANGZHOU": {"latitude": 30.2741, "longitude": 120.1551, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-WUHAN": {"latitude": 30.5928, "longitude": 114.3055, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-XIAN": {"latitude": 34.3416, "longitude": 108.9398, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-NANJING": {"latitude": 32.0603, "longitude": 118.7969, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-TIANJIN": {"latitude": 39.1240, "longitude": 117.2050, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "metro", "metro": True},
    "CN-QINGDAO": {"latitude": 36.0671, "longitude": 120.3826, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "city", "metro": True},
    "CN-XIAMEN": {"latitude": 24.4798, "longitude": 118.0894, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "city", "metro": True},
    "CN-FUZHOU": {"latitude": 26.0745, "longitude": 119.2965, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "city", "metro": True},
    "CN-KUNMING": {"latitude": 24.8801, "longitude": 102.8329, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "city", "metro": True},
    "CN-HARBIN": {"latitude": 45.8038, "longitude": 126.5349, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "city", "metro": True},
    "CN-SANYA": {"latitude": 18.2528, "longitude": 109.5119, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "city", "metro": False},
    "CN-LHASA": {"latitude": 29.6520, "longitude": 91.1721, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "city", "metro": False},
    "CN-DALI": {"latitude": 25.6065, "longitude": 100.2676, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "county", "metro": False},
    "CN-LIJIANG": {"latitude": 26.8721, "longitude": 100.2299, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "county", "metro": False},
    "CN-WUYUAN": {"latitude": 29.2476, "longitude": 117.8618, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "county", "metro": False},
    "CN-SHAXIAN": {"latitude": 26.3963, "longitude": 117.7927, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "county", "metro": False},
    "CN-XIAPU": {"latitude": 26.8859, "longitude": 120.0054, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "county", "metro": False},
    "CN-DUNHUANG": {"latitude": 40.1421, "longitude": 94.6618, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "county", "metro": False},
    "CN-PINGYAO": {"latitude": 37.1892, "longitude": 112.1746, "timezone": "Asia/Shanghai", "currency": "CNY", "scale": "county", "metro": False},
    "CN-HONGKONG": {"latitude": 22.3193, "longitude": 114.1694, "timezone": "Asia/Hong_Kong", "currency": "HKD", "scale": "metro", "metro": True},
    "CN-MACAO": {"latitude": 22.1987, "longitude": 113.5439, "timezone": "Asia/Macau", "currency": "MOP", "scale": "city", "metro": True},
    "CN-TAIPEI": {"latitude": 25.0330, "longitude": 121.5654, "timezone": "Asia/Taipei", "currency": "TWD", "scale": "metro", "metro": True},
    # ── Rest of the world ─────────────────────────────────────────────────
    "GB-LONDON": {"latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London", "currency": "GBP", "scale": "metro", "metro": True},
    "GB-EDINBURGH": {"latitude": 55.9533, "longitude": -3.1883, "timezone": "Europe/London", "currency": "GBP", "scale": "city", "metro": False},
    "FR-PARIS": {"latitude": 48.8566, "longitude": 2.3522, "timezone": "Europe/Paris", "currency": "EUR", "scale": "metro", "metro": True},
    "DE-BERLIN": {"latitude": 52.5200, "longitude": 13.4050, "timezone": "Europe/Berlin", "currency": "EUR", "scale": "metro", "metro": True},
    "IT-ROME": {"latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome", "currency": "EUR", "scale": "metro", "metro": True},
    "ES-MADRID": {"latitude": 40.4168, "longitude": -3.7038, "timezone": "Europe/Madrid", "currency": "EUR", "scale": "metro", "metro": True},
    "NL-AMSTERDAM": {"latitude": 52.3676, "longitude": 4.9041, "timezone": "Europe/Amsterdam", "currency": "EUR", "scale": "city", "metro": True},
    "RU-MOSCOW": {"latitude": 55.7558, "longitude": 37.6173, "timezone": "Europe/Moscow", "currency": "RUB", "scale": "metro", "metro": True},
    "TR-ISTANBUL": {"latitude": 41.0082, "longitude": 28.9784, "timezone": "Europe/Istanbul", "currency": "TRY", "scale": "metro", "metro": True},
    "JP-TOKYO": {"latitude": 35.6762, "longitude": 139.6503, "timezone": "Asia/Tokyo", "currency": "JPY", "scale": "metro", "metro": True},
    "JP-OSAKA": {"latitude": 34.6937, "longitude": 135.5023, "timezone": "Asia/Tokyo", "currency": "JPY", "scale": "metro", "metro": True},
    "JP-KYOTO": {"latitude": 35.0116, "longitude": 135.7681, "timezone": "Asia/Tokyo", "currency": "JPY", "scale": "city", "metro": True},
    "KR-SEOUL": {"latitude": 37.5665, "longitude": 126.9780, "timezone": "Asia/Seoul", "currency": "KRW", "scale": "metro", "metro": True},
    "SG-SINGAPORE": {"latitude": 1.3521, "longitude": 103.8198, "timezone": "Asia/Singapore", "currency": "SGD", "scale": "metro", "metro": True},
    "MY-KUALALUMPUR": {"latitude": 3.1390, "longitude": 101.6869, "timezone": "Asia/Kuala_Lumpur", "currency": "MYR", "scale": "metro", "metro": True},
    "TH-BANGKOK": {"latitude": 13.7563, "longitude": 100.5018, "timezone": "Asia/Bangkok", "currency": "THB", "scale": "metro", "metro": True},
    "VN-HANOI": {"latitude": 21.0278, "longitude": 105.8342, "timezone": "Asia/Ho_Chi_Minh", "currency": "VND", "scale": "city", "metro": False},
    "ID-BALI": {"latitude": -8.4095, "longitude": 115.1889, "timezone": "Asia/Makassar", "currency": "IDR", "scale": "county", "metro": False},
    "AE-DUBAI": {"latitude": 25.2048, "longitude": 55.2708, "timezone": "Asia/Dubai", "currency": "AED", "scale": "metro", "metro": True},
    "IN-DELHI": {"latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata", "currency": "INR", "scale": "metro", "metro": True},
    "US-NEWYORK": {"latitude": 40.7128, "longitude": -74.0060, "timezone": "America/New_York", "currency": "USD", "scale": "metro", "metro": True},
    "US-SANFRANCISCO": {"latitude": 37.7749, "longitude": -122.4194, "timezone": "America/Los_Angeles", "currency": "USD", "scale": "metro", "metro": True},
    "CA-TORONTO": {"latitude": 43.6532, "longitude": -79.3832, "timezone": "America/Toronto", "currency": "CAD", "scale": "metro", "metro": True},
    "AU-SYDNEY": {"latitude": -33.8688, "longitude": 151.2093, "timezone": "Australia/Sydney", "currency": "AUD", "scale": "metro", "metro": True},
    "NZ-AUCKLAND": {"latitude": -36.8485, "longitude": 174.7633, "timezone": "Pacific/Auckland", "currency": "NZD", "scale": "city", "metro": False},
    "BR-SAOPAULO": {"latitude": -23.5505, "longitude": -46.6333, "timezone": "America/Sao_Paulo", "currency": "BRL", "scale": "metro", "metro": True},
    "ZA-CAPETOWN": {"latitude": -33.9249, "longitude": 18.4241, "timezone": "Africa/Johannesburg", "currency": "ZAR", "scale": "city", "metro": False},
}

#: Indicative nightly stay rates per currency and city scale, in minor units.
#: These are *template* rates, not market quotes, and are labelled as such.
_INDICATIVE_NIGHTLY_MINOR: dict[str, dict[str, int]] = {
    "CNY": {"metro": 48000, "city": 30000, "county": 18000},
    "HKD": {"metro": 62000, "city": 42000, "county": 26000},
    "MOP": {"metro": 58000, "city": 40000, "county": 25000},
    "TWD": {"metro": 260000, "city": 180000, "county": 110000},
    "JPY": {"metro": 14000, "city": 10000, "county": 7000},
    "KRW": {"metro": 120000, "city": 85000, "county": 60000},
    "SGD": {"metro": 19000, "city": 14000, "county": 9000},
    "MYR": {"metro": 26000, "city": 18000, "county": 11000},
    "THB": {"metro": 180000, "city": 120000, "county": 70000},
    "VND": {"metro": 1400000, "city": 900000, "county": 500000},
    "IDR": {"metro": 900000, "city": 600000, "county": 350000},
    "AED": {"metro": 45000, "city": 32000, "county": 20000},
    "INR": {"metro": 600000, "city": 380000, "county": 200000},
    "GBP": {"metro": 14000, "city": 9500, "county": 7000},
    "EUR": {"metro": 13500, "city": 9500, "county": 6500},
    "RUB": {"metro": 700000, "city": 450000, "county": 300000},
    "TRY": {"metro": 220000, "city": 150000, "county": 95000},
    "USD": {"metro": 19000, "city": 13000, "county": 8500},
    "CAD": {"metro": 21000, "city": 14500, "county": 9500},
    "AUD": {"metro": 20000, "city": 14000, "county": 9000},
    "NZD": {"metro": 19000, "city": 13000, "county": 8500},
    "BRL": {"metro": 38000, "city": 25000, "county": 15000},
    "ZAR": {"metro": 120000, "city": 80000, "county": 50000},
}
_DEFAULT_INDICATIVE_NIGHTLY = 12000

#: Slot templates.  Deliberately spread across the whole day so that a
#: traveller's day rhythm has something to remove; a late riser loses the
#: ``morning`` slots and keeps the rest.
_SLOT_TEMPLATES: tuple[tuple[str, str, str], ...] = (
    ("morning", "09:00", "10:30"),
    ("late_morning", "11:00", "12:30"),
    ("midday", "12:40", "13:40"),
    ("afternoon", "14:30", "16:00"),
    ("late_afternoon", "16:30", "17:50"),
    ("evening", "18:30", "20:00"),
    ("night", "20:30", "22:00"),
)

_SLOT_TITLES_ZH: dict[str, tuple[str, str]] = {
    "morning": ("老城街区漫步", "neighborhood"),
    "late_morning": ("市博物馆", "museum"),
    "midday": ("本地菜市场", "market"),
    "afternoon": ("城市公园", "park"),
    "late_afternoon": ("滨水步道", "waterfront"),
    "evening": ("地方美食街", "food_street"),
    "night": ("夜市", "night_market"),
}

_SLOT_TITLES_EN: dict[str, tuple[str, str]] = {
    "morning": ("Old town walk", "neighborhood"),
    "late_morning": ("City museum", "museum"),
    "midday": ("Central market", "market"),
    "afternoon": ("City park", "park"),
    "late_afternoon": ("Riverside walk", "waterfront"),
    "evening": ("Local food street", "food_street"),
    "night": ("Night market", "night_market"),
}

#: Deterministic ring offsets, in degrees, so template POIs do not stack on the
#: city centre (and never on Null Island).
_RING_OFFSETS: tuple[tuple[float, float], ...] = (
    (0.006, 0.008),
    (-0.011, 0.005),
    (0.004, -0.013),
    (-0.008, -0.009),
    (0.014, 0.001),
    (-0.003, 0.015),
    (0.010, 0.012),
)

_STAY_NAMES_ZH = ("城中商务酒店", "老城精品客栈", "滨水公寓式酒店")
_STAY_NAMES_EN = ("Central Business Hotel", "Old Town Boutique Inn", "Riverside Apartments")


def _norm_code(raw: str) -> str:
    return str(raw or "").strip().upper().replace("_", "-")


def city_centre(city_code: str) -> dict[str, Any]:
    """Return the registry entry for a city, or an empty dict."""

    return dict(CITY_CENTRES.get(_norm_code(city_code), {}))


def city_scale(city_code: str) -> str:
    entry = CITY_CENTRES.get(_norm_code(city_code), {})
    return str(entry.get("scale", "city"))


def _is_cjk_city(city_code: str) -> bool:
    return _norm_code(city_code).startswith(("CN-", "HK-", "MO-", "TW-"))


def _nightly_minor(currency: str, scale: str) -> int:
    table = _INDICATIVE_NIGHTLY_MINOR.get(currency.upper())
    if table is None:
        return _DEFAULT_INDICATIVE_NIGHTLY
    return int(table.get(scale, table.get("city", _DEFAULT_INDICATIVE_NIGHTLY)))


def derive_generic_profile(
    city_code: str,
    *,
    currency: str | None = None,
    timezone: str | None = None,
    days: int = 3,
    party_size: int = 2,
) -> dict[str, Any]:
    """Build a template city profile for a city with no captured data.

    The returned dict has the same shape as a captured fixture so the planner
    can consume it unchanged, but its ``provenance`` is
    :data:`DERIVED_GENERIC` and every place it contains is explicitly
    ``UNKNOWN`` or ``ESTIMATED`` cost.  It is a starting point a traveller can
    edit, never evidence.
    """

    code = _norm_code(city_code)
    entry = CITY_CENTRES.get(code, {})
    latitude = float(entry.get("latitude", 0.0))
    longitude = float(entry.get("longitude", 0.0))
    scale = str(entry.get("scale", "city"))
    resolved_currency = str(currency or entry.get("currency") or "CNY").upper()
    resolved_timezone = str(timezone or entry.get("timezone") or "UTC")
    cjk = _is_cjk_city(code)
    titles = _SLOT_TITLES_ZH if cjk else _SLOT_TITLES_EN

    # A county town without a metro gets a shorter, walkable day; a metro city
    # gets the full spread.  This is the same distinction a traveller makes.
    slots = _SLOT_TEMPLATES if scale != "county" else _SLOT_TEMPLATES[:5]
    day_offsets = range(0, max(1, min(int(days), 5)))

    activities: list[dict[str, Any]] = []
    for day_offset in day_offsets:
        for index, (slot, start, end) in enumerate(slots):
            title, category = titles[slot]
            if scale == "county" and category in {"museum", "night_market"}:
                # A county town realistically has neither a municipal museum nor
                # a nightly market; offer the local version instead.
                title = "古村落" if cjk else "Heritage village"
                category = "heritage"
            d_lat, d_lon = _RING_OFFSETS[(day_offset * len(slots) + index) % len(_RING_OFFSETS)]
            activities.append(
                {
                    "key": f"{code.lower()}-{slot}-d{day_offset}",
                    "title": title,
                    "category": category,
                    "day_offset": day_offset,
                    "start": start,
                    "end": end,
                    "latitude": round(latitude + d_lat, 6),
                    "longitude": round(longitude + d_lon, 6),
                    # Never "KNOWN": the product has no cost evidence here.
                    "cost_amount_minor": 0,
                    "cost_status": "UNKNOWN",
                    "provenance": DERIVED_GENERIC,
                }
            )

    nightly = _nightly_minor(resolved_currency, scale)
    stay_names = _STAY_NAMES_ZH if cjk else _STAY_NAMES_EN
    room_type = "Family room" if int(party_size) > 3 else "Standard twin"
    stays: list[dict[str, Any]] = []
    for index, name in enumerate(stay_names):
        factor = (0.82, 1.0, 1.24)[index]
        d_lat, d_lon = _RING_OFFSETS[index]
        stays.append(
            {
                "external_offer_id": f"generic-{code.lower()}-{index + 1}",
                "property_name": f"{name}",
                "latitude": round(latitude + d_lat, 6),
                "longitude": round(longitude + d_lon, 6),
                "room_type": room_type,
                "nightly_amount_minor": int(round(nightly * factor)),
                "refundable": index != 2,
                "luggage_drop": {
                    "available": True,
                    "open_from": "07:00",
                    "open_to": "23:00",
                    "pickup_deadline": "22:30",
                },
                "provenance": DERIVED_GENERIC,
                "evidence_confidence": 0.35,
            }
        )

    return {
        "provider": {
            "provider_key": "citynexus-generic-template",
            "provenance": DERIVED_GENERIC,
            "captured_at": None,
        },
        "timezone": resolved_timezone,
        "currency": resolved_currency,
        "center": {
            "latitude": latitude,
            "longitude": longitude,
            "crs": "WGS84",
        },
        "scale": scale,
        "has_metro": bool(entry.get("metro", False)),
        "activities": activities,
        "stays": stays,
        "provenance": DERIVED_GENERIC,
    }


def resolve_city_profile(
    city_code: str,
    *,
    captured: dict[str, Any] | None = None,
    currency: str | None = None,
    timezone: str | None = None,
    days: int = 3,
    party_size: int = 2,
) -> dict[str, Any]:
    """Captured fixture when one exists, otherwise a labelled template."""

    if captured:
        profile = dict(captured)
        profile.setdefault("provenance", CAPTURED_REPLAY)
        return profile
    return derive_generic_profile(
        city_code,
        currency=currency,
        timezone=timezone,
        days=days,
        party_size=party_size,
    )


def known_cities() -> Iterable[str]:
    return tuple(CITY_CENTRES)
