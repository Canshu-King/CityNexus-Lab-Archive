"""Emit patches/V19_1_TESTS_ONLY.patch — new test files, nothing else.

The patch adds files under ``backend/tests/`` only, so it applies to the main
tree without touching any production module:

    git apply --check patches/V19_1_TESTS_ONLY.patch
    git apply         patches/V19_1_TESTS_ONLY.patch

Re-run this script after editing anything in ``tests/``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
SRC = LAB / "tests"
OUT = LAB / "patches" / "V19_1_TESTS_ONLY.patch"

FILES = [
    "v191_harness.py",
    "test_v191_capability_contract.py",
    "test_v19_postfix_capability_contract.py",
    "test_v191_eac_evidence_scope.py",
]

HEADER = """\
# V19.1 Convergence Red-Team — tests-only patch
#
# Adds capability contract tests to backend/tests/.  No production module is
# modified by this patch.
#
# Apply from the repository root:
#     git apply --check patches/V19_1_TESTS_ONLY.patch
#     git apply         patches/V19_1_TESTS_ONLY.patch
#
# Run:
#     cd backend && python -m pytest tests/test_v191_capability_contract.py \\
#         tests/test_v19_postfix_capability_contract.py \\
#         tests/test_v191_eac_evidence_scope.py -q
#
# Convention: test_v191_*_guard_* must pass; a failure is a regression.
#             test_v191_*_defect_* documents a known defect; a failure means it
#             was fixed (flip it to a guard when that happens).
#
# Evidence for every assertion: see the round's reports at the lab root,
# in particular EAC_PATCH_VALIDATION.md and
# ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md.
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
