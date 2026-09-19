# FINAL_MOBILE_UI_RECHECK — 移动端消费者 UI 门（v2）

视口要求：390x844 / Xiaomi 类。门标准见 UI_CONSUMER_GATE.md。证据三类：hotfix 包内截图（EAC 自产）、
源码渲染路径（file:line）、WorkBuddy 隔离活体栈（390x844 chromium）实测。

## 逐项判定

### 1. Booking 正常路径默认无裸语义/提取枚举 — **FAIL（R3 PARTIALLY_FIXED）**
- 默认面仍渲染：`item.role`(:581)、`draft.status`(:596)、`extraction_mode`(:597)、`anchor_role`(:601)、
  `payment_status`(:603)、`artifact_type`（JourneyInboxWorkbench.tsx）。
- V8Experience.tsx:1217-1223 声称 workbench 已挪入「高级 / 开发者」折叠，**实际折叠内是 Bookings 组件，workbench 留在折叠外** —— 注释与实现不符。
- EAC 包内截图（bookingfirst 系列）显示默认路径已改善（人话标签），但源码路径证明枚举值会在对应状态下漏出。
- Advanced 折叠（:2232）内的 Bookings 中文映射（bookingTypeLabel）工作正常。

### 2. Copilot 任务时间线默认无裸 tool_name — **FAIL（R4 PARTIALLY_FIXED）**
- 步骤主标签已人话化（toolLabels 映射，CopilotDock.tsx:47-59）✓。
- 但 :294 `event.tool_name ? <code>{event.tool_name}</code> : event.status` 经 AgentRunRail.tsx:18 **默认展开**渲染于「高级详情」折叠之外；
  挂载路径 V8Experience.tsx:1058 → latestNativeRun（CopilotDock.tsx:626）→ 任何触发 agent/tool mission 的对话即可见。
- 活体证据（前轮 final audit，修复后栈）：「鼓浪屿好玩吗」纯问句不触发；但重规划/搜索类 mission 会触发时间线。

### 3. Trips 无 check_out/departure/裸角色键 — **FAIL（R5 REPRODUCED）**
- TripItinerary.tsx:233（activity.type 直渲染）、ActivityDetail.tsx:211（meta.category 直渲染）、
  V8Experience.tsx:876（disruption type 仅下划线转空格）。
- 无任何本地化映射表；i18n 中亦无对应键。
- 活体实测注记：无 journey 深链时 `/v8/trips` 落到建单向导（138 字符），`?journey=` 参数不被前端深链加载机制识别 —— 深链分享场景只能看建向导，属可用性缺口（非本轮门项，记录备查）。

### 4. Copilot dock 不遮挡 sheet/主操作 — **FAIL（R6 PARTIALLY_FIXED）**
- dock 默认折叠为边缘条 ✓（相比常驻展开是实质改进）。
- 但无避让逻辑：CopilotDock 不感知 sheet/modal 状态，z-index 25 > sheet 的 20。
- EAC 自产截图实证：`01_create.png`/`02_ai.png`（AI 规划 sheet 被遮、「稍后」按钮挤成窄条）、
  `12_live_disruption.png`（dock 边缘条盖住第三张方案卡文字）。398px 视口下主操作可达性受损。

### 5. 多个 Live 提案可区分或去重 — **FAIL（R2 REPRODUCED）**
- LiveRecovery.tsx:188-213 `pending.map()` 无差别渲染；每卡只有计数摘要（「移除 N 项 · 新增 N 项」），
  **从不渲染 removed/added 的语义键或标题**；无去重、无 proposal 间差异展示。
- EAC 自产截图 `12_live_disruption.png`：两张卡逐字相同 + 两个相同的「接受新方案」按钮。
- 旅行者无法区分「两个真备选」还是「重复提案」——在闭馆恢复场景误点任何一卡后果相同，但违反门标准。
- 附带：added=0（纯移除提案）时摘要渲染为「移除 1 项 · 」（尾随间隔符，LiveRecovery.tsx:207 span 恒带 " · "）——次要文案瑕疵。

### 6. 酒店排名不暗示无依据证据 — **PASS（带质量保留意见，R7）**
- 卡片未声称排名依据；价格「暂无价格」三态诚实。
- 但卡片间近零差异（固定模板推荐语、无区域/供应商身份），选择实质上任意 —— 产品质量问题，不构成本门失败项。

## UI_CONSUMER_GATE 总判定：**FAIL**（第 1/2/3/4/5 项中 4 项 FAIL，仅第 6 项 PASS）

## 正面确认（保持不回归项）
- 离线只读模式、诚实空态（无 journey 时三步建向导 + 明确引导）、低价 advisory、价格三态——本轮源码与截图均未见回归。
- 建向导仍保留「使用封存的天津演示」按钮于默认视图（此前已记录，属演示残留，非本轮新增）。
