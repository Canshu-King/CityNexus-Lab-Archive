"""Generate sequential low-conflict V19.1 patches from the isolated lab."""

from __future__ import annotations

import difflib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "snapshot" / "main-tree-20260915T1220"
LAB = ROOT / "lab" / "runtime"
PATCHES = ROOT / "patches"
PATCHES.mkdir(exist_ok=True)


def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def write_patch(path: Path, pieces: list[str]) -> None:
    joiner = chr(10)
    payload = joiner.join(piece.rstrip(joiner) for piece in pieces if piece) + joiner
    path.write_bytes(payload.encode("utf-8"))


def new_file_patch(rel: str, content: str) -> str:
    lines = content.splitlines()
    body = "\n".join("+" + line for line in lines)
    if content.endswith("\n"):
        tail = ""
    else:
        tail = "\n\ No newline at end of file"
    return (
        f"diff --git a/{rel} b/{rel}\n"
        f"new file mode 100644\n"
        f"--- /dev/null\n"
        f"+++ b/{rel}\n"
        f"@@ -0,0 +1,{len(lines)} @@\n"
        f"{body}{tail}\n"
    )


def modified_file_patch(rel: str, old: str, new: str) -> str:
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
        n=3,
    )
    body = "".join(diff)
    if not body:
        return ""
    return f"diff --git a/{rel} b/{rel}\n" + body


def remove_block(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"start marker not found: {start_marker}")
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"end marker not found: {end_marker}")
    return text[:start] + text[end:]


def remove_line(text: str, needle: str) -> str:
    return "\n".join(line for line in text.splitlines() if needle not in line) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    main_rel = "backend/app/main.py"
    baseline_main = read(BASELINE, main_rel)
    final_main = read(LAB, main_rel)

    # state4: no autonomous routes/imports
    state4 = remove_block(
        final_main,
        '@app.get("/api/v1/capabilities/catalog")',
        '@app.get("/api/v1/travelers/{traveler_id}/capabilities")',
    )
    state4 = remove_line(state4, "CapabilityExtractRequest")
    state4 = remove_line(state4, "ACCESSIBILITY_STATES")
    state4 = remove_line(state4, "CAPABILITY_CLASSES")
    state4 = remove_line(state4, "CAPABILITY_SCOPES")
    state4 = remove_line(state4, "CAPABILITY_SEVERITIES")
    state4 = remove_line(state4, "capability_class_for")
    state4 = remove_line(state4, "default_severity")
    state4 = remove_line(state4, "extract_capabilities_from_text")

    # state3: no capability-plan-impact route/import
    state3 = remove_block(
        state4,
        '@app.get("/api/v1/journeys/{journey_id}/capability-plan-impact")',
        '@app.get("/api/v1/travelers/{traveler_id}/traveler-twin")',
    )
    state3 = remove_line(state3, "from app.capability_impacts import build_capability_impacts")

    # state2: no accessibility evidence routes/helpers/imports
    state2 = remove_block(
        state3,
        'def _parse_accessibility_place_tags(place: Any) -> dict[str, Any]:',
        '@app.get("/api/v1/travelers/{traveler_id}/traveler-twin")',
    )
    state2 = remove_line(state2, "from app.integrations.accessibility.osm import evidence_from_osm_tags, overall_accessibility_state")
    state2 = remove_line(state2, "from collections.abc import Mapping")

    for label, text in (("state2", state2), ("state3", state3), ("state4", state4)):
        tmp = ROOT / f"._patch_{label}.py"
        tmp.write_text(text, encoding="utf-8")
        print(label, len(text.splitlines()), "lines")

    groups: dict[str, list[str]] = {
        "01_LIVE_CAPABILITY_ADAPTER": [],
        "02_ACCESSIBILITY_EVIDENCE_REFERENCE": [],
        "03_CAPABILITY_EXPERIENCE_INTEGRATION": [],
        "04_PERFORMANCE_PWA_A11Y": [],
        "05_AUTONOMOUS_IMPROVEMENTS": [],
    }

    # 01: import fix + capability contract hardening + base/live frontend adapters
    groups["01_LIVE_CAPABILITY_ADAPTER"].append(modified_file_patch(main_rel, baseline_main, state2))
    groups["01_LIVE_CAPABILITY_ADAPTER"].append(
        modified_file_patch("backend/app/capabilities.py", read(BASELINE, "backend/app/capabilities.py"), read(LAB, "backend/app/capabilities.py"))
    )
    for rel in [
        "frontend/src/features/capability-experience/types.ts",
        "frontend/src/features/capability-experience/copy.ts",
        "frontend/src/features/capability-experience/evidence.ts",
        "frontend/src/features/capability-experience/adapter.ts",
        "frontend/src/features/capability-experience/recordedFixture.ts",
        "frontend/src/features/capability-experience/styles/capability-experience.css",
        "frontend/src/features/capability-experience/README.md",
        "frontend/src/features/capability-experience/liveShadowAdapter.ts",
        "frontend/src/features/capability-experience/livePlanAdapter.ts",
        "frontend/src/features/capability-experience/providerEvidence.ts",
    ]:
        groups["01_LIVE_CAPABILITY_ADAPTER"].append(new_file_patch(rel, read(LAB, rel)))

    # 02: accessibility provider evidence reference
    groups["02_ACCESSIBILITY_EVIDENCE_REFERENCE"].append(modified_file_patch(main_rel, state2, state3))
    groups["02_ACCESSIBILITY_EVIDENCE_REFERENCE"].append(
        modified_file_patch(
            "backend/app/replanning/feasibility.py",
            read(BASELINE, "backend/app/replanning/feasibility.py"),
            read(LAB, "backend/app/replanning/feasibility.py"),
        )
    )
    for rel in [
        "backend/app/integrations/accessibility/__init__.py",
        "backend/app/integrations/accessibility/osm.py",
        "backend/tests/test_v19_1_accessibility_evidence.py",
        "data/accessibility/evidence_cases.json",
        "frontend/src/features/capability-experience/components/ProviderEvidencePanel.tsx",
    ]:
        groups["02_ACCESSIBILITY_EVIDENCE_REFERENCE"].append(new_file_patch(rel, read(LAB, rel)))

    # 03: capability experience integration
    groups["03_CAPABILITY_EXPERIENCE_INTEGRATION"].append(modified_file_patch(main_rel, state3, state4))
    for rel in [
        "backend/app/capability_impacts.py",
        "frontend/src/features/capability-experience/CapabilityShadowExperience.tsx",
        "frontend/src/features/capability-experience/components/EvidenceBadge.tsx",
        "frontend/src/features/capability-experience/components/JourneySetupNeeds.tsx",
        "frontend/src/features/capability-experience/components/CopilotNeedsConfirmation.tsx",
        "frontend/src/features/capability-experience/components/CapabilityPlanExplanation.tsx",
        "frontend/src/features/capability-experience/components/RecoveryDiffCapability.tsx",
        "frontend/src/features/capability-experience/components/TwinCapabilitySummary.tsx",
        "frontend/src/features/capability-experience/components/MobileCapabilityShield.tsx",
        "frontend/src/features/capability-experience/components/CapabilityMapOverlay.tsx",
    ]:
        groups["03_CAPABILITY_EXPERIENCE_INTEGRATION"].append(new_file_patch(rel, read(LAB, rel)))

    # 04: performance/PWA/a11y lab and tests
    for path in sorted((ROOT / "shadow-app").rglob("*")):
        if path.is_file() and not ({"node_modules", "dist", "__pycache__", ".vite", ".vite-temp"} & set(path.parts)):
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            groups["04_PERFORMANCE_PWA_A11Y"].append(new_file_patch(rel, path.read_text(encoding="utf-8")))
    for rel in [
        "tests/playwright.config.ts",
        "tests/v19_1_shadow.spec.ts",
        "tests/package.json",
        "PERFORMANCE_PWA_A11Y_RESULTS.md",
    ]:
        groups["04_PERFORMANCE_PWA_A11Y"].append(new_file_patch(rel, read(ROOT, rel)))

    # 05: autonomous
    groups["05_AUTONOMOUS_IMPROVEMENTS"].append(modified_file_patch(main_rel, state4, final_main))
    groups["05_AUTONOMOUS_IMPROVEMENTS"].append(
        modified_file_patch(
            "backend/app/schemas.py",
            read(BASELINE, "backend/app/schemas.py"),
            read(LAB, "backend/app/schemas.py"),
        )
    )
    for rel in [
        "backend/tests/test_v19_1_capabilities.py",
        "AUTONOMOUS_BACKLOG_DECISIONS.md",
        "tools/v19_1_shadow_flows.py",
    ]:
        source_root = LAB if (LAB / rel).exists() else ROOT
        groups["05_AUTONOMOUS_IMPROVEMENTS"].append(new_file_patch(rel, read(source_root, rel)))

    manifest = {}
    for name, pieces in groups.items():
        path = PATCHES / f"{name}.patch"
        write_patch(path, pieces)
        manifest[name] = {"bytes": path.stat().st_size, "lines": len(path.read_text(encoding="utf-8").splitlines())}
        print(name, manifest[name])
    (PATCHES / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("wrote patches")
    for tmp in ROOT.glob("._patch_state*.py"):
        tmp.unlink()


if __name__ == "__main__":
    main()
