# CONSUMER_LANGUAGE_AUDIT — 2026-09-17 01:25（对 01:10 快照）

方法：对 `frontend/src` 全量 grep 内部术语，再核对使用点是否用户可见（i18n 字符串 = 直接可见）。

## A. 用户可见的内部术语泄漏（中文主流程，不可接受）

| # | 证据 | 位置 | 严重度 |
|---|------|------|--------|
| L1 | Copilot 行动按钮直接渲染 `item.response.action.type` 原始枚举（如 REQUEST_PLACE_SEARCH）作为按钮文字 | `features/agent/CopilotDock.tsx:535` | P0（真机改前照片 1000053121.jpg 已证实用户看到大号 REQUEST_PLACE_SEARCH） |
| L2 | Copilot 副标题「DeepSeek 语义 · Hermes 真实事件 · CityNexus 真相」 | `CopilotDock.tsx:518`（zh/en 双语都是工程黑话） | P1 |
| L3 | 工具事件流渲染 `<code>{event.tool_name}</code>` 原始工具名 | `CopilotDock.tsx:294` | P1 |
| L4 | i18n 中文键 `bookings.protectedC4` = 「受保护 C4」 | `i18n/LocaleContext.tsx:819`，用于 `V8Experience.tsx:1875` | P1（C4 内部等级直接见客） |
| L5 | i18n 中文 `discovery.authoritativeSub` = 「…与所有其他 PlanVersion 一样，可用于 JourneyTwin、地图和执行界面」 | `LocaleContext.tsx:976` | P1 |
| L6 | i18n `agent.whatIfStudio` = 「只读 What-if Studio」；`agent.whatIfPreview` = 「What-if 预览」 | `LocaleContext.tsx:912/895` | P1（任务书明确禁止 What-if Studio 出现在默认视图） |
| L7 | i18n `intel.advisory` = 「ADVISORY」原样英文枚举 | `LocaleContext.tsx:517` | P2（若在 Advanced 内可接受，需确认挂载点） |
| L8 | `inbox.semanticReady` = 「DeepSeek 已解读此工件。请查看…语义角色和确定性检查」；`inbox.semanticInterpretation` = 「DeepSeek 语义解读」 | `LocaleContext.tsx:1050/1098` | P1（booking 导入是主流程，「工件/语义角色/确定性」全是工程话） |
| L9 | `shell.missionCaptured` = 「Mission captured · external model unavailable, so the deterministic CityNexus path remains active.」英文工程句出现在中文 shell | `LocaleContext.tsx:91` | P1 |
| L10 | `discovery.shapeSub`（zh）= 「模型可选择语义方向，但只有服务端已知的地点才能到达权威方案」 | `LocaleContext.tsx:~310` | P2 |
| L11 | V8Experience 提前暴露 `protected_commitment_levels: ["C3_Guaranteed","C4_Anchored"]` 内部枚举值作为筛选/策略输入 | `V8Experience.tsx:528` | P2（数据层；是否见客待截图验证） |

## B. 良好信号（对照）

- `AgentComposer.tsx:90` 已把 REQUEST_PLACE_SEARCH 映射为友好标签并跳转 discover（说明模式存在，但 CopilotDock 未复用）。
- `mobileRoutes` 已按设计规范改为 Today/Trips/Map/Copilot/Me（v8Routes.ts:18-24，注释引用 DESIGN_CORRECTIONS §1）。钱包已离开黄金导航位。✓
- LegacyApp 已收进 `/legacy`，首访用户不会落在旧控制台（main.tsx:1651-1662）。✓
- Copilot 生命周期事件有 zh/en 友好标签表（lifecycleLabels），覆盖不全时回退 friendly_label。

## C. 分类结论

- 可保留在 Advanced/Developer：semantic envelope 详情（`<details>` 默认折叠，AgentComposer:231）、policy mode 枚举、guardian 诊断。
- 必须从默认旅行者视图移除：A 表全部，尤其 L1（CopilotDock 原始 action 枚举按钮）、L4/L5（中文界面里的 C4/PlanVersion/JourneyTwin）。
- 「DeepSeek」品牌名出现在 ≥6 处主流程文案 —— 消费产品不应让用户知道/关心推理供应商。

## D. 待运行时确认（截图后更新）

- L1/L2/L3 在当前构建是否仍在（EAC 00:59 刚改过 CopilotDock 相关壳文件，需实拍）。
- `intel.advisory`、What-if Studio 挂载在哪个 tab，是否默认可见。
