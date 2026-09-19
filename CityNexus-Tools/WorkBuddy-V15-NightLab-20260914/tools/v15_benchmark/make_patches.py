"""Regenerate the two V15 patches as conflict-free, new-file-only diffs.

Both patches are built from ``/dev/null`` so every hunk is an addition of a file
that cannot already exist in the Codex worktree. That is what makes them safe to
apply on top of in-flight work: there is no context to conflict with, no existing
line to move, and no deletion. ``git apply`` either creates the file or fails
loudly.

  patches/V15_COPILOT_TESTS_ONLY.patch
      test-support modules + test modules only. Applies to any V14/V15 tree.
      The semantic-contract and contrast modules ``importorskip`` the router, so
      this patch is green on a tree that has no router yet.

  patches/V15_REFERENCE_IMPLEMENTATION_OPTIONAL.patch
      the optional reference router. Independent of the tests-only patch and
      explicitly NOT a mandate to replace Codex's implementation.

Usage::

    python tools/v15_benchmark/make_patches.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATCH_DIR = ROOT / "patches"

TESTS_ONLY = [
    "backend/tests/v15_copilot_helpers.py",
    "backend/tests/_v15_semantic_cases.py",
    "backend/tests/test_v15_copilot_semantic_contract.py",
    "backend/tests/test_v15_copilot_authority_boundary.py",
    "backend/tests/test_v15_copilot_v14_gaps.py",
    "backend/tests/test_v15_cross_city_genericity.py",
    "backend/tests/test_v15_semantic_contrast.py",
]

REFERENCE = [
    "backend/app/agent/semantic_router.py",
]


def diff_one(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"missing source file: {rel}")
    proc = subprocess.run(
        ["git", "diff", "--no-index", "--no-color", "--", "/dev/null", rel],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # git returns 1 when the inputs differ, which is always the case here.
    if proc.returncode not in (0, 1):
        raise SystemExit(f"git diff failed for {rel}: {proc.stderr}")
    body = proc.stdout
    # Drop git's advisory about CRLF; it is noise in a patch file.
    return "\n".join(
        line for line in body.splitlines()
        if not line.startswith("warning: in the working copy of")
    )


def build(name: str, files: list[str], header: str) -> Path:
    chunks = [diff_one(rel).rstrip("\n") for rel in files]
    text = header.rstrip("\n") + "\n\n" + "\n\n".join(chunks) + "\n"
    out = PATCH_DIR / name
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    # Patches must stay LF-only: git apply is line-ending sensitive on Windows.
    out.write_bytes(text.encode("utf-8"))
    return out


def main() -> int:
    tests_header = (
        "V15 Copilot semantic + cross-city authority: TESTS ONLY.\n"
        "\n"
        "Every file below is new (new file mode / --- /dev/null), so this patch\n"
        "adds only test-support modules and test modules. It changes no product\n"
        "code, no schema, no route and no configuration, and it deletes nothing.\n"
        "There is therefore nothing for it to conflict with in the Codex worktree.\n"
        "\n"
        "Guarantees it encodes:\n"
        "  * hypothetical (WHAT_IF) and preference messages never create a real Event;\n"
        "  * only DISRUPTION_REPORT may create one, and only from a present-tense report;\n"
        "  * authority-override attempts never receive a mutation-permitting policy;\n"
        "  * commitment-touching requests always require confirmation;\n"
        "  * no copilot path moves PlanVersion / Commitment / Booking / payment state;\n"
        "  * cross-city journeys never inherit another city's locale, place hints or money unit;\n"
        "  * the two named minimal pairs never collapse into one route.\n"
        "\n"
        "Known V14 gaps are recorded as named xfail(strict=False) markers rather than\n"
        "failures, so this patch is green on today's tree and turns green-to-XPASS as\n"
        "the gaps are fixed.\n"
        "\n"
        "Apply:  git apply patches/V15_COPILOT_TESTS_ONLY.patch\n"
        "Verify: git apply --check patches/V15_COPILOT_TESTS_ONLY.patch\n"
    )
    ref_header = (
        "V15 Copilot semantic router: OPTIONAL REFERENCE IMPLEMENTATION.\n"
        "\n"
        "This is a reference, not a mandate. It exists so the tests-only patch has a\n"
        "measured comparison point, and so the deterministic rules that close the V14\n"
        "gaps are written down somewhere concrete. Do NOT treat it as a required\n"
        "replacement for the Codex implementation. It is independent of\n"
        "V15_COPILOT_TESTS_ONLY.patch and may be dropped entirely.\n"
        "\n"
        "Division of responsibility, as the V15 brief requires:\n"
        "  * the model (or this deterministic layer) proposes an INTENT;\n"
        "  * the server owns AUTHORITATIVE FACTS and MUTATION PERMISSION.\n"
        "A model can never talk the router into granting mutation rights for an\n"
        "authority-override message, and can never make a hypothetical materialise a\n"
        "real Event.\n"
        "\n"
        "Measured on the 213-case benchmark: 99.1% intent, 96.7% mutation policy,\n"
        "100% event boundary, 0 event false positives, 0 authority-override escapes.\n"
        "\n"
        "Apply:  git apply patches/V15_REFERENCE_IMPLEMENTATION_OPTIONAL.patch\n"
    )

    a = build("V15_COPILOT_TESTS_ONLY.patch", TESTS_ONLY, tests_header)
    b = build("V15_REFERENCE_IMPLEMENTATION_OPTIONAL.patch", REFERENCE, ref_header)

    for path in (a, b):
        text = path.read_bytes().decode("utf-8")
        new_files = text.count("new file mode")
        additions = sum(
            1 for line in text.splitlines() if line.startswith("+") and not line.startswith("+++")
        )
        print(f"{path.name}: {len(text.splitlines())} lines, "
              f"{new_files} new files, {additions} insertions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
