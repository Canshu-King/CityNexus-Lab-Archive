from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy low-conflict post-WP04 foundation files into a CityNexus repo."
    )
    parser.add_argument("repo", type=Path)
    parser.add_argument("--apply", action="store_true", help="Actually copy files. Default is dry-run.")
    args = parser.parse_args()

    package_root = Path(__file__).resolve().parents[1]
    source = package_root / "backend_overlay"
    repo = args.repo.resolve()

    if not (repo / "backend" / "app").exists():
        raise SystemExit("Expected existing CityNexus backend/app directory")

    allowed_prefixes = (
        Path("app/intelligence"),
        Path("app/integrations/provider_status.py"),
        Path("app/integrations/provider_config.py"),
        Path("app/integrations/registry.py"),
        Path("app/integrations/mobility"),
        Path("app/integrations/context"),
        Path("app/integrations/discovery"),
        Path("app/integrations/ai"),
        Path("app/integrations/trust"),
        Path("app/planning"),
        Path("tests/test_foundation_reason_codes.py"),
        Path("tests/test_foundation_opportunity_window.py"),
        Path("tests/test_foundation_replan_diff.py"),
        Path("tests/test_foundation_routingpy_adapter.py"),
        Path("tests/test_foundation_http_adapters.py"),
        Path("tests/test_foundation_planner_adapter.py"),
        Path("tests/test_foundation_registry.py"),
        Path("tests/test_foundation_discovery_pipeline.py"),
    )

    candidates: list[tuple[Path, Path]] = []
    for file in source.rglob("*"):
        if not file.is_file():
            continue
        rel = file.relative_to(source)
        if not any(rel == prefix or prefix in rel.parents for prefix in allowed_prefixes):
            continue
        target = repo / "backend" / rel
        candidates.append((file, target))

    conflicts = [target for source_file, target in candidates if target.exists() and target.read_bytes() != source_file.read_bytes()]
    if conflicts:
        print("CONFLICTS: existing files differ; do not overwrite blindly:")
        for path in conflicts:
            print(f"  {path}")
        raise SystemExit(2)

    for source_file, target in candidates:
        print(f"{'COPY' if args.apply else 'WOULD COPY'} {source_file.relative_to(package_root)} -> {target}")
        if args.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)

    if not args.apply:
        print("Dry-run only. Re-run with --apply after WP04 external PASS and manual conflict review.")


if __name__ == "__main__":
    main()
