<p align="center">
    <img src="docs/assets/codex-skills-architecture-light.svg#gh-light-mode-only" width="100%" alt="Codex-Skills 横版架构 Banner（浅色）" >
    <img src="docs/assets/codex-skills-architecture-dark.svg#gh-dark-mode-only" width="100%" alt="Codex-Skills 横版架构 Banner（深色）" >
</p>

# Codex-Skills

[![Release](https://img.shields.io/github/v/release/JiaxI2/Codex-Skills?label=release)](https://github.com/JiaxI2/Codex-Skills/releases/latest) [![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B%20%7C%207%2B-5391FE?logo=powershell&logoColor=white)](https://learn.microsoft.com/powershell/) [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![License](https://img.shields.io/github/license/JiaxI2/Codex-Skills)](LICENSE)

`Codex-Skills` 是可复用 Codex Skill、AiCoding Plugin 源码、Codex lifecycle hooks 和个人 standalone skills 的源码仓库，也是 AiCoding Git 治理标准的 canonical source。

[中文](README_CN.md) | [English](README_EN.md)

## 项目定位 / Project Positioning

- Skill 源码仓库：维护 `embedded/`、`platform/` 和根目录 standalone skills 的 canonical source。
- Plugin 源码仓库：从 `config/aicoding-plugin-pack.json` 生成 `plugins/AiCoding`，作为可安装的 AiCoding Codex Plugin 包。
- 治理标准源：`platform/aicoding-git-governance/references/aicoding-git-governance-standard.md` 是后续 Git 仓库治理的 canonical URL。
- 运行边界：不把整个仓库作为长期 Skill Root；运行时只暴露明确安装的 standalone skill 或已安装 plugin 中的 `aicoding-*` skill。

## 状态 / Status

- 当前仓库是 Codex skills、AiCoding plugin packaging 和 Git governance standard 的标准源。
- 生成的 plugin 副本是构建产物，不是可手工编辑的源文件。
- README、CHANGELOG、Tag 和 Release 治理均以 `.github/repository-governance.toml` 中的 `[governance_standard]` URL 为同步基准。

## 环境预览 / Environment Preview

| 区域 | 当前默认 | 说明 |
|---|---|---|
| Skill 验证 | PowerShell scripts | [scripts/verify-skills.ps1](scripts/verify-skills.ps1) |
| Plugin 构建 | PowerShell 5.1+ / 7+ | [scripts/build-plugin.ps1](scripts/build-plugin.ps1) |
| Markdown/Release 校验 | Python 3.10+ | [platform/aicoding-git-governance/scripts](platform/aicoding-git-governance/scripts) |
| Git 治理标准 | canonical URL + local lint | [aicoding-git-governance-standard.md](platform/aicoding-git-governance/references/aicoding-git-governance-standard.md) |

## 快速开始 / Quick Start

```powershell
git clone https://github.com/JiaxI2/Codex-Skills.git
cd Codex-Skills
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-skills.ps1
```

- `embedded/` 存放嵌入式领域 skill 源码。
- `platform/` 存放跨领域平台 workflow skill，包括 Git 治理。
- `plugins/AiCoding/skills/` 由 `config/aicoding-plugin-pack.json` 生成，不手工编辑。
- `plugins/AiCoding/hooks/` 是手工维护的 plugin hook 源码。
- `.agents/plugins/marketplace.json` 是本地 plugin 测试用 development marketplace。

## 目录说明 / Repository Navigation

| 路径 | 用途 |
|---|---|
| `embedded/` | 嵌入式固件 skill 族，包括 C99、架构、ARM、DSP、EtherCAT/CiA402、OS、电机控制和评审路由。 |
| `platform/aicoding-git-governance/` | Git-Skill 源码、canonical standard、配置模板、lint 模板和 Release 校验工具。 |
| `platform/aicoding-kit-maintenance/` | Codex-Skills/AiCoding 架构、plugin packaging、submodule、hooks 和完成门禁维护 workflow。 |
| `platform/aicoding-user-skill-creator/` | 创建、验证、改进和迁移 AiCoding user skills 的 workflow。 |
| `external/` | 通过 Git submodule URL 绑定的第三方 standalone Skills；真实入口由 `config/external-skill-bindings.json` 映射。 |
| `plugins/AiCoding/` | 生成/可安装的 Codex plugin 包，包含手工维护 manifest/hooks 和生成的 skills/BUILDINFO。 |
| `config/aicoding-plugin-pack.json` | AiCoding Plugin 打包清单的唯一来源。 |
| `scripts/` | 构建、验证、漂移检查和维护脚本。 |

## 构建和验证 / Build And Verify

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-plugin.ps1 -Plugin AiCoding -Configuration Development -Clean -Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/compare-generated.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage-external-skills.ps1 -Action Status
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-skills.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/lint-git-governance.ps1 -Mode all
```

正式 release build 只应在排除生成 plugin 输出的干净 source tree 中使用 `-Configuration Release`。

## Git 治理标准 / Git Governance Standard

本仓库和后续 AiCoding-governed Git 仓库必须引用同一份 canonical standard：

- 标准文档：[aicoding-git-governance-standard.md](platform/aicoding-git-governance/references/aicoding-git-governance-standard.md)
- GitHub URL：https://github.com/JiaxI2/Codex-Skills/blob/main/platform/aicoding-git-governance/references/aicoding-git-governance-standard.md
- Raw URL：https://raw.githubusercontent.com/JiaxI2/Codex-Skills/main/platform/aicoding-git-governance/references/aicoding-git-governance-standard.md

Commit type taxonomy：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`build`、`ci`、`chore`。

Branch naming and environment mapping：`main` 是稳定基线；`develop`、`feature/*`、`test/*`、`release/*`、`hotfix/*` 分别表示集成、功能、测试、发布和热修复工作。

README 默认中文优先，必须保留 `README_CN.md` / `README_EN.md` 文件级语言切换、环境 badge、Release badge、License badge 和 GitHub About 双语元数据。

Release notes 必须按主类型汇总，包含 Deprecations、Release Notes、Full Changelog、New Contributors 等必要段落；无内容时显式写 `None`。

## 运行时原则 / Runtime Principles

- `aicoding-*` 成组能力通过 AiCoding Plugin 暴露。
- standalone skill 通过用户 Skill Root 的独立目录或链接暴露。
- GitHub 来源 Skill 只通过 `external/` 子模块绑定，并跟随最新稳定 SemVer tag；同步或移除先 dry-run，再显式 `-Apply`。
- 不手工编辑 `plugins/AiCoding/skills/` 或 `plugins/AiCoding/BUILDINFO.json`。
- 不直接修改 Codex plugin cache。

## 文档和支持 / Documentation And Support

- [英文文档](README_EN.md)
- [架构说明](docs/ARCHITECTURE.md)
- [Plugin 开发说明](docs/PLUGIN_DEVELOPMENT.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [问题反馈](https://github.com/JiaxI2/Codex-Skills/issues)
- [许可证](LICENSE)

## 更新日志和发布 / Changelog And Releases

- [更新日志](CHANGELOG.md)
- [最新版本](https://github.com/JiaxI2/Codex-Skills/releases/latest)
- [全部 Release](https://github.com/JiaxI2/Codex-Skills/releases)

diff 摘要应放在 `CHANGELOG.md`、annotated Tag message 或 GitHub Release notes 中，不放在 README 中。

## 维护规则 / Maintenance Rules

- 每个 skill source 只保留一个权威位置；生成的 plugin 副本不是源码。
- GitHub 来源 Skill 不复制进仓库；卸载时同步删除 binding manifest、`.gitmodules` 条目和 gitlink。
- 每次普通 commit 都要评估并更新 `CHANGELOG.md`，且明确 commit type。
- Codex hooks 和 Git hooks 分开维护。
- 不把 `obsidian-*` 打包进 AiCoding。
- 不在 plugin 文件、hooks、scripts 或 README 文件中硬编码个人绝对路径。
- 不在 AiCoding submodule checkout 内重建 AiCoding plugin；应在 Codex-Skills 中构建、提交，再更新 AiCoding submodule pointer。
