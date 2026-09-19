from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()

    issues: list[tuple[str, str, str]] = []
    ok: list[str] = []

    schema = (repo / "backend/db/schema.sql").read_text(encoding="utf-8")
    models = (repo / "backend/app/db/models.py").read_text(encoding="utf-8")
    commerce_models = repo / "backend/app/commerce/models.py"
    if commerce_models.exists():
        models += "\n" + commerce_models.read_text(encoding="utf-8")
    ports = (repo / "backend/app/integrations/ports.py").read_text(encoding="utf-8")
    commerce_ports = repo / "backend/app/integrations/commerce_ports.py"
    if commerce_ports.exists():
        ports += "\n" + commerce_ports.read_text(encoding="utf-8")
    openapi = (repo / "contracts/openapi.yaml").read_text(encoding="utf-8")

    m = re.search(r"level TEXT NOT NULL CHECK \(level IN \(([^)]*)\)\)", schema)
    if m:
        levels = [x.strip().strip("'\"") for x in m.group(1).split(",")]
        if len(levels) != 5:
            issues.append(("P0", "COMMITMENT_STRENGTH_COUNT", f"SQL currently supports {len(levels)} levels: {levels}; source requires exactly five"))
        else:
            ok.append(f"commitment SQL exposes five levels: {levels}")
    else:
        issues.append(("P0", "COMMITMENT_STRENGTH_SCHEMA", "could not identify commitment strength check"))

    for cls in ["Commitment", "Booking", "Order", "PaymentTransaction", "ProviderCall", "IdempotencyKey"]:
        if f"class {cls}(" not in models:
            issues.append(("P0", "ORM_MISSING", cls))
    for proto in ["BookingProvider", "PaymentProvider"]:
        if f"class {proto}(" not in ports:
            issues.append(("P0", "PORT_MISSING", proto))

    needed_paths = [
        "/journeys/{journey_id}/bookings:",
        "/bookings/{booking_id}/cancel:",
        "/journeys/{journey_id}/orders:",
        "/journeys/{journey_id}/transactions:",
    ]
    for path in needed_paths:
        if path not in openapi:
            issues.append(("P0", "OPENAPI_MISSING", path))

    optional_requirements = {
        "IR-006": ["booking-slots", "/bookings/{booking_id}:"],
        "IR-007": ["/transactions/{transaction_id}:"],
    }
    for rid, tokens in optional_requirements.items():
        missing = [token for token in tokens if token not in openapi]
        if missing:
            issues.append(("P1", "CONTRACT_COVERAGE", f"{rid} missing contract tokens: {missing}"))

    status_path = repo / "docs/implementation/implementation-status.csv"
    if status_path.exists():
        with status_path.open(encoding="utf-8-sig") as handle:
            ids = {row["requirement_id"] for row in csv.DictReader(handle)}
        for rid in ["FR-029", "FR-030", "FR-033", "FR-036", "FR-037", "IR-006", "IR-007", "IR-015", "BR-017", "BR-018"]:
            if rid not in ids:
                issues.append(("P0", "TRACE_MISSING", rid))
    else:
        issues.append(("P1", "TRACE_FILE_MISSING", str(status_path)))

    print("WP04 PRE-FLIGHT")
    for item in ok:
        print("PASS", item)
    for severity, code, detail in issues:
        print(severity, code, detail)
    print(f"SUMMARY p0={sum(1 for x in issues if x[0]=='P0')} p1={sum(1 for x in issues if x[0]=='P1')}")
    return 2 if any(x[0] == "P0" for x in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
