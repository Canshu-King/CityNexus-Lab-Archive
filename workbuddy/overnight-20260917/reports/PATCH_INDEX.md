# PATCH_INDEX.md — 影子补丁索引（Phase 8）

全部补丁在**隔离副本**实施并用浏览器端到端验证通过（`evidence/patch_verify_trace.json`，截图 `pt_*.png`）。
补丁基于主仓库 HEAD `7d22cd0`（eac/v19.2.2-realphone-codegate 分支起点相同，干净可 apply）。
原始文件备份于 `lab/patches/orig/`。

| 补丁 | 文件 | 修复的发现 | 验证结果 |
|------|------|-----------|---------|
| P1 | `P1_bookings_import_robustness.patch`（V8Experience.tsx）| B1 非 JSON 零反馈 / B11 价格静默丢弃 / B7 枚举与出发地不显示 | 非 JSON → 中文警示卡「暂时无法识别这段内容…」（pt_00）；卡片显示「厦门北 → 福州南 · 实时状态待确认 · 已保护」（pt_01）|
| P1b | `P1b_i18n_consumer_keys.patch`（i18n/LocaleContext.tsx）| P1 所需新键 + B7「受保护 C4」→「已保护/Protected」 | pt_01 卡片徽章「已保护」 |
| P2 | `P2_ai_plan_honesty_gate.patch`（features/planning/PlanWithAiSheet.tsx）| **P0 假成功**（1.1 节）| 空 mission 不再伪造 COMPLETED；COMPLETED 后核查 `/plans` 真实非空才说「方案已准备好」；实测显示诚实警示卡「这次没能生成方案…你的行程没有被改动」（pt_05）|
| P3 | `P3_copilotdock_consumer_language.patch`（features/agent/CopilotDock.tsx）| C2/C3 消费者语言红线 | DeepSeek/Hermes/Semantic 栏全部消失；REQUEST_PLACE_SEARCH→「搜索候选地点」按钮、DISCOVER→「探索」chip、未知 intent 隐藏、UNVERIFIED 不再出现（pt_02/pt_03，leaks={}）|

## 给 EAC 的 apply 说明
```
git apply P1_bookings_import_robustness.patch
git apply P1b_i18n_consumer_keys.patch
git apply P2_ai_plan_honesty_gate.patch
git apply P3_copilotdock_consumer_language.patch
```
- 补丁互相独立，可单独采纳；P1 依赖 P1b 的 i18n 键
- P2 的诚实门是**前端闸门**：真正的修复还应包含后端——mission COMPLETED 时若未 materialize plan，应在 mission status 中显式区分（建议 `COMPLETED_NO_PLANS` 语义上移到后端）
- 已知残留（本补丁未覆盖）：后端 import 端点对嵌套 `price:{}` 形状仍不接受（P1 已在 UI 侧平铺适配，后端原生支持 `amount_minor` 平铺；UI 层价格平铺后 wallet 仍显示「价格未知」，说明后端提取链对 STRUCTURED_JSON 的 amount_minor 也未落库——需要 EAC 在后端核实 `_draft_payload`/confirm 链）

## 建议但未实施（时间窗内评估为高成本低杠杆）
- Today 空态 CTA（C1）——需要产品决策（复用行程 tab 空态组件即可，但涉及路由/布局改动）
- 菜单开发者路由折叠进「高级」（TC-10）——同上
- 酒店空态伪证据卡（TC-09）——需要后端 stay-options 空数组语义确认
