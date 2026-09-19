"""Aggregate the V16 lab per-persona JSONs into a results table + jsonl.

Run from the V16 workspace root:
    python tools/v16_realuser/_build_results.py
Emits:
    evidence/v16_lab/lab_summary.json            (compact array of per-persona rows)
    evidence/v16_lab/V16_REALUSER_RESULTS.jsonl  (one row per line)
and prints a markdown table to stdout.
"""
from __future__ import annotations

import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAB = os.path.join(ROOT, "evidence", "v16_lab")


def _row(d: dict) -> dict:
    plan = d.get("plan") or {}
    ai_desk = d.get("ai_desk") or []
    ai_calls = sum(1 for a in ai_desk if a.get("http_status") == 200)
    blocked = sum(1 for a in ai_desk if a.get("submit_disabled"))
    http_errors = d.get("http_errors") or []
    fatal = d.get("setup_error")
    if not fatal:
        for a in ai_desk:
            if isinstance(a.get("http_status"), int) and a["http_status"] >= 400:
                fatal = f"ai_desk http {a['http_status']}"
                break
    return {
        "persona": d.get("persona"),
        "city": d.get("city"),
        "city_code": d.get("city_code"),
        "currency": d.get("currency"),
        "options": plan.get("option_count"),
        "http_errors": len(http_errors),
        "console_errors": len(d.get("console_errors") or []),
        "page_errors": len(d.get("page_errors") or []),
        "ai_calls": ai_calls,
        "blocked": blocked,
        "fatal": fatal,
    }


def main() -> None:
    rows = []
    for f in sorted(glob.glob(os.path.join(LAB, "P*.json"))):
        if "lab_summary" in f:
            continue
        with open(f, encoding="utf-8") as fh:
            rows.append(_row(json.load(fh)))

    with open(os.path.join(LAB, "lab_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)

    with open(os.path.join(LAB, "V16_REALUSER_RESULTS.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"personas aggregated: {len(rows)}")
    total_err = sum(
        (r["http_errors"] or 0) + (r["console_errors"] or 0) + (r["page_errors"] or 0)
        for r in rows
    )
    min_opts = min((r["options"] or 0) for r in rows) if rows else 0
    print(f"total errors: {total_err}   min options: {min_opts}")
    print()
    print("| persona | city | cur | options | http | console | page | ai | blocked | fatal |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(
            "| {persona} | {city} | {currency} | {options} | {http_errors} | "
            "{console_errors} | {page_errors} | {ai_calls} | {blocked} | {fatal} |".format(**r)
        )


if __name__ == "__main__":
    main()
