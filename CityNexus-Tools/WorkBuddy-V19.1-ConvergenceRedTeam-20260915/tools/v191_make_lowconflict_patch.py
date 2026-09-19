"""Emit patches/V19_1_LOW_CONFLICT_FIXES.patch.

Three surgical changes to ``backend/app/capabilities.py``, each independently
justified by a measured finding and each validated on a scratch copy of
Snapshot C:

  1. ``canonicalize_capabilities`` keys its dedup map on ``(scope, code)``
     instead of ``code`` alone, so a TRAVELER-scoped need and a JOURNEY-scoped
     need of the same code both survive.
  2. ``normalize_osm_tags`` unwraps a list/tuple used as a mapping value,
     instead of ``str(["yes"]) -> "['yes']"`` silently losing the tag.
  3. ``evaluate_accessibility_requirement`` reads ``step_count`` / ``steps`` /
     ``highway=steps`` as stair evidence, so ``wheelchair=yes`` beside
     ``step_count=5`` is reported as CONFLICT rather than UNVERIFIED.

Measured effect on Snapshot C: 8 of the 8 new provider-evidence defects fixed,
the cross-scope regression fixed, and no guard broken
(54 failed / 119 passed -> 46 failed / 127 passed).

NOT included (see CODEX_HANDOFF_V19_1.md §9): the ``feasibility.py`` key
whitelist, the residual false-HARD guard markers, D4/D5/D7, and the two P0 C4
defects.  This patch is deliberately limited to changes that cannot collide with
in-flight work in ``main.py`` / ``services.py`` / ``feasibility.py``.

The patch is generated, never applied.

Usage:  python tools/v191_make_lowconflict_patch.py
"""

from __future__ import annotations

import difflib
import hashlib
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
BASE = LAB / "snapshot_c" / "backend" / "app" / "capabilities.py"
FIXED = LAB / "_fixescratch" / "capabilities.py"
OUT = LAB / "patches" / "V19_1_LOW_CONFLICT_FIXES.patch"
REPO_PATH = "backend/app/capabilities.py"

HEADER = """\
# V19.1 Convergence Red-Team — low-conflict production fixes
#
# THREE changes to backend/app/capabilities.py.  Nothing else is touched.
#
#   1. canonicalize_capabilities: dedup key is (scope, code), not code.
#      -> fixes a REGRESSION: a TRAVELER-scoped and a JOURNEY-scoped need of the
#         same code currently collapse into one row and the second is discarded.
#
#   2. normalize_osm_tags: unwrap a list/tuple used as a mapping value.
#      -> fixes silent tag loss: {"wheelchair": ["yes"]} normalised to
#         {"wheelchair": "['yes']"} and matched nothing downstream.
#
#   3. evaluate_accessibility_requirement: treat step_count / steps /
#      highway=steps as stair evidence.
#      -> fixes wheelchair=yes + step_count=5 being reported as
#         ACCESSIBILITY_UNVERIFIED instead of ACCESSIBILITY_CONFLICT.
#
# Measured on Snapshot C (2026-09-15 13:47:07), scratch copy:
#     before   54 failed / 119 passed / 15 skipped
#     after    46 failed / 127 passed / 15 skipped
# i.e. all 8 new provider-evidence defects fixed, the cross-scope regression
# fixed, and every guard still holds.
#
# Apply from the repository root:
#     git apply --check patches/V19_1_LOW_CONFLICT_FIXES.patch
#     git apply         patches/V19_1_LOW_CONFLICT_FIXES.patch
#
# Generated against the main tree at 13:47:07.  Codex was still editing at
# 13:54; re-run --check before applying.
"""


def blob_id(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()  # noqa: S324


def main() -> int:
    if not BASE.exists() or not FIXED.exists():
        raise SystemExit(f"missing input: {BASE} / {FIXED}")
    old = BASE.read_text(encoding="utf-8")
    new = FIXED.read_text(encoding="utf-8")
    if old == new:
        raise SystemExit("nothing to patch: fixed file is identical to the base")

    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{REPO_PATH}",
        tofile=f"b/{REPO_PATH}",
        n=3,
    )
    body = "".join(diff)

    parts = [HEADER]
    parts.append(f"diff --git a/{REPO_PATH} b/{REPO_PATH}\n")
    parts.append(f"index {blob_id(old.encode())[:7]}..{blob_id(new.encode())[:7]} 100644\n")
    parts.append("--- a/" + REPO_PATH + "\n")
    parts.append("+++ b/" + REPO_PATH + "\n")
    parts.append(body)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # newline="" is mandatory: the default translates "\n" to CRLF on Windows,
    # which puts a stray "\r" on every context line and makes `git apply` fail
    # with "patch does not apply".
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        fh.write("".join(parts))

    added = sum(1 for line in body.splitlines() if line.startswith("+")
                and not line.startswith("+++"))
    removed = sum(1 for line in body.splitlines() if line.startswith("-")
                  and not line.startswith("---"))
    print(f"wrote {OUT}")
    print(f"  +{added} / -{removed} lines in {REPO_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
