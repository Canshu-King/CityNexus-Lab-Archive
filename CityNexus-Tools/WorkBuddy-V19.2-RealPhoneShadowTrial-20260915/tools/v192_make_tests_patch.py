"""Emit patches/V19_2_TESTS_ONLY.patch — new test files, nothing else.

The patch adds files under ``backend/tests/`` only, so it applies to the main
tree without touching any production module:

    git apply --check patches/V19_2_TESTS_ONLY.patch
    git apply         patches/V19_2_TESTS_ONLY.patch

Re-run this script after editing anything in ``tests/``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
SRC = LAB / "tests"
OUT = LAB / "patches" / "V19_2_TESTS_ONLY.patch"

FILES = [
    "v192_harness.py",
    "test_v192_shadow_trial_gate.py",
]

HEADER = """\
# V19.2 Real-Phone Shadow-Trial Gate — tests-only patch
#
# Adds the shadow-trial gate contract tests to backend/tests/.  No production
# module is modified by this patch.
#
# Apply from the repository root:
#     git apply --check patches/V19_2_TESTS_ONLY.patch
#     git apply         patches/V19_2_TESTS_ONLY.patch
#
# Run:
#     cd backend && python -m pytest tests/test_v192_shadow_trial_gate.py -q
#
# Convention:
#     test_v192_guard_*   must PASS.  A failure is a regression.
#     test_v192_defect_*  documents a known, still-open defect.  A failure means
#                         the defect was fixed — flip it to a guard.
#
# Measured on the V19.2 baseline (capabilities.py 23,668 B /
# sha16 9b68b17997f4cf4e, main.py c17f74c4867a1a1d):
#     37 guards PASS, 24 defects FAIL.
#
# The harness keeps its throwaway SQLite database in the system temp directory
# and disables bytecode writing, so running these tests never writes into the
# repository.
#
# Evidence for every assertion: see the round's reports at the lab root —
# P0_GATE_TABLE.md, NUMERIC_TIME_BOUNDARY_RESULTS.md,
# CAPABILITY_SEMANTICS_RESULTS.md, C4_ANCHOR_AND_IDEMPOTENCY_RESULTS.md,
# MIDTRIP_AND_STALE_LIFECYCLE_RESULTS.md, REGRESSION_LIST.md.
"""


def blob_id(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - git object id


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    parts = [HEADER]
    for name in FILES:
        path = SRC / name
        if not path.exists():
            raise SystemExit(f"missing test file: {path}")
        text = path.read_text(encoding="utf-8")
        data = text.encode("utf-8")
        if not text.endswith("\n"):
            text += "\n"
        lines = text.splitlines()
        parts.append(f"diff --git a/backend/tests/{name} b/backend/tests/{name}\n")
        parts.append("new file mode 100644\n")
        parts.append(f"index 0000000..{blob_id(data)[:7]}\n")
        parts.append("--- /dev/null\n")
        parts.append(f"+++ b/backend/tests/{name}\n")
        parts.append(f"@@ -0,0 +1,{len(lines)} @@\n")
        for line in lines:
            parts.append("+" + line + "\n")
    # newline="" is mandatory: the default translates "\n" to CRLF on Windows,
    # which would put a stray "\r" at the end of every added line.
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        fh.write("".join(parts))
    total = sum((SRC / n).read_text(encoding="utf-8").count("\n") for n in FILES)
    print(f"wrote {OUT}")
    print(f"files: {len(FILES)}  added lines: {total}")
    for name in FILES:
        print(f"  + backend/tests/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
