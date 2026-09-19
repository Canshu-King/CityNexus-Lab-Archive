"""Flatten the V19.1 A/B evidence into the contract's jsonl artefacts.

  evidence/boundaries.jsonl   <- evidence/boundaries_{a,b}.json
  evidence/e2e_results.jsonl  <- lifecycle / c4_gate / c4_start /
                                 commitment_conflict {a,b}.json

Read-only w.r.t. everything except the two output files.
"""

from __future__ import annotations

import json
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
EV = LAB / "evidence"

BOUNDARY_SECTIONS = (
    "control",
    "max_walking_per_leg_m",
    "max_continuous_walking_min",
    "max_daily_walking_m",
    "midday_rest_window",
    "infant_nap_window",
    "rest_every_min",
    "toilet_break_every_min",
    "evidence_symmetry",
)

E2E_SOURCES = ("lifecycle", "c4_gate", "c4_start", "commitment_conflict")


def flatten(section: object, label: str, name: str) -> list[dict]:
    rows: list[dict] = []
    if isinstance(section, list):
        for i, item in enumerate(section):
            if isinstance(item, dict):
                rows.append({"snapshot": label, "section": name,
                             "index": i, **item})
            else:
                rows.append({"snapshot": label, "section": name,
                             "index": i, "value": item})
    elif isinstance(section, dict):
        for key, item in section.items():
            if isinstance(item, dict):
                rows.append({"snapshot": label, "section": name,
                             "case": key, **item})
            elif isinstance(item, list):
                for i, sub in enumerate(item):
                    if isinstance(sub, dict):
                        rows.append({"snapshot": label, "section": name,
                                     "case": key, "index": i, **sub})
                    else:
                        rows.append({"snapshot": label, "section": name,
                                     "case": key, "index": i, "value": sub})
            else:
                rows.append({"snapshot": label, "section": name,
                             "case": key, "value": item})
    else:
        rows.append({"snapshot": label, "section": name, "value": section})
    return rows


def main() -> int:
    # ---- boundaries.jsonl
    out = []
    for label in ("a", "b"):
        path = EV / f"boundaries_{label}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for name in BOUNDARY_SECTIONS:
            if name in data:
                out.append(("boundaries", flatten(data[name], label, name)))
    flat = [row for _, rows in out for row in rows]
    (EV / "boundaries.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in flat),
        encoding="utf-8")
    print(f"boundaries.jsonl: {len(flat)} rows")

    # ---- e2e_results.jsonl
    e2e = []
    for label in ("a", "b"):
        for src in E2E_SOURCES:
            path = EV / f"{src}_{label}.json"
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for name, section in data.items():
                if name == "snapshot":
                    continue
                e2e.extend(flatten(section, label, f"{src}.{name}"))
    (EV / "e2e_results.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in e2e),
        encoding="utf-8")
    print(f"e2e_results.jsonl: {len(e2e)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
