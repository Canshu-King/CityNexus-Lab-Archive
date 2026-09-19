from pathlib import Path
P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")
old = '''        provenance=fact.provenance,
        provider_snapshot_id=fact.provider_snapshot_id,
        captured_at=fact.captured_at,
        expires_at=fact.expires_at,
    )'''
new = '''        provenance=fact.provenance,
        paid_mode=fact.paid_mode,
        evidence_json=fact.evidence_json,
        captured_at=fact.captured_at,
        expires_at=fact.expires_at,
    )'''
assert old in s
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
