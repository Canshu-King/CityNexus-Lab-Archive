"""Package the V19.1 Autonomous Product Lab deliverable."""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = Path("D:/moodle/CityNexus-Tools/CityNexus-DSH-EAC-V19.1-AutonomousProductLab-20260915.zip")

INCLUDE = [
    "citynexus_dsheac_v19_1_autonomous_product_lab",
    "patches",
    "evidence",
    "tests",
    "shadow-app",
    "tools",
    "lab/runtime/frontend/src/features/capability-experience",
    "lab/runtime/frontend/src/types/react-shims.d.ts",
    "lab/runtime/frontend/tsconfig.v19_1_feature.json",
    "lab/runtime/backend/app/integrations/accessibility",
    "lab/runtime/data/accessibility/evidence_cases.json",
    "DSH_EAC_V19_1_AUTONOMOUS_PRODUCT_LAB_REPORT.md",
    "LIVE_CAPABILITY_CONTRACT_MAP.md",
    "ACCESSIBILITY_PROVIDER_EVIDENCE_REPORT.md",
    "SHADOW_INTEGRATION_RESULTS.md",
    "WEB_MOBILE_LIVE_RESULTS.md",
    "PERFORMANCE_PWA_A11Y_RESULTS.md",
    "AUTONOMOUS_BACKLOG_DECISIONS.md",
    "CODEX_MERGE_GUIDE_V19_1.md",
    "SNAPSHOT_MANIFEST.json",
    "SHADOW_APP_RUN.md",
]

EXCLUDE_PARTS = {"node_modules", "dist", "test-results", "__pycache__", ".git", ".vite", ".vite-temp"}


def iter_files(path: Path):
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*")):
        if child.is_file() and not (EXCLUDE_PARTS & set(child.parts)):
            yield child


def main() -> None:
    if ZIP.exists():
        ZIP.unlink()
    files = []
    for rel in INCLUDE:
        source = ROOT / rel
        if not source.exists():
            raise SystemExit(f"missing include: {rel}")
        files.extend(iter_files(source))
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"wrote {ZIP} ({ZIP.stat().st_size} bytes, {len(set(files))} files)")


if __name__ == "__main__":
    main()
