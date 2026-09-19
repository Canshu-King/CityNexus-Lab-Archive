# MULTIMODAL_UI_REDTEAM.md — 多模态 UI 红队审计（Phase 2）

- 审计者：WorkBuddy（GLM-5.3-Flash 独立红队）
- 时间窗：2026-09-17 00:30 – 03:00+
- 方法：隔离副本（后端 8011 / 前端 vite 5181）+ playwright-core + chromium-1243，iPhone 级 viewport 390×844 @2x，zh-CN locale
- 参考：`reference/UIReference/.../ui_reference/final_10/`（01 Today / 03 Create / 06 AI进度 / 07 方案比较 / 08 活动详情 / 09 酒店对比 / 10 Live）
- 截图目录：`screenshots/`（bk_* = bookings 域，ibx_* = 多模态收件箱，pc_* = 方案域，前缀见 VISUAL_PARITY_MATRIX.csv）
- 并发安全：未写入权威仓库任何文件；所有测试在隔离副本执行

---

## 1. 域 B：旅行票夹（Bookings）+ 多模态收件箱

### B1 · [P1｜UX/诚信] 主导入框要求旅行者手写 raw JSON，坏输入零反馈
- 证据：`V8Experience.tsx:1886-1898`（textarea `#reservation-json` + `submit` 中裸 `JSON.parse(input)`，无 try/catch）；截图 `bk_00_page.png`
- 实测（`evidence/bookings_hostile_trace.json`）：
  - Case C 粘贴自然语言「我的高铁票是明天早上9点30分从厦门北到福州南…」→ 点「审核并保护」→ **unhandled rejection**：`SyntaxError: Unexpected token '我'… is not valid JSON`（pageerror 捕获），UI 纹丝不动，无任何错误提示（`caseC_feedback_visible.errorFeedback = false`）
  - 普通旅行者语义 =「点了没反应，App 坏了」
- 对照：同页 `JourneyInboxWorkbench.tsx:209-225 extractText` 有完整 try/catch —— 同一页面两套错误处理标准
- 违反任务书 §2：raw JSON 仅限 Advanced；默认旅行者路径应为 paste booking text / manual form

### B2 · [P1｜产品结构] 消费者导入已具备完整多模态能力，但 JSON 框仍占据「导入确认」主位
- 后端早有 `/api/v1/journeys/{id}/inbox/text-extract`（`main.py:3023`，DeepSeek 提取）；前端 `JourneyInboxWorkbench.tsx` 已实现三路导入（粘贴文本提取 / 手动表单 / 截图提取），文案完整（`inbox.tabPaste/tabManual/manual*` 全套中文）
- 但 Bookings 页顶部「导入确认」卡仍是「预订 JSON」textarea + JSON placeholder（`bookings.reservationJson`、`bookings.lede`「粘贴结构化预订 JSON…」），与下方多模态收件箱**双入口并存、主次颠倒**
- 影子补丁方向：见 `lab/patches/P4`（Bookings 页把 JSON 框降级为 Advanced 折叠项，引导至多模态收件箱）

### B3 · [P1｜消费者语言红线] 文本提取失败时把原始英文异常直接抛给消费者
- 实测：粘贴完整 12306 短信文本 → 「提取文本草稿」→ ~9s 后显示 **「DeepSeek Responses request failed」**（`evidence/inbox_workbench_trace.json` text_extract_message；截图 `ibx_01_text_extract_result.png`）
- 根因：`JourneyInboxWorkbench.tsx:173/221` `setMessage(error instanceof Error ? error.message : …)` —— error.message 是英文原始异常，含 **DeepSeek 品牌名**、无中文解释、无下一步指引
- 触发条件真实：DeepSeek key 未配置/网络失败时，小米 13 Ultra 试用者会撞到

### B4 · [P2｜语言] 「Provider price unavailable 合计」英文硬编码混入中文界面
- 证据：`bk_00_page.png` / `bk_02_valid_after_submit.png` 住宿证据卡；来源为 price 为 null 时的回退文案未走 i18n（EN/CN 两套字典里该句均未本地化）

### B5 · [P2｜语言] 权威记忆面板渲染后端英文标题 "Journey Memory"
- 证据：`ibx_00_workbench.png`；`JourneyInboxWorkbench.tsx:475` `memory?.title ?? t("inbox.journeyMemory")` —— i18n 键有中文「行程记忆」，但被后端返回的英文 title 覆盖

### B6 · [P2｜枚举泄漏/可读性] 受保护事实渲染「Travel fact · UNKNOWNWB-RAIL-…」
- 证据：`ibx_00_workbench.png`；UNKNOWN 类型枚举与确认号无分隔符拼接，消费者不可读；类型枚举未本地化

### B7 · [P2｜枚举泄漏] wallet 卡片徽章直接显示 `UNKNOWN_REALTIME` 与「受保护 C4」
- 证据：`bk_02_valid_after_submit.png`；`V8Experience.tsx:1862`（`item.type · item.realtime_status` 原始枚举）+ `:1879`（`t("bookings.protectedC4")`=「受保护 C4」，内部承诺等级 C4_Anchored 见客）
- 与 CONSUMER_LANGUAGE_AUDIT L4 呼应

### B8 · [P2｜UX] 手动表单提交成功后零反馈
- `JourneyInboxWorkbench.tsx:166-171`：成功路径仅 `setDraft` + `setManualOpen(false)`（自动切回粘贴 tab），无「草稿已创建」消息；实测 30s 后 message 为空（`inbox_workbench_trace.json` manual_message）

### B9 · [正面✓] 双击/并发防重有效
- Case D 连续两次点击提交（两个不同 ref）各只产生 1 条记录；`main.py:3355` 注释确认 `(journey_id, confirmation_ref)` unique index 兜底并发双确认

### B10 · [正面✓] 缺字段 JSON 有合理反馈
- Case B `{"reservation_type":"HOTEL"}` → toast「预订需要审核后才能成为承诺。」（NEEDS_REVIEW 路径正常；但未告知缺哪些字段，改进空间有限级）

### B11 · [P2｜数据诚信] Bookings JSON 框提交的价格被静默丢弃
- Case A 提交 `price: {amount_minor: 12800, currency: "CNY"}` → 卡片显示「价格未知」
- 根因：后端 import 期望平铺 `amount_minor`（`JourneyInboxWorkbench.tsx:156` 手动表单即此形状），Bookings JSON 框透传用户 JSON 的 `price` 嵌套 → **同一端点两种 payload 形状，一个生效一个静默失效**。用户「已确认」的价格事实未被保护，与票夹「你的真实预订，受保护」承诺相悖

---

## 2. 域 C：Copilot + Today 空态

### C1 · [P1｜空态缺陷] 无方案时「今天」页主体纯空白，零 CTA 零引导
- 证据：截图 `cp_00_page.png` / `cp_04_today_diag.png`；API 拦截 `evidence/copilot_trace_v3.json`（experience 200 正常返回，`options:[]`、`active_plan_version_id:null`、plans `[]`）
- `/v8/today` 与 `/v8/copilot` 内容区均为空白（仅顶栏 + dock 收起条 + 底部 tab），无「创建行程 / 让 AI 规划 / 查看候选」任何引导；面包屑仍显示「今天」但 `/v8/copilot` 路由无对应页面内容
- 消费者视角：开 App = 白屏；与参考屏 01 Today（城市/日期/当日卡）完全脱节

### C2 · [P1｜消费者语言红线] Copilot 回复附原始枚举大按钮 REQUEST_PLACE_SEARCH
- 证据：截图 `cp_06_reply.png`；API `/copilot/messages` 返回 intent DISCOVER（confidence 0.72）
- 实测问答「鼓浪屿好玩吗？适合下午去吗？」→ 中文回复本身诚实（「搜索结果不会直接写入方案」✓），但下方渲染 **REQUEST_PLACE_SEARCH 全宽枚举按钮** + DISCOVER 英文徽章（`CopilotDock.tsx:535` 静态发现的动态实证）
- 同屏泄漏（leaks 实测）：`DeepSeek`、`Hermes`、`REQUEST_PLACE_SEARCH`

### C3 · [P2｜消费者语言红线] Copilot dock 头部与状态条系统性暴露内部架构
- dock 副标题「DeepSeek 语义 · Hermes 真实事件 · CityNexus 真相」（`CopilotDock.tsx:518`）
- 状态条「Semantic: DeepSeek Execution: DIRECT Truth: CityNexus」——英文技术词 + 供应商品牌，对旅行者零意义
- 输入 placeholder 正常中文 ✓

---

## 3. 域 D：酒店 / 行程 / 地图 / 我的（待巡检）

## 4. 视觉对比矩阵
见同目录 `VISUAL_PARITY_MATRIX.csv`。
