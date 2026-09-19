"""Probe the *post-fix* capability backstop chain.

Codex landed ``app/capabilities.py`` at 10:53 during the V19 run.  The module
is the intended safety net for the exact V19 attacks.  This probe measures
whether the net actually catches them:

  raw text
    -> model capability item (severity chosen by DeepSeek, attacker-controlled)
    -> extract_capabilities_from_text(text)      <-- local backstop
    -> canonicalize_capabilities(model + local)  <-- merge, no dedupe
    -> capability_constraints(...)               <-- only HARD becomes a gate

The question is: when the model mislabels a hard accessibility need, does the
local backstop still put a HARD item on the gate?

Usage:
    python tools/v19_probe_capability_backstop.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
CURRENT = LAB / "repo_copy_current"
EVID = LAB / "evidence"

sys.path.insert(0, str(CURRENT / "backend"))

from app.capabilities import (  # noqa: E402
    canonicalize_capabilities,
    capability_constraints,
    extract_capabilities_from_text,
    summarize_capabilities,
)

HARD_CODES = ("STEP_FREE_REQUIRED", "AVOID_STAIRS")


def text_of(case: dict) -> str:
    return case.get("raw_text") or case.get("text") or ""


def merge(model_items, text, scope="JOURNEY"):
    """Mirror of semantic_compiler.compile_semantic_envelope's merge step."""
    local = extract_capabilities_from_text(text, scope=scope)
    merged = canonicalize_capabilities(
        [*model_items, *local], source="SEMANTIC", provenance="USER_STATED"
    )
    return local, merged


def gate_codes(items) -> list[str]:
    return [g["rule_code"] for g in capability_constraints(items)]


def main() -> int:
    out: dict = {}

    # ------------------------------------------------------------------ 1. the
    # canonicalize_capabilities downgrade guard, exhaustively over its own
    # documented promise: "A hard accessibility capability may not be
    # downgraded by a model or by an API client that mislabeled its class."
    guard = {}
    for code in HARD_CODES:
        for severity in ("HARD", "STRONG", "SOFT", None):
            for klass in ("HARD_ACCESSIBILITY_NEED", "SOFT_PREFERENCE", None):
                payload = {"code": code}
                if severity:
                    payload["severity"] = severity
                if klass:
                    payload["class"] = klass
                canon = canonicalize_capabilities([payload])
                guard[f"{code}|{severity}|{klass}"] = {
                    "in": payload,
                    "out_severity": canon[0]["severity"] if canon else None,
                    "out_class": canon[0]["class"] if canon else None,
                    "hard_gate": bool(capability_constraints(canon)),
                }
    out["guard_matrix"] = guard
    out["guard_matrix_summary"] = {
        "cells": len(guard),
        "input_said_HARD": sum(1 for v in guard.values() if v["in"].get("severity") == "HARD"),
        "output_is_HARD": sum(1 for v in guard.values() if v["out_severity"] == "HARD"),
        "downgrades_accepted": [
            k for k, v in guard.items()
            if v["in"].get("severity") in ("STRONG", "SOFT", None) and v["out_severity"] != "HARD"
        ],
        "class_always_corrected": all(
            v["out_class"] == "HARD_ACCESSIBILITY_NEED" for v in guard.values()
        ),
    }

    # ------------------------------------------------------------------ 2. the
    # end-to-end exploit: model says SOFT, local backstop is silent.
    exploit = {}
    for label, text in {
        "clean_hard_zh": "必须全程无障碍，一步楼梯都不能走",
        "clean_hard_en": "I use a wheelchair, every leg must be step-free",
        "negation_marker_present": "我以前不用轮椅，但现在必须全程 step-free",
        "negation_marker_zh": "我没有过敏，但我用轮椅，必须全程无障碍",
        "past_reference": "过去我坐轮椅，现在必须全程无障碍",
        "polite_hard": "麻烦安排一下，我用轮椅，希望全程无台阶",
    }.items():
        model_soft = [{"code": "STEP_FREE_REQUIRED", "severity": "SOFT", "params": {}}]
        model_strong = [{"code": "STEP_FREE_REQUIRED", "severity": "STRONG", "params": {}}]
        local, merged_soft = merge(model_soft, text)
        _, merged_strong = merge(model_strong, text)
        exploit[label] = {
            "text": text,
            "local_backstop": [c["code"] for c in local],
            "model_SOFT__merged_severities": [c["severity"] for c in merged_soft],
            "model_SOFT__gate": gate_codes(merged_soft),
            "model_SOFT__need_survives": bool(gate_codes(merged_soft)),
            "model_STRONG__gate": gate_codes(merged_strong),
            "model_STRONG__need_survives": bool(gate_codes(merged_strong)),
        }
    out["end_to_end_exploit"] = exploit
    out["end_to_end_exploit_summary"] = {
        "cases": len(exploit),
        "model_SOFT_lost": sum(1 for v in exploit.values() if not v["model_SOFT__need_survives"]),
        "model_STRONG_lost": sum(1 for v in exploit.values() if not v["model_STRONG__need_survives"]),
    }

    # ------------------------------------------------------------------ 3. how
    # often the local backstop is silent at all, i.e. how often the model's
    # label is the sole authority over a hard need.
    cases = [json.loads(l) for l in (EVID / "semantic_cases.jsonl").open(encoding="utf-8") if l.strip()]
    silent = Counter()
    totals = Counter()
    should_be_hard_silent = []
    for case in cases:
        bucket = case["bucket"]
        totals[bucket] += 1
        local = extract_capabilities_from_text(text_of(case), scope="JOURNEY")
        if not local:
            silent[bucket] += 1
        expects_hard = (case.get("expected") or {}).get("hardness") == "HARD"
        if expects_hard and not local:
            should_be_hard_silent.append(
                {"id": case["id"], "bucket": bucket, "role": case.get("role"),
                 "text": text_of(case), "expected": case.get("expected")}
            )
    out["backstop_silence"] = {
        "overall": {
            "cases": sum(totals.values()),
            "silent": sum(silent.values()),
            "rate": round(sum(silent.values()) / sum(totals.values()), 4),
        },
        "by_bucket": {
            b: {"cases": totals[b], "silent": silent[b], "rate": round(silent[b] / totals[b], 4)}
            for b in sorted(totals)
        },
    }
    out["hard_expected_but_no_backstop"] = {
        "count": len(should_be_hard_silent),
        "samples": should_be_hard_silent[:20],
    }

    # ------------------------------------------------------------------ 4. no
    # dedupe: the same code can arrive twice with conflicting severities.
    dup_model = [{"code": "STEP_FREE_REQUIRED", "severity": "SOFT", "params": {}}]
    text = "必须全程无障碍，一步楼梯都不能走"
    _, merged = merge(dup_model, text)
    summary = summarize_capabilities(merged)
    out["duplicate_code_no_dedupe"] = {
        "merged": [{"code": c["code"], "severity": c["severity"], "source": c["source"]} for c in merged],
        "same_code_appears_twice": len({c["code"] for c in merged}) < len(merged),
        "hard_list": [c["severity"] for c in summary["hard"]],
        "soft_list": [c["severity"] for c in summary["soft"]],
        "code_in_both_hard_and_soft": sorted(
            {c["code"] for c in summary["hard"]} & {c["code"] for c in summary["soft"]}
        ),
        "gate": gate_codes(merged),
    }

    # ------------------------------------------------------------------ 5. scope:
    # the module defines TRAVELER scope but can the deterministic path emit it?
    scopes = Counter()
    for case in cases:
        for cap in extract_capabilities_from_text(text_of(case)):
            scopes[cap["scope"]] += 1
    traveler_direct = extract_capabilities_from_text(
        "我用轮椅，这是永久情况，不只是这次旅行", scope="TRAVELER"
    )
    out["scope_reachability"] = {
        "extractor_default_scope_distribution": dict(scopes),
        "explicit_TRAVELER_request": [c["scope"] for c in traveler_direct],
        "note": "The extractor honours the scope argument but never infers TRAVELER "
                "from language such as 'always' / 'permanently' / '不只是这次'.",
    }

    (EVID / "capability_backstop_probe.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(json.dumps({
        "guard_matrix_summary": out["guard_matrix_summary"],
        "end_to_end_exploit_summary": out["end_to_end_exploit_summary"],
        "backstop_silence_overall": out["backstop_silence"]["overall"],
        "hard_expected_but_no_backstop": out["hard_expected_but_no_backstop"]["count"],
        "duplicate_code_no_dedupe": out["duplicate_code_no_dedupe"],
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
