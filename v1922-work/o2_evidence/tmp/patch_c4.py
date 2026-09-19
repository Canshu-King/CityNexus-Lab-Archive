from pathlib import Path
p = Path("D:/moodle/CityNexus/backend/app/stay_mobility.py")
s = p.read_text(encoding="utf-8")

old = '''        "disruptions": [
            {
                "id": item.id,
                "type": item.event_type,
                "severity": item.severity,
                "affected_activity_id": item.affected_activity_id,
                "occurred_at": item.occurred_at,
                "payload": _load(item.payload_json, {}),
            }
            for item in disruptions
        ],'''
new = '''        "disruptions": [
            {
                "id": item.id,
                "type": item.event_type,
                "severity": item.severity,
                "status": item.status,
                "affected_activity_id": item.affected_activity_id,
                "occurred_at": item.occurred_at,
                "resolved_at": item.resolved_at,
                "payload": _load(item.payload_json, {}),
            }
            for item in disruptions
        ],'''
assert s.count(old) == 1, "disruptions payload anchor"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("stay_mobility patched: disruptions now carry status + resolved_at")
