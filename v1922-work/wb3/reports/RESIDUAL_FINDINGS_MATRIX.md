# RESIDUAL_FINDINGS_MATRIX — R1-R9 复检矩阵（v2）

审计对象：`CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917`（SHA-256 匹配 ✓）
证据来源：包内源码（file:line）+ 包内截图/trace + WorkBuddy 隔离活体栈实测。权威仓库未修改。

| # | 发现 | 判定 | 关键证据 |
|---|---|---|---|
| R1 | 被关闭目标可能在接受后存活 | **PARTIALLY_FIXED** | 引擎真值 PASS（受控流：closed place 彻底移除，diff.removed=["place-gulangyu-organ"]，plan f19d1146→afce0ec8）；但提交 trace 无 ID 级证据、同标题字节级存活 → 主张不可验证；新缺陷 R1-a（None in {None} → 有预订旅程闭馆流 422 误拒）、R1-b（编译器解析非确定）。详见 REPLAN_IDENTITY_RESULTS.md |
| R2 | Live 多张不可区分的重规划卡 | **REPRODUCED** | LiveRecovery.tsx:188-213 `pending.map()` 无差别渲染，只显示「移除 N 项 · 新增 N 项」计数，从不渲染 removed/added 具体内容；包内截图 `12_live_disruption.png` 两卡标题/正文/摘要/按钮逐字相同。旅行者被迫在两个不可区分的「接受新方案」间选择 |
| R3 | 预订审查默认面暴露内部词汇 | **PARTIALLY_FIXED** | 新增 BOOKING_FIELDS/TYPE_LABELS/DECISION_LABELS 人话映射（JourneyInboxWorkbench.tsx:110-154）✓；但 artifact_type、draft.status(:596)、extraction_mode(:597)、anchor_role(:601)、payment_status(:603)、item.role(:581) 仍在默认面裸渲染。V8Experience.tsx:1217 注释称 workbench 已入 Advanced 折叠，实际折叠内是 `<Bookings>`，workbench 在折叠外 |
| R4 | Copilot 任务时间线裸渲染 tool_name | **PARTIALLY_FIXED** | 新增 toolLabels 映射用于步骤主标签（CopilotDock.tsx:47-59、134-139）✓；但 `event.tool_name ? <code>{event.tool_name}</code> : event.status`（:294）原样保留，经 AgentRunRail.tsx:18 默认展开渲染，位于「高级详情」折叠之外 |
| R5 | Trips 泄漏内部活动角色键 | **REPRODUCED** | TripItinerary.tsx:233 直接渲染 activity.type；ActivityDetail.tsx:211 渲染 meta.category；V8Experience.tsx:876 渲染 disruption type（仅下划线转空格）。全源码无 check_out→退房 / departure→出发 / museum→博物馆 映射 |
| R6 | Copilot dock 抢占核心内容空间 | **PARTIALLY_FIXED** | dock 默认折叠为边缘条（真实缓解）✓；但 CopilotDock 不接收 sheet 状态，z-index 25 > sheet 20，不避让：`01_create/02_ai.png` 显示 AI 规划 sheet 内容被遮、「稍后」按钮被挤成窄条；`12_live_disruption.png` 中边缘条盖住第三张方案卡文字 |
| R7 | 酒店卡片弱差异化 | **REPRODUCED**（产品质量，非硬阻塞） | 推荐语为固定模板嵌两个数值；无区域/地址/供应商身份；无「证据不足以排名」明示。未发现虚假排名声明 |
| R8 | AI 门禁 fail-open 基线边缘 | **REPRODUCED** | PlanWithAiSheet.tsx:115-130 `existingPlanIds()`：`if (!response.ok) return new Set()`（:120）与 `catch { return new Set(); }`（:127）——基线快照失败返回空集 → fail-OPEN，旧方案会被误判为「新方案」→ 可能假成功。要求 fail-closed |
| R9 | 包内陈旧验收证据未标注 | **REPRODUCED**（打包卫生） | 14:38 前的验收证据均无 PRE_HOTFIX/SUPERSEDED 标注；含 739 vs 748 测试数、双 journey 指纹等矛盾。另：包缺 `db/schema.sql`（离线回放失败） |

## 前序热修确认（任务书第 1 部分，全部源码级验证通过）

| 项 | 状态 | 证据 |
|---|---|---|
| Me 策略内部默认隐藏 | ✓ | V8Experience.tsx:2432-2455 ADVISORY/policy 位于 `me-advanced` `<details>` 内 |
| 免费/付费/未知价格三态 | ✓ | ActivityDetail.tsx:189-194（「免费」/「暂无价格」/金额）；HotelsPanel.tsx:184 |
| 部分价格不假装预算结论 | ✓ | PlanComparison.tsx:117-139「部分价格未知（knownCount/stops）」，不完整覆盖不打预算标签 |
| 低预算 advisory | ✓ | V8Experience.tsx:1316-1419 `budget-advisory`（含 tight 变体与可关闭） |
| 路由别名 | ✓ | V8Experience.tsx:167-193 ROUTE_ALIASES（today/copilot/bookings/wallet/itinerary/stay…），未知路由回退 Today |
| 运行级 plan-ID 快照 | ✓（有边缘） | PlanWithAiSheet.tsx:114-140 existingPlanIds —— 但见 R8 fail-open |
