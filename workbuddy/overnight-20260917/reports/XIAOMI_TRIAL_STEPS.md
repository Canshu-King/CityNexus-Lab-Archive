# XIAOMI_TRIAL_STEPS — 转 ACCEPTS 的最短路径（按阻塞权重排序）

前置：本清单基于 v2 复检（hotfix 候选 SHA ede70c66…）。完成 1-5 后重跑 TARGETED_RECHECK 全项，七门 + 六条件全过即改判。

## 第 1 步 — Live 提案卡可区分（R2，硬阻塞，约 0.5 天）
`LiveRecovery.tsx:188-213`
1. 渲染前按 `diff.removed+diff.added+diff.kept` 语义键元组去重，相同 diff 只保留最新 proposal。
2. 每卡列出被移除/新增活动的**人话标题**（活动 title 已在 experience 数据里，不需要新接口）。
3. 多卡时给每卡一行差异说明（如「方案 A：直接去掉闭馆点」「方案 B：换成 X 博物馆」）。
4. 修复 added=0 时「移除 1 项 ·」尾随间隔符。

## 第 2 步 — 闭馆重规划健壮化（R1-a/R1-b，P1，约 0.5 天）
`main.py:6591`
1. `None in {None}` 缺陷：改为 `if trigger_event.affected_activity_id and trigger_event.affected_activity_id in {...}`。
   有导入预订（承诺 activity_id=None）的旅程目前闭馆流 100% 422 误拒。
2. 影响评估解析出 `selected_activity_id` 后回写 `Event.affected_activity_id`，让门禁用已解析身份而非原始 None。
3. 语义编译器目标解析失败（unresolved_references 非空）时回退到确定性标题匹配（act.title CONTAINS closed_venue），
   消除 LLM 非确定性导致的「时好时坏」。

## 第 3 步 — 消费者语言收尾（R3/R4/R5，硬阻塞，约 0.5-1 天）
1. JourneyInboxWorkbench：把 :581/:596/:597/:601/:603 的 role/status/extraction_mode/anchor_role/payment_status
   渲染全部走人话映射（映射表已存在，直接复用 BOOKING_FIELDS/DECISION_LABELS），或整体挪进 :2232 的 Advanced 折叠。
   同步修正 V8Experience.tsx:1217 的失实注释。
2. CopilotDock.tsx:294：`<code>{event.tool_name}</code>` 挪进「高级详情」折叠，或改用已有 toolLabels 映射（未命中时显示 status 的人话）。
3. Trips/ActivityDetail：新建 ROLE_LABELS = {check_out: 退房, departure: 出发/离开, museum: 博物馆, food: 美食, …}
   映射表，TripItinerary.tsx:233 / ActivityDetail.tsx:211 / V8Experience.tsx:876 三处全部走映射，未命中回退原文。

## 第 4 步 — AI 门禁 fail-closed（R8，硬阻塞，约 0.5 天）
`PlanWithAiSheet.tsx:115-130`：基线快照失败（!ok 或异常）时**不得返回空集继续流程**——
返回 null 并让 submit 走「结果不确定」终态（禁止成功文案）。原则：无法证明「没有旧方案」时，永远不把 GET 到的旧方案算作新产出。

## 第 5 步 — 打包卫生 + 可选项（R9/R7，非阻塞）
1. 陈旧验收证据标 `PRE_HOTFIX / SUPERSEDED` 或移出顶层 evidence；补 `db/schema.sql` 入包（当前离线回放必失败）。
2. R7 酒店卡：加区域/地址行；无供应商证据时明示「暂无法比较，按距离排列」。
3. Copilot dock 避让（R6）：sheet/modal 打开时 dock 自动最小化（一行状态联动 + z-index 调整），或 z-index 降到 sheet 之下。

## 第 6 步 — 修复后证据要求（提交给 WorkBuddy 复核的最小集）
1. **ID 级 VISIBLE_UI_TRACE**：proposal diff 摘录 diff.removed[]/added[] 的语义键 + 接受后 plan 的 activity/place ID 清单
   （标题级 before/after 样本不再被接受——本轮 R1 的教训）。
2. 闭馆流证据必须产生于上述源码修复**之后**（TRACE_INTEGRITY_GATE 原则）。
3. 有导入预订的旅程上跑一次闭馆重规划（覆盖 R1-a 修复路径）。
4. 390px 视口下：AI 规划 sheet 打开时的 dock 状态截图、Live 双提案去重后截图、Trips 角色键中文化截图。
