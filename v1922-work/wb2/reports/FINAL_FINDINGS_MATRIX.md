# FINAL_FINDINGS_MATRIX — 终局 F1-F12 核验矩阵

审计对象：`CityNexus-EAC-Overnight-Continuation-Final-20260917.zip`（SHA-256 已验证匹配 `0bd524…9f1`）。
方法：源码级扫描（file:line）+ 活体复现（包源码隔离栈 8011/5181 + 移动视口 390×844，Playwright，
实测时间 16:06–16:14，**晚于包内全部源码修复时间**，故本矩阵全部为修复后证据）+ 包内证据链审计。
判定：REPRODUCED（未修）/ PARTIALLY_FIXED / FIXED / NOT_REPRODUCIBLE。

| # | 发现 | 判定 | 关键证据 | 阻断试用？ |
|---|---|---|---|---|
| F1 | Copilot 地点问句证据 stale | **PARTIALLY_FIXED（证据缺口）** | 包内两份 trace（11:17/14:55）均早于最终修复（copilot_contract.py 14:56）；活体实测（16:07）：回复诚实拒绝+「探索地点」人类按钮、零枚举泄漏，但「鼓浪屿」仍无可信资料可答 | 证据门：STALE/MISSING ⇒ 阻断 READY 声明 |
| F2 | Copilot 工程词汇泄漏 | **PARTIALLY_FIXED** | 气泡已全量映射 ✅；但 CopilotDock.tsx:49/52 值级泄漏 "JourneyTwin"/"deterministic"、:296 policy_decision 原文、AgentComposer.tsx:208 feasibility 枚举直渲染；活体默认视图仍见「只读 What-if Studio」 | 否（次级界面） |
| F3 | Me 页策略内部暴露 | **REPRODUCED** | 活体+包内截图（lab_2_B__v8_me.png 14:48）双实锤：默认 Me 页大字 `ADVISORY` + kicker「我的 · 权限边界」（V8Experience.tsx:2161/2196、LocaleContext.tsx:848） | **是** |
| F4 | 预订规范路径内部标签 | **REPRODUCED** | 活体 bookings 页（有 journey）：`Journey Memory`、`UNKNOWN`、`受保护 C4`、`UNKNOWN_REALTIME` 全部可见（final_bookings_journey_text.txt）；包内 canonical trace 同样含 STRUCTURED_JSON/DETERMINISTIC/DeepSeek | **是** |
| F5 | 钱包次要路由 JSON 优先 | **PARTIALLY_FIXED** | Trips 主入口已是多模态收件箱（包截图 C1_16：粘贴/手动/截图/图片）✅；但 /v8/bookings 顶层仍裸 textarea（V8Experience.tsx:2001 无 try/catch），活体敌意粘贴无任何反馈，无「高级」标注 | 是（崩溃风险+无反馈） |
| F6 | 活动价格三态 | **REPRODUCED** | ActivityDetail.tsx:120 `costKnown = (amount_minor ?? 0) > 0`：已知免费景点显示「暂无价格」，无「免费」态 | **是**（真相缺陷） |
| F7 | 部分价格假置信 | **PARTIALLY_FIXED** | 零价格守卫已有（显示「花费未知」）；但检查为 `.some()`，1/N 已知仍打预算内/超预算标签 | 是（预算真相） |
| F8 | 预算合理性提示缺失 | **REPRODUCED（缺失）** | 包源码全局无任何「每日预算/偏高/紧张」advisory 实现（仅 studio.dailyMovement 无关项）；39 天/2 人/¥3000 组合无提示 | **是**（任务书明确要求） |
| F9 | 深链 /v8/today、/v8/copilot | **REPRODUCED** | routeFromPath 认识 13 键，无 today/copilot 别名；活体：无 journey→建单向导（尚可），**有 journey→/v8/today 仅 53 字符纯空白** | 是（刷新/分享深链白屏） |
| F10 | 旧方案假成功复发 | **REPRODUCED（源码）/ NOT_REPRODUCIBLE（活体）** | PlanWithAiSheet.tsx:182 `planCount > 0 → COMPLETED` 统计 `/plans` 全量（含旧方案）；活体无法构造前置（places API 返回 0 无法播种旧方案——该空池同时解释 AI 规划必然空转）；零旧方案场景终态诚实 ✅ | 是（结构风险） |
| F11 | 弱断言 | **REPRODUCED** | stay 证据 `undefined in=undefined out=undefined` 仍判 SELECTED（两份 trace+验收 MD）；triple-agreement trips=7/backend=14/live=文本，三量纲无定义口径即称「一致」 | 是（验收可信度） |
| F12 | 包可回放性 | **PARTIALLY_FIXED** | `source/backend/data/` 仅 mock\，缺 `data/v9/city_operations.json`（仓库根存在）；开箱回放必失败（本审计需手动从仓库补 data 才能起服务）；自报 739 测试无独立复放 | 否（工程债） |

**统计：0 FIXED / 5 PARTIALLY_FIXED / 7 REPRODUCED。**
EAC 的 READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL 声明与包内自带证据相矛盾
（其 WORKBUDDY_FINDINGS_REVALIDATION.md 自认 WB-H2–H5 仅部分修复，但验收文档标为已关闭）。
