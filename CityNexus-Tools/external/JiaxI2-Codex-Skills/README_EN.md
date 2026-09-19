<p align="center">
    <img src="docs/assets/codex-skills-architecture-light.svg#gh-light-mode-only" width="100%" alt="Codex-Skills 横版架构 Banner（浅色）" >
    <img src="docs/assets/codex-skills-architecture-dark.svg#gh-dark-mode-only" width="100%" alt="Codex-Skills 横版架构 Banner（深色）" >
</p>

# Codex-Skills

[![Release](https://img.shields.io/github/v/release/JiaxI2/Codex-Skills?label=release)](https://github.com/JiaxI2/Codex-Skills/releases/latest) [![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B%20%7C%207%2B-5391FE?logo=powershell&logoColor=white)](https://learn.microsoft.com/powershell/) [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![License](https://img.shields.io/github/license/JiaxI2/Codex-Skills)](LICENSE)

`Codex-Skills` is the source repository for reusable Codex skills, AiCoding plugin sources, Codex lifecycle hooks, standalone personal skills, and the canonical AiCoding Git governance standard.

[中文](README_CN.md) | [English](README_EN.md)

## Project Positioning

- Skill source repository for `embedded/`, `platform/`, and root-level standalone skills.
- Plugin source repository for generating `plugins/AiCoding` from `config/aicoding-plugin-pack.json`.
- Governance source repository for `platform/aicoding-git-governance/references/aicoding-git-governance-standard.md`.
- Runtime boundary: do not expose this whole repository as a long-term Skill Root; expose installed standalone skills or the installed AiCoding plugin.

## Status

- Canonical source tree for Codex skills, AiCoding plugin packaging, and Git governance.
- Generated plugin copies are build outputs, not editable source.
- README, CHANGELOG, Tag, and Release governance track the `[governance_standard]` URL in `.github/repository-governance.toml`.

## Environment Preview

| Area | Default | Reference |
|---|---|---|
| Skill verification | PowerShell scripts | [scripts/verify-skills.ps1](scripts/verify-skills.ps1) |
| Plugin build | PowerShell 5.1+ / 7+ | [scripts/build-plugin.ps1](scripts/build-plugin.ps1) |
| Markdown/Release validation | Python 3.10+ | [platform/aicoding-git-governance/scripts](platform/aicoding-git-governance/scripts) |
| Git governance standard | canonical URL + local lint | [aicoding-git-governance-standard.md](platform/aicoding-git-governance/references/aicoding-git-governance-standard.md) |

## Quick Start

```powershell
git clone https://github.com/JiaxI2/Codex-Skills.git
cd Codex-Skills
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-skills.ps1
```

- `embedded/` contains embedded-domain skill sources.
- `platform/` contains cross-domain platform workflow skills, including Git governance.
- `plugins/AiCoding/skills/` is generated from `config/aicoding-plugin-pack.json`; do not edit it by hand.
- `plugins/AiCoding/hooks/` is manually maintained plugin hook source.
- `.agents/plugins/marketplace.json` is the development marketplace for local plugin testing.

## Repository Navigation

| Path | Purpose |
|---|---|
| `embedded/` | Embedded firmware skill family. |
| `platform/aicoding-git-governance/` | Git-Skill source, canonical standard, governance templates, lint templates, and release validators. |
| `platform/aicoding-kit-maintenance/` | Codex-Skills/AiCoding architecture, plugin packaging, submodule, hook, and completion-gate maintenance workflow. |
| `platform/aicoding-user-skill-creator/` | Workflow for creating, validating, improving, and migrating AiCoding user skills. |
| `external/` | Third-party standalone Skills URL-bound as Git submodules; `config/external-skill-bindings.json` maps the real Skill directory. |
| `plugins/AiCoding/` | Generated/installable Codex plugin package. |
| `config/aicoding-plugin-pack.json` | Single source for the AiCoding plugin package list. |
| `scripts/` | Build, validation, drift-check, and maintenance scripts. |

## Build And Verify

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-plugin.ps1 -Plugin AiCoding -Configuration Development -Clean -Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/compare-generated.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage-external-skills.ps1 -Action Status
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-skills.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/lint-git-governance.ps1 -Mode all
```

Use `-Configuration Release` only from a clean source tree that excludes generated plugin outputs.

## Git Governance Standard

This repository and future AiCoding-governed repositories must reference the same canonical standard:

- Standard document: [aicoding-git-governance-standard.md](platform/aicoding-git-governance/references/aicoding-git-governance-standard.md)
- GitHub URL: https://github.com/JiaxI2/Codex-Skills/blob/main/platform/aicoding-git-governance/references/aicoding-git-governance-standard.md
- Raw URL: https://raw.githubusercontent.com/JiaxI2/Codex-Skills/main/platform/aicoding-git-governance/references/aicoding-git-governance-standard.md

Commit type taxonomy: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.

Branch naming and environment mapping: `main` is the stable baseline; `develop`, `feature/*`, `test/*`, `release/*`, and `hotfix/*` represent integration, feature, test, release, and hotfix work.

README defaults to Chinese-first and must keep `README_CN.md` / `README_EN.md` file-level language switching, environment badges, Release badge, License badge, and bilingual GitHub About metadata.

Release notes must group changes by primary type and include Deprecations, Release Notes, Full Changelog, New Contributors, and other required sections. Use `None` when a section has no applicable content.

## Runtime Principles

- `aicoding-*` capabilities are exposed as a group through the AiCoding plugin.
- Standalone skills are exposed through explicit user Skill Root directories or links.
- GitHub-sourced Skills are bound only through `external/` submodules and follow the latest stable SemVer tag; sync and removal are dry-run first and require explicit `-Apply`.
- Do not edit `plugins/AiCoding/skills/` or `plugins/AiCoding/BUILDINFO.json` by hand.
- Do not modify the Codex plugin cache directly.

## Documentation And Support

- [Chinese documentation](README_CN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Plugin development](docs/PLUGIN_DEVELOPMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Issue tracker](https://github.com/JiaxI2/Codex-Skills/issues)
- [License](LICENSE)

## Changelog And Releases

- [CHANGELOG](CHANGELOG.md)
- [Latest Release](https://github.com/JiaxI2/Codex-Skills/releases/latest)
- [All Releases](https://github.com/JiaxI2/Codex-Skills/releases)

Diff summaries belong in `CHANGELOG.md`, annotated Tag messages, or GitHub Release notes, not README.

## Maintenance Rules

- Keep each skill source in one place; generated plugin copies are not source.
- Do not copy GitHub-sourced Skills into the repository; uninstall removes the binding manifest entry, `.gitmodules` section, and gitlink together.
- Update `CHANGELOG.md` for every normal commit and mark the commit type explicitly.
- Keep Codex hooks and Git hooks separate.
- Do not package `obsidian-*` into AiCoding.
- Do not hard-code personal absolute paths in plugin files, hooks, scripts, or README files.
- Do not rebuild the AiCoding plugin from inside the AiCoding submodule checkout; build in Codex-Skills, commit, then update the AiCoding submodule pointer.
