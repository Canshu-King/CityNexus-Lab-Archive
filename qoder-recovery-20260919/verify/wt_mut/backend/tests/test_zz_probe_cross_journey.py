from fastapi.testclient import TestClient
from app.main import app
import test_wp05_integrity_next as base

client = TestClient(app)

def test_probe():
    ids, _ = base._selected(start=True)
    j1 = ids["journey_id"]; traveler = ids["traveler_id"]
    j2 = client.post("/api/v1/journeys", json={
        "traveler_id": traveler, "title": "Second Journey", "city_code": "CNX-DEMO",
        "timezone": "Asia/Shanghai", "start_at": "2026-10-10T09:00:00+08:00",
        "end_at": "2026-10-10T19:00:00+08:00",
        "budget": {"amount_minor": 50000, "currency": "CNY"}, "planning_mode": "balanced"}).json()["id"]
    ev2 = client.post(f"/api/v1/journeys/{j2}/events", json={"event_type": "WEATHER"}).json()
    r = client.post(f"/api/v1/journeys/{j1}/replans", json={"trigger_event_id": ev2["id"]})
    print("CROSS status", r.status_code, r.text[:300])
    # control: j1's own event
    ev1 = client.post(f"/api/v1/journeys/{j1}/events", json={"event_type": "WEATHER"}).json()
    c = client.post(f"/api/v1/journeys/{j1}/replans", json={"trigger_event_id": ev1["id"]})
    print("CONTROL status", c.status_code, c.text[:200])
    print("j2 journey id", j2, "event2", ev2.get("id"), "status", ev2.get("status"))
