"""Probe cross-city assumptions: money parsing, place hints, locale coercion."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main_module  # noqa: E402
from app.agent import mission as mission_module  # noqa: E402
from app.db.models import Event as EventModel  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402

client = TestClient(main_module.app)

MONEY_MESSAGES = [
    ("最多多花 500 元", "zh CNY budget bound"),
    ("不超过 3000 元", "zh CNY cap"),
    ("预算 5000 元", "zh budget keyword"),
    ("under 500 SGD", "en under, SGD"),
    ("budget 50000 JPY", "en budget keyword, JPY"),
    ("less than 200 GBP", "en less-than, GBP"),
    ("loss limit 100 EUR", "en loss limit"),
    ("最多损失 200 元", "zh loss limit"),
    ("不超过 8000 日元", "zh JPY word"),
    ("under 3000 yen", "en yen word"),
    ("预算不超过 100 新加坡元", "zh SGD word"),
]

PLACE_HINT_MESSAGES = [
    ("现在海河那边涨水了。", "zh Tianjin river name"),
    ("The river is flooding near the pier.", "en generic river, London journey"),
    ("haihe is flooded", "en transliteration"),
]

LOCALE_MATRIX = [
    ("CN-FUZHOU", "Asia/Shanghai", "CNY", "zh-CN", "2026-10-01T09:00:00+08:00", "2026-10-03T18:00:00+08:00"),
    ("CN-SHANGHAI", "Asia/Shanghai", "CNY", "zh-CN", "2026-10-01T09:00:00+08:00", "2026-10-03T18:00:00+08:00"),
    ("SG-SINGAPORE", "Asia/Singapore", "SGD", "en", "2026-10-01T09:00:00+08:00", "2026-10-03T18:00:00+08:00"),
    ("JP-TOKYO", "Asia/Tokyo", "JPY", "ja", "2026-10-01T09:00:00+09:00", "2026-10-03T18:00:00+09:00"),
    ("GB-LONDON", "Europe/London", "GBP", "en", "2026-10-01T09:00:00+01:00", "2026-10-03T18:00:00+01:00"),
]


def make_journey(city, tz, cur, loc, start, end):
    traveler = client.post(
        "/api/v1/travelers",
        json={"display_name": city, "locale": loc, "timezone": tz},
    ).json()
    journey = client.post(
        "/api/v1/journeys",
        json={
            "traveler_id": traveler["id"],
            "title": city,
            "city_code": city,
            "timezone": tz,
            "start_at": start,
            "end_at": end,
            "budget": {"amount_minor": 200000, "currency": cur},
            "stay_budget": {"amount_minor": 80000, "currency": cur},
            "party_size": 1,
            "occupancy": {"adults": 1, "rooms": 1},
            "arrival_anchor": {"at": start, "location": "arr"},
            "departure_anchor": {"at": end, "location": "dep"},
        },
    ).json()
    return journey["id"]


def main() -> int:
    report: dict = {}

    # --- 1. money regex coverage
    pattern = mission_module._MONEY_PATTERN
    money_rows = []
    for message, label in MONEY_MESSAGES:
        match = pattern.search(message)
        money_rows.append(
            {
                "label": label,
                "message": message,
                "matched": bool(match),
                "captured": match.group(1) if match else None,
                "currency_suffix_present": bool(match and re.search(r"元|块|CNY", match.group(0))),
            }
        )
        print(f"money  matched={str(bool(match)):<5} {label:<28} {message}")
    report["money_pattern"] = money_rows

    # --- 2. Tianjin place hint leakage
    hint_rows = []
    for message, label in PLACE_HINT_MESSAGES:
        jid = make_journey(
            "GB-LONDON", "Europe/London", "GBP", "en",
            "2026-10-01T09:00:00+01:00", "2026-10-03T18:00:00+01:00",
        )
        client.post(
            f"/api/v1/journeys/{jid}/agent/commands",
            json={"command": message, "requested_autonomy": "EXECUTE_WITHIN_BOUNDS"},
        )
        with SessionLocal() as session:
            events = list(
                session.scalars(select(EventModel).where(EventModel.journey_id == jid)).all()
            )
        hints = [json.loads(e.payload_json).get("affected_place_hint") for e in events]
        hint_rows.append({"label": label, "message": message, "hints": hints})
        print(f"hint   hints={hints} {label:<32} {message}")
    report["place_hint"] = hint_rows

    # --- 3. copilot locale coercion
    locale_rows = []
    for city, tz, cur, loc, start, end in LOCALE_MATRIX:
        jid = make_journey(city, tz, cur, loc, start, end)
        resp = client.post(
            f"/api/v1/journeys/{jid}/copilot/messages",
            json={"message": "Explain today's plan."},
        )
        text = (resp.json() or {}).get("message") or ""
        han = any("\u4e00" <= ch <= "\u9fff" for ch in text)
        locale_rows.append(
            {
                "city": city,
                "timezone": tz,
                "currency": cur,
                "ui_locale": loc,
                "reply_has_han": han,
                "reply_head": text[:60],
            }
        )
        print(f"locale han={str(han):<5} {city:<14} {tz:<16} ui={loc:<6} {text[:40]}")
    report["copilot_locale"] = locale_rows

    # --- 4. journey currency / timezone round-trip
    currency_rows = []
    for city, tz, cur, loc, start, end in LOCALE_MATRIX:
        jid = make_journey(city, tz, cur, loc, start, end)
        body = client.get(f"/api/v1/journeys/{jid}").json()
        currency_rows.append(
            {
                "city": city,
                "expected_currency": cur,
                "actual_currency": (body.get("budget") or {}).get("currency"),
                "expected_timezone": tz,
                "actual_timezone": body.get("timezone"),
            }
        )
    report["journey_roundtrip"] = currency_rows
    for row in currency_rows:
        ok = row["expected_currency"] == row["actual_currency"] and row["expected_timezone"] == row["actual_timezone"]
        print(f"roundtrip ok={ok} {row['city']:<14} {row['actual_currency']} {row['actual_timezone']}")

    out = ROOT / "evidence" / "cross_city_probe.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
