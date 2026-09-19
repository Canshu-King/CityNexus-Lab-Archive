# TOP_FIXES_FOR_EAC.md — 给 EAC 的修复清单（Phase 9）

按 ROI 排序。前 4 项有 WorkBuddy 已验证的影子补丁可直接 `git apply`（见 `PATCH_INDEX.md`）。

## 立即修（试用前必须）
1. **AI 规划诚实门** —— apply `P2_ai_plan_honesty_gate.patch`；同时把「COMPLETED 但无 plan」的区分**上移到后端** mission status（agent 确认无法生成时不要返回 COMPLETED）
2. **Bookings 导入健壮化** —— apply `P1_bookings_import_robustness.patch` + `P1b_i18n_consumer_keys.patch`；后端核实 STRUCTURED_JSON 导入链 `amount_minor` 是否落库（前端平铺后 wallet 仍显示「价格未知」，提取链疑似丢弃金额）
3. **Copilot 消费者语言** —— apply `P3_copilotdock_consumer_language.patch`；同法处理：inbox 的「DeepSeek 语义解读」（`inbox.semanticInterpretation`）、酒店页 `0% confidence`/`explicit`/`captured hotel`、票夹 `UNKNOWN_REALTIME`、权威记忆 `UNKNOWN` 粘连与后端英文 title "Journey Memory"
4. **Provider price unavailable 合计** —— 该句未走 i18n（中英字典均无此键），定位硬编码处补键

## 本周内（试用前强烈建议）
5. **Today 空态**：复用行程 tab 空态模式（一句话 + 「AI 帮我规划」CTA）；`/v8/copilot` 路由补内容或重定向到 dock 展开
6. **汉堡菜单收纳**：开发者路由（TODAY/PLAN/TRAVEL/SYSTEM 分类）移入「高级/开发者」折叠区
7. **酒店空态**：stay_journey_options 为空时显示「还没有采集到住宿候选」引导，而非渲染空费率卡
8. **文本提取失败态**：`extractText` catch 分支改用 i18n 文案 + 重试按钮（参考 P3 的处理思路），禁止 `error.message` 直出

## 结构性（下个迭代）
9. 预订导入应以多模态收件箱（文本/手动/截图）为默认路径，JSON 框降级为「高级」折叠项——后端能力已齐，纯前端工作
10. mission/stepper 状态机统一：任何「成功」终态必须绑定可验证产物（plan 存在、卡片入库），杜绝乐观终态
11. 消费者语言 lint：把 PlanVersion/JourneyTwin/C3/C4/UNVERIFIED/REQUEST_*/供应商品牌加进 CI 文案扫描（CONSUMER_LANGUAGE_AUDIT.md 的 L1-L11 可作种子词表）

## 验收自测脚本
WorkBuddy 的 lab 脚本可复用为回归：`lab/verify_patches.js`（补丁效果）、`lab/flow_bookings_hostile.js`（导入敌意三例）、`lab/flow_copilot3.js`（Copilot 泄漏扫描）。跑法见各文件头部注释；Node + 副本 node_modules + 本机 chromium，无需下载依赖。
