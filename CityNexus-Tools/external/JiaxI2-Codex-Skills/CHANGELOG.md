# 更新日志

## 2026-08-21

### 更新 / Changed

- **docs(c99)**：补强嵌入式 C99 函数命名、入参与函数/回调设计契约：新函数使用 `snake_case`，不超过 32 个字符、默认不超过两个下划线且每词不超过 12 个字符，多词模块使用统一短前缀；参数按上下文、输入、输出分组，超过 5 个进入设计审查而非机械封装；复杂度指标改为人工审查信号，并将可机器检查的名称形态与必须人工判断的职责、内聚性和生命周期明确分流；strengthen C99 naming, parameter, function, and callback contracts while keeping semantic design review human-owned.
- **build(plugin)**：从干净的 `57f8e1e` canonical source 重新生成 AiCoding Plugin，同步 C99 函数接口规则并记录 `dirtySource=false`；regenerate the AiCoding package from the verified C99 source commit and preserve clean build metadata.

## 2026-08-18

### 新增 / Added

- **feat(external-skill)**：以共享 Git submodule 将 `mattpocock/skills` 最新稳定版本 `v1.2.3` 固定到 `external/mattpocock-skills`，并按其正式 plugin 清单映射 25 个 engineering/productivity Skills；pin the latest stable upstream release and expose only its published Skill set through explicit nested paths.

### 更新 / Changed

- **build(plugin)**：从干净的 `8e15779` canonical source commit 重新生成 AiCoding Plugin，将共享外部仓库生命周期规则同步到 packaged `aicoding-kit-maintenance`，并记录 `dirtySource=false`；regenerate the package from the clean canonical source commit and preserve clean build metadata.
- **fix(external-skill)**：外部 Skill 生命周期现在支持一个上游仓库承载多个 Skill；同步只抓取一次共享 submodule，移除单个 binding 时保留仍被其他 binding 使用的 `.gitmodules` section 和 gitlink，最后一个 binding 移除时再清理仓库链接；support shared-repository bindings without redundant fetches or premature submodule removal.

## 2026-07-27

### 更新 / Changed

- **build(plugin)**：从干净的 `2a4a67c` canonical 源树重新生成 AiCoding Plugin，纳入架构 Skill 新增的规范、模板、检查脚本、治理章节与嵌入式路由更新，并将 `BUILDINFO.json` 固化为 `dirtySource=false`；regenerate the official AiCoding package from the clean canonical source tree and record clean build metadata.
- **fix(embedded-architecture)**：将门禁规则与人工反馈确认拆为独立治理章节，使 standard/workflow Skill 契约可由 `skill_gate.py validate` 阻断验证；split gate rules and human confirmation into independently verifiable governance sections.
- **feat(embedded-architecture)**：把架构 skill 重建为按 ID 引用的规范体系（`AP-*` 原则、`SL-*` 语义角色、`DR-*`/`GATE-*` 规则门禁、`AM-*` 方法、`PAT-*` 模式、`SYN-*` 成熟度、`SIG-*` 泄漏信号），新增 `document-architecture.json` 与自校验脚本强制单一所有权、依赖无环、链接与声明一致、锚点有效和 ID 唯一归属；rebuild the embedded architecture skill around a self-validating ID system.
- **feat(embedded-architecture)**：新增 `check_layering.ps1` 分层检查器，按语义角色而非目录名校验依赖方向、公共头环境纯度、组合根可见性，并给出过度抽象（`DR-012`）与"一条映射盖住契约+实现两个角色"（`DR-014`）警告；配置来自项目自身，脚本不含任何仓库路径；add a project-decoupled layering checker driven by the project's own role map.
- **fix(embedded-architecture)**：把工具明确置于人工判断的下游——「哪些是用户代码」「什么算环境类型」「目录意图」均非脚本可推断，故 `external_include_patterns`、`forbidden_public_types`、`analysis_confirmed_by` 或规则 `evidence` 缺失时拒绝给出结论并返回 2，不再静默报 0；新增 `-Evidence` 只抓事实模式与 `AM-011` 分析先行方法；make the checker refuse to conclude on incomplete judgement inputs instead of silently reporting zero.

## 2026-07-23

### 更新 / Changed

- **docs(git-readme)**：修正架构图小bug.

## 2026-07-22

### 更新 / Changed

- **fix(git-governance)**：在 Windows PowerShell 5 中按退出码捕获 README 治理验证器的预期 stderr，使缺徽章、能力漂移、四象限、凭据和 Mermaid 负例能够继续执行并断言错误码；capture expected validator stderr without terminating the negative-case matrix on Windows PowerShell 5.
- **docs(architecture)**：新增由单一 Diagram IR 生成的横版 Visio 架构图，以 light/dark SVG 和 GitHub `#gh-light-mode-only` / `#gh-dark-mode-only` 标记实现主题 Banner；README、README_CN、README_EN、移动端和远程端复用同一资产对，并支持点击阅读原图；add one semantic Visio source with theme-aware SVG Banners shared by every README surface.
- **feat(git-governance)**：将 canonical 标准升至 `2026.07.22`，加入可选的 README 三层结构、技术栈徽章投影、可再生双主题 banner、Mermaid 架构图、能力橱窗、四象限演进与安全 Star History profile；add portable opt-in README profiles while keeping repositories without the new TOML sections behavior-compatible.
- **test(git-governance)**：新增仓库中立 adapter 契约与非 AiCoding fixture，覆盖旧 TOML 兼容、版本徽章、能力缺行/幽灵行、四象限、Star History 凭据和 Mermaid 节点/命令负例；exercise portable README policy without coupling the standard to the AiCoding Kit registry.

## 2026-07-16

### 更新 / Changed

- **fix(plugin-buildinfo)**：将生成包中的 HTML 纳入稳定文本换行归一化，并按 ordinal 相对路径排序计算树摘要，消除 Windows PowerShell 与 `pwsh` 的文化排序差异；同时从当前源码重新生成 `BUILDINFO.json`，使 fresh worktree 重建和 installed-cache 漂移检查都对应同一 19-Skill 发布包；normalize generated HTML and use ordinal relative-path ordering so both PowerShell runtimes produce the same package digest.
- **feat(visio-diagram)**：新增通用 standalone `visio-diagram` Skill，以精简入口和按需 references 覆盖工程/控制框图、泳道图、流程图与状态机，并明确不包含时序图工作流；add a progressively loaded generic Visio workflow without coupling it to the AiCoding plugin.
- **fix(visio-diagram)**：将侧边中心/多端口车道、双端 glue、正交路由以及文字不得覆盖连接线、框线或其他文字设为阻断门禁；make connector geometry and text-clearance failures block final export.
- **fix(visio-diagram)**：新增紧凑布局、同轴可统一尺寸、逐维内容/端口尺寸包络、容器有界 padding，以及箭头头尾不得穿入节点的阻断规则；add measurable compactness, bounded sizing, container, and arrow-clearance gates.
- **fix(visio-diagram)**：新增连接文字相对中点锚定和有界漂移、框体外部标题绑定、profile Latin/Asian 字体、普通框 80% 文本安全区与真实检查门禁；add bounded label/caption anchors, requested fonts, and measured text-safe-area checks.
- **feat(visio-diagram)**：新增渐进加载的精简 JSON 样式 reference，仅暴露字体组、默认字号、文字安全区、线宽和圆角，默认保持早期紧凑视觉；标版字号仅按元素显式应用，并以真实字号/线宽/圆角门禁验证；add restrained configurable typography and line-style standards without global restyling.
- **fix(visio-diagram)**：同轴同尺寸族连续节点的框间距改用页面绝对边界检查，组内差值超过 `0.03 in` 即阻断；enforce equal absolute boundary gaps for comparable same-axis nodes.
- **docs(visio-diagram)**：吸收 Visiomaster 的场景契约、renderer-effective 字段和双阶段视觉回归思想，新增精简按需复刻/回归 reference，并明确不复制其品牌与在线标签缺陷；adapt the useful source-driven and no-op review loop without importing upstream coupling.
- **build(visio-diagram)**：补齐 consistent-workflow 类型、Workflow Contract、Gate Rules 与人工 PNG 复核契约；make the standalone workflow satisfy repository Skill governance.

## 2026-07-15

### 新增 / Added

- **feat(external-skill)**：以嵌套 Git submodule 将 Agents365-ai `drawio-skill` 最新稳定 tag `v1.34.0` 绑定到 `external/drawio-skill`，并通过 `config/external-skill-bindings.json` 映射真实入口 `skills/drawio-skill`；bind the latest stable upstream draw.io release without maintaining copied source.
- **feat(external-skill)**：新增 `scripts/manage-external-skills.ps1`，支持外部 Skill 稳定版本状态、同步更新和同步移除 manifest/`.gitmodules`/gitlink；add dry-run-first lifecycle management for URL-bound Skills.
- **fix(external-skill)**：同步操作会暂存新的 gitlink，卸载操作通过标准 `git rm` 原子更新 `.gitmodules` 并检查关键子命令结果；make sync and uninstall changes commit-ready and fail fast.
- **build(governance)**：规定后续所有 GitHub 来源 Skill 必须通过 `external/` 子模块链集成，并由 `verify-skills.ps1` 校验 gitlink、URL、稳定 tag、Skill 子路径和 frontmatter 名称；enforce latest-stable URL-bound integration for future GitHub sources.
- **refactor(drawio)**：移除仓库内旧的复制版 `drawio/`，由上游 URL 绑定的 `drawio-skill` 替代；replace the legacy copied Skill with the maintained upstream source.

## 2026-07-08

### 更新 / Changed

- **docs(c99)**：明确 C99 修改记录中的作者字段默认使用 `HU JIAXUAN`，但项目已有负责人、作者或文件头规则时按项目规范替换；clarify the default C99 change-record author while preserving project-specific owner and file-header rules.
- **docs(readme)**：治理 README/README_CN，移除个人本地绝对路径，补充英文 Runtime Principles 和中文 Release 链接，并扩展 lint 以检查 README 双语治理与本地路径泄漏；govern README/README_CN, remove personal local paths, add runtime/release links, and extend lint for bilingual README governance.
- **docs(readme)**：将 README/README_CN 收敛到同一 `minimal-internal` profile，补齐状态、快速开始、文档支持、更新日志和发布入口，并让 lint 按同一 profile 校验双语 README；align README/README_CN to one `minimal-internal` profile and enforce the same profile in lint.
- **docs(git-governance)**：建立统一 Git 治理 canonical URL，同步 README 默认中文首页、README_CN/README_EN 文件级分流、环境 badge、GitHub About 和 lint 模板，后续仓库必须通过 `[governance_standard]` 引用同一标准；establish the canonical Git governance URL and enforce Chinese-first README, README_CN/README_EN switching, environment badges, GitHub About, and lint templates for future repositories.
## 2026-06-27

### 新增 / Added
- **feat(git-governance)**：为 Codex-Skills 本仓库新增 `.githooks/`、`.github/repository-governance.toml` 和 `scripts/lint-git-governance.ps1`，把 README 中文链接、Git 治理标准、commit type 和 Release typed summary 规则接入当前 Git hook；wire the governance lint into this repository Git hook.
- **feat(git-governance)**：新增 `assets/lint-git-governance.ps1` hook/lint 模板，机器检查 README 中文链接、Git 治理标准、commit type 和 Release typed summary 规则；add a reusable hook/lint template that enforces README Chinese-link, Git governance, commit type, and release typed-summary rules.
- **docs(git-governance)**：补充分支命名、环境映射、commit type、单次提交约束和 Release typed commit summary 标准，要求所有 AiCoding 管理仓库在 README 或等价治理文档中写明；document branch/environment, commit type, single-commit, and release typed-summary standards for all AiCoding-governed repositories.
- **docs(repo)**：新增 Apache-2.0 `LICENSE`、`CONTRIBUTING.md`、`SECURITY.md` 和 `CITATION.cff`，补齐 GitHub About 侧栏可识别的仓库元数据文件；add repository metadata files recognized by GitHub About.
- **docs(git-governance)**：要求存在 `README_CN.md` 时 `README.md` 顶部提供显眼中文文档链接，并更新 Codex-Skills README 顶部链接为中英双语；require a visible top-of-file Chinese documentation link in `README.md` when `README_CN.md` exists.

- **feat(platform)**：新增 AiCoding SDD/MVP/BDD/架构优先/TDD fallback/文档同步 workflow skills 与共享 references，并将其纳入 AiCoding Plugin 打包清单；add standalone-capable SDD, MVP, BDD, architecture-first, TDD fallback, documentation synchronization workflow skills and shared references, and package them in the AiCoding Plugin.

## 2026-06-26

### 新增 / Added

- **docs**：新增 `README_CN.md` 中文入口，并在 `README.md` 链接中文说明；add a Chinese README entry and link it from the English README.

### 更新 / Changed

- **docs**：更新 `aicoding-git-governance` 的 README、CHANGELOG、Tag 和 GitHub Release 语言策略，默认采用中文优先的中英双语治理；update Git-Skill governance so README, CHANGELOG, Tag, and Release workflows default to bilingual Chinese/English handling.
- **fix(build)**：规范化 AiCoding Plugin 生成文本和 BUILDINFO digest，避免新 clone 或不同换行策略导致构建漂移；normalize generated plugin text and BUILDINFO digests so fresh clones do not drift because of line endings.
- **build**：新增 .gitattributes 约束并重新归一化 generated plugin 文本，确保新电脑 checkout 后重复构建不产生换行漂移；add generated plugin eol attributes and renormalize package text for clean fresh-checkout rebuilds.

### 修复

- **fix(skill)**：修复 `aicoding-git-governance` workflow contract 中残留的字面量换行标记，保持 canonical source 与生成 plugin 文档格式一致；fix the literal newline marker in the Git governance Skill workflow contract so canonical source and generated plugin docs render consistently.

- **fix(tooling)**：修复 `scripts/compare-generated.ps1` 对 `plugins/AiCoding/BUILDINFO.json` 的非自引用构建模型误报；漂移检查现在比较 BUILDINFO 稳定字段，并按字节恢复可变元数据，避免 `sourceCommit`、`sourceTag`、`buildTimestampUtc` 和 `dirtySource` 造成重复构建漂移。
## 2026-06-25

### 新增

- **feat**：新增 `platform/aicoding-kit-maintenance/`，定义 Codex-Skills/AiCoding 双仓库维护流程，明确 AGENTS 边界、架构文档、config/scripts 执行入口以及 Git hooks/CI 完成门禁。
- **docs**：新增根 `AGENTS.md`、`plugins/AiCoding/AGENTS.md` 和 `docs/PLUGIN_DEVELOPMENT.md`，明确人工维护区、自动生成区、Hook 辅助边界和跨仓库发布顺序。
- 新增 `skill-creator/`，将原 Anthropic skill creator 迁移为 Codex/OpenCode Agent Skill 创建、迁移和验证工作流。
- 新增 `platform/aicoding-user-skill-creator/scripts/skill_gate.py`，用于判断是否应该创建 skill、分类四类 skill，并阻塞缺失 workflow contract、gate rules 或人工确认的标准/流程类 skill。

### 更新

- 更新 `embedded/C99/`，把 C99 编码规范补充为 `consistent-workflow`、`organization-standard` 和 `team-expertise` 类型，并要求可机器检查规则落成 CLI/Hook/Lint/CI 门禁。
- 更新 `embedded/architecture/`，把架构平台化规范补充为四类 skill，并要求架构边界、发布门禁和量产约束优先机器化为阻塞规则。
- 更新 `README.md`，加入 `platform/aicoding-user-skill-creator/` 目录说明，并改为依赖 Git 管理 user-level skill 变更，避免散落临时备份。
- **docs**：更新 `embedded/git/` 提交治理规则，要求每次提交明确 `feat/fix/docs/style/refactor/perf/test/chore/build/ci` 类型，在 CHANGELOG 记录类型和影响，并通过 lint/hook 管理提交消息与 CHANGELOG 门禁。
- **docs**：新增 `embedded/git/references/repository-initialization.md`，把 Git 仓库初始化标准化为本地同步空远程、远程优先绑定本地、克隆已有远程、本地引导、模板引导和 submodule 感知初始化，并要求通过 CLI 配置 `.githooks` 后运行 hook/lint 验证。
- **docs**：补充大厂式 Git 分支/环境映射和单次提交纪律，覆盖 `main/develop/feature/test/release/hotfix`、`DEV/FAT/UAT/PRO`、同类提交、不超过 3 个议题以及禁止默认使用破坏性 reset。
- **feat**：新增 `plugins/AiCoding/`，按 Codex 官方 plugin 结构生成扁平化 `aicoding-*` skills、Codex lifecycle hooks 和 `BUILDINFO.json`，用于新电脑安装 AiCoding 嵌入式 Codex kit。
- **refactor**：将 `embedded/git/` 迁移为 `platform/aicoding-git-governance/`，把 Git-Skill 明确归类为跨领域平台治理能力。
- **build**：新增 `config/aicoding-plugin-pack.json`、`scripts/build-plugin.ps1`、`scripts/verify-plugin.ps1`、`scripts/compare-generated.ps1` 和 `scripts/verify-skills.ps1`，支持可重复构建、生成目录校验和构建漂移检查。
- **docs**：新增 `docs/ARCHITECTURE.md`，明确人工维护目录与自动生成目录、BUILDINFO 非自引用模型、local plugin 缓存刷新方式、CodingKit 外部资产发现协议、Hook 辅助边界以及禁止 AiCoding 在 submodule 中重新构建 Plugin。
- **docs**：将 `embedded/git/` 的 skill 名称从 `embedded-git-workflow` 改为 `Git-Skill`（frontmatter `name: git-skill`），保留嵌入式路径定位，同时说明其嵌入式优先、可通用的 Git 治理边界。

### 移除

- 移除旧的 `anthropic-skill-creator/` 路径，后续统一使用 `skill-creator/`。
## 2026-06-22

### 新增

- **feat**：新增 `platform/aicoding-kit-maintenance/`，定义 Codex-Skills/AiCoding 双仓库维护流程，明确 AGENTS 边界、架构文档、config/scripts 执行入口以及 Git hooks/CI 完成门禁。
- **docs**：新增根 `AGENTS.md`、`plugins/AiCoding/AGENTS.md` 和 `docs/PLUGIN_DEVELOPMENT.md`，明确人工维护区、自动生成区、Hook 辅助边界和跨仓库发布顺序。
- 新增 `embedded/git/`，覆盖嵌入式仓库分支、提交、PR、Tag、Release、README、CHANGELOG、版本文件、固件制品、测试基线、生产基线和客户交付治理。
- 新增 EtherCAT 开源项目与 MCP 设计参考，包含 SOEM/IgH、SSC/SOES、CiA402 开源实现、TwinCAT/LinuxCNC/ROS2 诊断、项目选型和维护路线。

### 更新

- 更新 `embedded/SKILL.md`、`embedded/readme.md` 和 `embedded/agents/openai.yaml`，将 Git/发布治理纳入嵌入式 skill 路由。
- 扩展 `embedded/ethercat/SKILL.md`、`embedded/ethercat/README.md` 和评估数据，增加新增参考资料的读取规则。
- `.gitignore` 增加 `*.bak-*`，避免本地备份文件误提交。
- 从 `README.md` 移除日期型 diff 摘要，并在 `embedded/git` 规则中明确 diff 摘要应进入 CHANGELOG、Tag 或 Release Notes。
- 收紧 `embedded/git` 的 GitHub Release 规则和模板：创建 Release 时必须包含 Deprecations、Full Changelog、New Contributors 等完整章节，非适用项写 `None`。
- 调整 Release 语言策略：中文仓库默认中文，首次创建 GitHub Release 需确认语言；Release Notes 模板和校验脚本支持中文优先的中英双语标题。

## 2026-06-20

### Diff 概览

- `embedded/c99-standard-c/` 删除并迁移至 `embedded/C99/`。
- 新增 `embedded/architecture/` 及其架构审查模板和参考资料。
- 扩充 `embedded/motorcontrol/` 的算法、时序、多轴、测试和参考工程资料。
- 扩充 `embedded/ethercat/` 的 EtherCAT/CiA402、TwinCAT、SSC/ET9300、DC 和故障排查资料，并新增解码脚本与评估数据。
- 更新 `embedded/SKILL.md`、相关 `agents/openai.yaml`、仓库 README 和发布说明。

### C99 通用规范

- 将当前 C99 Skill 作为唯一通用 C 编码规范，不保留来源 Skill 的品牌或重复触发词。
- 修改前必须判断项目自研、自动生成或第三方代码。
- 自动生成和第三方代码默认保持实际编码及局部风格。
- 新项目和项目自研代码统一命名、4 空格、大括号、函数头及函数内部注释规则。
- 新增或大改函数记录作者、日期、原因以及必要的缺陷根因和修复方式。
- 项目自研代码非 GBK 时必须询问是否转换；第三方和生成代码保持实际编码。

### 嵌入式架构与电机控制

- 新增 architecture Skill，明确系统架构与控制算法的职责边界。
- 增加 Bootloader、OTA、A/B、Manifest、参数区、校准区和量产发布门禁。
- motorcontrol 增加 PWM/ADC/Encoder 同步、FOC/SVPWM、三环带宽、补偿、多轴同步及故障验证资料。
- 增加 VESC、ODrive、moteus、ODRI、PX4、ArduPilot、Betaflight 和 TI SDK 的参考边界说明。

### EtherCAT/CiA402

- 强化 EtherCAT 从站、CiA402 状态机、TwinCAT 联调、PDO/SDO/CoE 和 DC 同步规则。
- 新增 SSC/ET9300、Working Counter、WcState、AL/ESM、NC 轴 Ready 和多轴同步排查资料。
- 新增 `scripts/decode_cia402.py`、`evals/evals.json` 和专项参考索引。

### 发布

- 发布 tag：`v2026.06.20`。
- README 增加当前版本的路径级 diff 摘要。

## 2026-06-17

### 新增

- **feat**：新增 `platform/aicoding-kit-maintenance/`，定义 Codex-Skills/AiCoding 双仓库维护流程，明确 AGENTS 边界、架构文档、config/scripts 执行入口以及 Git hooks/CI 完成门禁。
- **docs**：新增根 `AGENTS.md`、`plugins/AiCoding/AGENTS.md` 和 `docs/PLUGIN_DEVELOPMENT.md`，明确人工维护区、自动生成区、Hook 辅助边界和跨仓库发布顺序。
- 建立 `Codex-Skills` 远程同步仓库结构。
- 新增中文 `README.md`，说明仓库用途、目录、排除规则和维护方式。
- 新增此 `CHANGELOG.md`，记录 skills 仓库变更。

### embedded

- `embedded` 增加独立 `SKILL.md` 作为一级 skill 入口。
- `embedded/readme.md` 改为二级 skill 分流说明，避免 `c99-standard-c`、`review` 和领域 skill 冗余调用。
- `embedded/review` 增加 MaJerle/c-code-style 中文评审参考：
  - `review/references/majerle-c-code-style-review-cn.md`
  - 明确该参考只用于风格、Doxygen、命名、格式化和头/源文件组织评审。
  - 明确兼容优先级：项目规范 > `c99-standard-c` > MaJerle 风格参考。
- `embedded/c99-standard-c` 保持 C99、安全、实时性、并发、寄存器和可移植性规则的优先级。

### 同步策略

- 排除 `.system/`、`backup/`、`*.zip` 和缓存文件。
- 使用独立 git 仓库管理 `C:\Users\24322\.codex\skills`，避免误提交上层用户目录。
