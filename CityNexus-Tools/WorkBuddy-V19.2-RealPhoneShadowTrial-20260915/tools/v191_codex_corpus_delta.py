"""Quantify Codex V19.1 against FINAL_V19 across the 182-case corpus.

Re-uses the texts already recorded in evidence/eac_differential.jsonl, runs only
the live-tree extractor, and diffs against the stored FINAL_V19 result.  Pure
functions, no database, no network.

Output: evidence/codex_v19_1_corpus_delta.json
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
LAB = HERE.parents[1]
LIVE = Path(r"D:\moodle\CityNexus\backend")
CORPUS = LAB / "evidence" / "eac_differential.jsonl"
OUT = LAB / "evidence" / "codex_v19_1_corpus_delta.json"

HARD_CODES = {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


LIVE_CAPS = load(LIVE / "app" / "capabilities.py", "_cd_live")


def run(text: str) -> dict:
    fn = LIVE_CAPS.extract_capabilities_from_text
    kwargs = {"scope": "JOURNEY"} if "scope" in inspect.signature(fn).parameters else {}
    try:
        items = fn(text, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"codes": [], "hard": [], "error": f"{type(exc).__name__}: {exc}"}
    rows = []
    for item in items:
        if hasattr(item, "code"):
            rows.append({"code": item.code, "severity": item.severity,
                         "scope": item.scope})
        elif isinstance(item, dict):
            rows.append(dict(item))
    return {
        "codes": sorted({str(r.get("code")) for r in rows if r.get("code")}),
        "hard": sorted({str(r.get("code")) for r in rows
                        if r.get("code") in HARD_CODES}),
        "count": len(rows),
    }


def main() -> int:
    rows = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    out = []
    for row in rows:
        live = run(row["text"])
        b_codes = row["b"]["codes"]
        out.append({
            "id": row["id"], "bucket": row["bucket"], "text": row["text"],
            "b_codes": b_codes,
            "live_codes": live["codes"],
            "live_hard": live["hard"],
            "b_hard": row["b"]["hard_codes"],
            "changed": live["codes"] != b_codes,
            "live_only": sorted(set(live["codes"]) - set(b_codes)),
            "b_only": sorted(set(b_codes) - set(live["codes"])),
            "live_false_hard_fixed": bool(row["b"]["hard_codes"]) and not live["hard"],
            "live_new_hard": bool(live["hard"]) and not row["b"]["hard_codes"],
        })

    by_bucket: dict = defaultdict(lambda: {
        "cases": 0, "changed": 0, "live_only": 0, "b_only": 0,
        "hard_fixed": 0, "new_hard": 0, "live_hard": 0, "b_hard": 0})
    for r in out:
        s = by_bucket[r["bucket"]]
        s["cases"] += 1
        s["changed"] += int(r["changed"])
        s["live_only"] += int(bool(r["live_only"]))
        s["b_only"] += int(bool(r["b_only"]))
        s["hard_fixed"] += int(r["live_false_hard_fixed"])
        s["new_hard"] += int(r["live_new_hard"])
        s["live_hard"] += int(bool(r["live_hard"]))
        s["b_hard"] += int(bool(r["b_hard"]))

    summary = {
        "corpus_size": len(out),
        "changed": sum(1 for r in out if r["changed"]),
        "live_only": sum(1 for r in out if r["live_only"]),
        "b_only": sum(1 for r in out if r["b_only"]),
        "hard_fixed": sum(1 for r in out if r["live_false_hard_fixed"]),
        "new_hard": sum(1 for r in out if r["live_new_hard"]),
        "live_hard_total": sum(1 for r in out if r["live_hard"]),
        "b_hard_total": sum(1 for r in out if r["b_hard"]),
        "by_bucket": dict(sorted(by_bucket.items())),
        "hard_fixed_examples": [
            {"id": r["id"], "text": r["text"], "b": r["b_codes"],
             "live": r["live_codes"]} for r in out if r["live_false_hard_fixed"]][:20],
        "new_hard_examples": [
            {"id": r["id"], "text": r["text"], "b": r["b_codes"],
             "live": r["live_codes"]} for r in out if r["live_new_hard"]][:20],
        "regressions": [
            {"id": r["id"], "text": r["text"], "b": r["b_codes"],
             "live": r["live_codes"]} for r in out if r["b_only"]][:20],
    }
    OUT.write_text(json.dumps({"summary": summary, "rows": out},
                              ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {OUT}")
    print(json.dumps({k: v for k, v in summary.items()
                      if not isinstance(v, (dict, list))},
                     ensure_ascii=False, indent=2))
    print("\n--- by bucket ---")
    for bucket, s in sorted(by_bucket.items()):
        print(f"  {bucket:20s} n={s['cases']:3d} changed={s['changed']:3d} "
              f"live_only={s['live_only']:3d} b_only={s['b_only']:3d} "
              f"hard_fixed={s['hard_fixed']:3d} new_hard={s['new_hard']:3d} "
              f"live_hard={s['live_hard']:3d} b_hard={s['b_hard']:3d}")
    print("\n--- hard_fixed (false HARD removed) ---")
    for r in summary["hard_fixed_examples"]:
        print(f"  {r['text'][:56]:58s} B={r['b']} -> LIVE={r['live']}")
    print("\n--- regressions (B had a code, LIVE lost it) ---")
    for r in summary["regressions"]:
        print(f"  {r['text'][:56]:58s} B={r['b']} -> LIVE={r['live']}")
    print("\n--- new_hard ---")
    for r in summary["new_hard_examples"]:
        print(f"  {r['text'][:56]:58s} B={r['b']} -> LIVE={r['live']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
