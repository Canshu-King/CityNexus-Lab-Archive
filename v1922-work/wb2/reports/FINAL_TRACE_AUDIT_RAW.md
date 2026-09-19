# FINAL_TRACE_AUDIT_RAW — CityNexus EAC 候选包证据链完整性 / 新鲜度审计

- 审计对象根目录：`eac_final_pkg/CityNexus-EAC-Overnight-Continuation-Final-20260917/`
- 审计性质：**只读**；仅核对 JSON / MD / 截图文件名与 LastWriteTime，未运行任何服务。
- 时间戳约定：所有本地文件 mtime 为北京时间（UTC+8，即 `Z` 时间 +8h）。trace 内 `ts` 为 UTC（`Z`），已折算比对。
- 核心判据（TRACE_INTEGRITY_GATE）：证据必须产生于对应源码修复**之后**；修复前的截图/轨迹不能证明修复后的声明；拒绝无实质 diff 的新 UUID、API 代打、换 journey_id、demo/reset 替代。

---

## 任务 1 — F1 证据新鲜度（重点：Copilot「鼓浪屿好玩吗？」）

### 1.1 两版 trace 中 Copilot 步骤原文

**VISIBLE_UI_TRACE.json（文件 mtime 11:17；run started 03:12:50Z=11:12:50 北京；journey_id `618fca41-428f-460f-ab92-1253c62f16fe`）**
```
ts 03:16:09Z (11:16:09 北京)
action: copilot-question
status: "empty"            <-- 注意：空
result: "你 鼓浪屿好玩吗？"   <-- 仅回显了用户问题，无任何 Copilot 回复
```
（同文件 `copilot-after-replan` 步骤 `status:"empty" result:""`）

**VISIBLE_UI_TRACE_run1.json（文件 mtime 14:55；run started 06:52:18Z=14:52:18 北京；journey_id `29fb8e0f-1231-4d2d-9393-a44210bbd03c`）**
```
ts 06:54:00Z (14:54:00 北京)
action: copilot-question
status: "answered"
result: "CityNexus 我没有可靠识别这条请求。可以问我为什么这样安排、如果多待一小时会怎样、找一个室内地点，或报告正在发生的交通/天气变化。 其他问题"
```

### 1.2 差异说明了什么
- canonical（11:17）的 Copilot **完全没回答**（status=`empty`，result 只有用户问题回显）——即一个**坏掉的/无响应的 Copilot**。
- run1（14:55）的 Copilot **给出了回复**，但只是优雅拒绝（"我没有可靠识别这条请求"），并非实质性地点解答。
- 两版差异说明：canonical 这一版证据**不能证明 Copilot 工作**；它记录的是一个空的 Copilot 响应。

### 1.3 源码修复时间 vs 证据时间
- `frontend/src/features/agent/CopilotDock.tsx` mtime = **2026-09-17 10:18:30**（修复 dock 崩溃 / locale 未定义）。
- `frontend/src/features/agent/AgentComposer.tsx` mtime = 2026-09-16 23:52:28。
- `backend/app/integrations/ai/copilot_contract.py` mtime = **2026-09-17 14:56:24**（OVERNIGHT_RUN_LEDGER C11，15:04 条目明确："`鼓浪屿好玩吗？` 被误判为不可解读、答 'I could not understand'，现已用人工 chips（查找地点/搜索更多地点）路由修复"）。

关键结论：
- canonical 11:17 的运行（11:12–11:17）**晚于** CopilotDock.tsx 修复（10:18），但 Copilot 仍返回 `empty`——说明该修复并未让"鼓浪屿好玩吗？"得到回答。
- **真正让该问句得到回答的修复是 `copilot_contract.py`（14:56:24，C11）**。而 **canonical（11:17）和 run1（14:55 结束）两个 trace 都早于 14:56:24**，均未包含该修复。
- 因此：**canonical trace 相对 Copilot 修复是 STALE（且为损坏态）**；即便 run1 的"answered"也只是修复前的优雅拒绝；最终"human chips"答案仅存在于 ledger C11 的**叙述**中，包内**无任何 trace / 截图证据**。

### 1.4 额外发现（包内自相矛盾）
- ledger C6（11:19）声称："`VISIBLE_UI_TRACE.json written for run 1 (archived as VISIBLE_UI_TRACE_run1.json)`"。但两文件 **journey_id 不同（618fca41 vs 29fb8e0f）、copilot 状态不同（empty vs answered）、时间戳不同（11:17 vs 14:55）**——根本不是同一份运行的归档。**标签/归档声明为假**。
- ledger C6 同时声称该 run1"Copilot place question answered from live provider evidence"，但 canonical trace 实际为 `empty`，**直接矛盾**。
- canonical trace 头部 `"copilot_useful": true`，但其 `copilot-question` 步骤 `status:"empty"`；PRODUCT_ACCEPTANCE_RESULTS.md 第 46 行 `copilot-question | empty` 却在第 66 行写"Copilot answer judged useful: True"——**内部自相矛盾**。

**F1 结论：canonical trace（VISIBLE_UI_TRACE.json）对 Copilot 地点问答特性是 STALE / 损坏的。提交为「READY」的旗舰证据显示 Copilot 无响应。**

---

## 任务 2 — F4 预订规范路径标签核査

检索字符串：`Journey Memory` / `manual-entry` / `Departure anchor` / `UNKNOWN` / `STRUCTURED_JSON` / `DETERMINISTIC` / `受保护 C4` / `UNKNOWN_REALTIME`

### 2.1 出现位置（均在 evidence/ 内）
| 字符串 | 出现文件 / 步骤 | 时间 / 备注 |
|---|---|---|
| `UNKNOWN` | VISIBLE_UI_TRACE.json L152 `booking-manual-draft`；L160 `booking-review` | 11:17，默认旅行者预订流 |
| `UNKNOWN` | VISIBLE_UI_TRACE_run1.json L152、L160 | 14:55 |
| `STRUCTURED_JSON` | 同上两文件 L160 `booking-review`；PRODUCT_ACCEPTANCE_RESULTS.md L43 | 默认预订流 |
| `DETERMINISTIC` | 同上 L160、MD L43 | 默认预订流 |
| `Departure anchor` / `DEPARTURE` | 同上 L160（"DeepSeek 语义解读DEPARTURE · 100% 置信度目标 · Departure anchor支付 · UNKNOWN"） | 默认预订流 |
| `DeepSeek` | 同上 L152/L160（"DeepSeek 语义解读"） | 默认预订流 |
| `UNKNOWN_REALTIME` | LAB_CYCLES.jsonl L2（"Zero internal enums (UNKNOWN_REALTIME / REQU…"）；LAB_PROBE_RESULTS.json `internalLeaks:[]` | 实验室"零泄漏"声明 |

**未出现**的字符串：`Journey Memory`、`manual-entry`、`受保护 C4`（"受保护 C4" 仅见于 reports/ 内代码级引用，未在任何 trace / UI 证据 JSON 中出现）。

### 2.2 是否出现在「默认旅行者界面」证据中？
**是。** `STRUCTURED_JSON` / `DETERMINISTIC` / `DEPARTURE` / `Departure anchor` / `UNKNOWN` / `DeepSeek` 全部出现在 `booking-manual-draft` 与 `booking-review` 步骤——而 booking-first 是默认（非高级）场景，且这些步骤文本即用户可见的预订审核界面。即**内部契约枚举直接泄漏进了默认旅行者中文 UI**。

### 2.3 与"零枚举泄漏"声明的冲突（重点）
- AUTONOMOUS_CYCLE_2.md、LAB_CYCLES cycle2、LAB_PROBE cycle2 断言"**no internal enum leaks into the Chinese UI**"，且 AUTONOMOUS_CYCLE_2 明确列出禁止词含 `UNKNOWN_REALTIME / REQUEST_* / … / DeepSeek / Hermes`。
- 但其探测**只覆盖了 Today/Copilot/Trips/Live（无 journey / API 阻断）**，从未驱动**预订审核**这一界面。而 canonical trace 的 `booking-review` 步骤恰恰出现了 `DeepSeek`（在禁止词列表中！）以及 `STRUCTURED_JSON/DETERMINISTIC/DEPARTURE/UNKNOWN`。
- ⇒ 实验室"零泄漏"结论**范围不完整**，且被包内 canonical trace 自身**反向证伪**。WB-H3 独立复核报告也确认 H3 仅为 PARTIALLY_FIXED（预订/agent 路由仍有原始枚举泄漏）。

---

## 任务 3 — F10 旧方案假成功

### 3.1 AI 规划轮次记录
- 全部 trace 的 `ai-plan` 均显示 `plans-ready(3)` → `choose-plan` `selected`。**没有任何 trace 记录 plan_version / candidate id**。
- scenario 的 Copilot 文本："当前使用 **PlanVersion 4 (ACTIVE）**…"——说明 plan 会累积版本（PlanVersion 4）。

### 3.2 旧方案假成功风险（来自包内 WB 复核报告）
WORKBUDDY_FINDINGS_REVALIDATION.md（WB-H1 段）明确指出残留：
> "planCount is `plans.length` over `GET /journeys/{id}/plans`, and that endpoint applies **no status filter**… A journey that already owns an `ACTIVE`/`SELECTED`/`REJECTED`/`SUPERSEDED` `PlanVersion` would therefore report 'N candidate plans are ready' even when **no *new* candidate was produced by this run**."

即：成功门统计的是**全部 plan**（含旧方案），而非"本次新生成的 CANDIDATE"。若 journey 已持有旧 PlanVersion，旧方案即可满足成功门——**典型旧方案假成功**。

### 3.3 终态文本
- 所有 scenario trace 的规划轮次终态均为 success（plans-ready → selected）。
- 诚实失败路径（`NO_PLANS_PRODUCED`，WB-H1 报告所述"your trip is unchanged"终态）**在任何 trace 中均无体现**。
- `run_ai.json` / `run_canonical_partial.json` / `run_chain2.json` 是 **2026-09-16（前一天）的陈旧产物**（journey `a47f190a`，时间戳 17:18Z），其中 `run_ai.json` 仍含旧假成功串"`方案已准备好`"、`run_chain2.json` 出现 `plan-compare 0 cards` / `choose-hotel not-selected` / 422 错误——这些是**修复前的旧 bug 证据**，属陈旧残留，绝不可作为修复后证明引用。

**F10 结论：包内无证据能区分"3 个 plan"是新候选还是包含旧方案；成功门状态未过滤，存在旧方案假成功风险；诚实失败路径无证据。**

---

## 任务 4 — F11 弱断言

### 4.1 stay 证据中的 `undefined` check-in/out
- VISIBLE_UI_TRACE.json L143-144：
  ```
  action: stay-truth
  status: "SELECTED"
  result: "undefined in=undefined out=undefined"
  ```
- VISIBLE_UI_TRACE_run1.json L142-143 完全相同：`"undefined in=undefined out=undefined"`。
- PRODUCT_ACCEPTANCE_RESULTS.md L41 亦复现：`stay-truth | SELECTED | undefined in=undefined out=undefined`。
⇒ 住宿的入住/退房时间字段为 `undefined`，却仍标记为 `SELECTED` 并判过——**弱断言**（带 undefined 日期仍判通过）。

### 4.2 Trips 可见数量 vs 后端数量 的三方一致性
- canonical `triple-agreement` 步骤：`status:"consistent"`，`result:"trips=7 backend=14 live=\"下一站：厦门高崎国际机场\""`。
- 三方是**三种不同量纲**：UI 7 个 stops、后端 14 个 activities、Live 一个文本字符串。
- 仅以"consistent"一词断言，**未给出任何定义的对比口径**（7 如何映射到 14？activity 与 stop 的换算规则？）。"Trips and Live must agree with the backend"（canonical L248）也仅是模糊要求，无量化定义。
⇒ **弱断言**：含糊的"一致"，无明确定义口径。

---

## 任务 5 — TRACE_INTEGRITY_GATE 七项特性门

说明：
- journey_id：canonical=`618fca41…`，run1=`29fb8e0f…`；其余 scenario 各有独立 id（budget `7adb4d31`、longtrip `92befafc`、degraded `932fbcdc`、hostile `2f026c29`、bookingfirst `377fd2d6`）。
- plan id：**所有 trace 均未记录 plan_version/candidate id**（F10 弱点），表中以"—"标注。
- 证据类型：trace=JSON 轨迹；screenshot=截图；api=API 探针。
- 判定：PASS=证据晚于修复且无缺陷；STALE=证据早于/等于修复前态或显示修复前缺陷；MISSING=修复后正确态无证据。

| # | 特性 | 修复文件 (mtime) | 修复时间 | 证据文件 (mtime) | 证据时间 | journey_id | plan id | 证据类型 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AI planning success gate (WB-H1) | `PlanWithAiSheet.tsx` (02:41:46) | 09-17 02:41 | VISIBLE_UI_TRACE.json (11:17) + 5 scenario (11:20–14:55) | 09-17 11:17+ | 618fca41… | — | trace | **PASS**（残留：计数未过滤状态，见 F10） |
| 2 | plan select / 预算真相 | `PlanComparison.tsx` (14:49:30) | 09-17 14:49 | canonical `plan-compare`="预算内/预算内/预算内"(11:17) **早于修复**；run1="花费未知/花费未知/花费未知"(14:55) | 11:17 / 14:55 | 618fca41… / 29fb8e0f… | — | trace | **STALE**（canonical 显示修复前伪造"预算内 CNY 0"；run1 PASS） |
| 3 | hotel select | `HotelsPanel.tsx`(01:21:12) / `stay_mobility.py`(08:54:34) | 09-17 01:21/08:54 | canonical `hotel-compare`10 hotels→`choose-hotel` selected (11:17) | 09-17 11:17 | 618fca41… | — | trace | **PASS** |
| 4 | booking confirm | `semantic_intake.py`(08:49:48)/`main.py`(14:59:48)/`operations/v9.py`(11:24:46) | 09-17 08:49–14:59 | canonical booking-manual-draft/review/import/visible (11:17) | 09-17 11:17 | 618fca41… | — | trace | **PASS**（但含 F4 枚举泄漏 + F11 undefined stay） |
| 5 | Copilot place answer | `CopilotDock.tsx`(10:18:30) + **`copilot_contract.py`(14:56:24)** | 09-17 10:18 / 14:56 | canonical `copilot-question`=**empty**(11:17)；run1=优雅拒绝(14:55)；最终 human-chips 答案**无证据** | 11:17 / 14:55 / — | 618fca41… / 29fb8e0f… | — | trace | **STALE**（canonical 损坏；最终修复态 MISSING 证据） |
| 6 | Live material replan | `main.py` replan*(14:59:48) / `stay_mobility.py`+`real_city.py`(C4 08:41) | 09-17 08:41–14:59 | canonical `disruption-event`201 → `replan-proposal` preserved=true → `accept-replan` accepted (11:17) | 09-17 11:17 | 618fca41… | — | trace | **PASS**（注：canonical replan 对象 before/after_titles 完全一致，removed/added 未在标题体现，存疑minor） |
| 7 | replan accept | 同上 (C4) | 09-17 08:41+ | canonical `accept-replan`="已按新安排更新你的行程。" (11:17) | 09-17 11:17 | 618fca41… | — | trace | **PASS** |

### 截图证据映射（按文件名前缀 / LastWriteTime）
- `C1_*`（26 张，mtime **14:52:18**）= run1.json 那次 canonical 运行（journey 29fb8e0f）的完整流程截图，含 `C1_17_copilot.png`、`C1_20_live_disruption.png`、`C1_21_live_accepted.png`。
- **canonical（11:17, journey 618fca41）没有任何截图前缀集**（无 11:12–11:17 区间的截图）。即旗舰 canonical 运行的**可视化证据缺失**，现存截图属于更晚的 run1。
- `lab_*`（60 张：cycle1×26、cycle2×34）= 五个自主实验室周期证据。
- `budget_/longtrip_/degraded_/hostile_/bookingfirst_`（各 7 张）= 对应 scenario 截图。
- `vp_*`（12 张）+ `vp_xiaomi13ultra-412x915_*`（6 张）= 三视口证据，**含 Xiaomi 13 Ultra 412x915**（与 VIEWPORT_EVIDENCE.json 一致）。
- `noplan_*/empty_*`、`probe_budget2` = WB-H4 / cycle4 证据。

**七门统计：PASS = 5（#1,#3,#4,#6,#7）；STALE = 2（#2 canonical、#5）；MISSING = #5 的最终修复态无证据。**
（若以 run1 替代 canonical 看 #2/#5：#2 转 PASS、#5 仍为 STALE/MISSING。）

---

## 任务 6 — EAC 自述 vs 包内可验证证据

### 6.1 EAC 自报（README_FIRST / PRODUCT_ACCEPTANCE_RESULTS / ledger FINAL）
- 6 次端到端浏览器运行全绿（0 console error、0 failed step）。
- 5 个自主实验室周期（发现并修复 2 个真实缺陷）。
- 3 个验收视口（390x844、430x932、Xiaomi 13 Ultra 412x915@DPR3.5）。
- 后端套件 **739 passed / 0 failed / 15 skipped**；前端生产构建通过。
- **WB-H1..H5 全部 FIXED / 关闭**。
- 终裁：**READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL**。

### 6.2 OVERNIGHT_RUN_LEDGER.jsonl 结构
14 条记录（START、C1–C11、SHUTDOWN_INTERRUPTION、FINAL）。每条约字段：
`timestamp`(+08:00) / `checkpoint` / `phase` / `top_blocker` / `changed_files_since_last[]` / `browser_scenarios_completed[]` / `remaining_p0_p1` / `notes`（部分含 `verdict`）。

### 6.3 LAB_CYCLES.jsonl 结构
5 条（cycle 1–5）。每条约字段：
`timestamp`(+08:00) / `cycle` / `hypothesis` / `verdict`（cycle1、cycle4 = CONFIRMED_DEFECT；cycle2/3/5 = NOT_REPRODUCIBLE）/ `files_changed[]` / `evidence`。

### 6.4 自述与包内证据冲突（关键）
1. **WB-H1..H5 状态冲突**：EAC 声明全部 FIXED/关闭；但包内自带的 `WORKBUDDY_FINDINGS_REVALIDATION.md` 明确给出 **H1=FIXED_BY_CURRENT_EAC，H2–H5=PARTIALLY_FIXED**。EAC 把"仅部分修复"的发现标记为关闭——**包内自相矛盾**。
2. **Copilot 声明冲突**：ledger C6 称 canonical run1 "Copilot place question answered from live provider evidence" 且 "VISIBLE_UI_TRACE.json archived as run1.json"；但 canonical trace 实际 `empty`，且两文件是不同运行（见任务1）。ledger C8 再称 run1 canonical "Copilot answered"，而 run1.json 实为该问句的优雅拒绝、ledger C11 又承认该问句"直到 C11 仍答不出"——**三处自相矛盾**。
3. **预算真相冲突**：canonical `plan-compare`="预算内/预算内/预算内"（修复前伪造结论），EAC 却在 PRODUCT_ACCEPTANCE_RESULTS L32 当作 run1 证据呈现——**陈旧证据被当成品**。
4. **最终 Copilot 修复无证据**：ledger C11 称 C11 修复后"鼓浪屿好玩吗？"以 human chips 回答，但包内**无对应 trace / 截图**。

---

## 总体结论（供 FINAL_TRACE_AUDIT.md 加工）

- **canonical trace 对 F1（Copilot 地点问答）为 STALE/损坏**：显示空响应，且标签/归档声明虚假、与 ledger 自相矛盾；最终修复态无证据。
- **七门判定：5 PASS / 2 STALE（#2 用 canonical 看、#5）**；其中 #5 的最终修复态证据 MISSING。
- **F11 两处弱断言均坐实**：stay `undefined in/out` 仍判 SELECTED；triple-agreement 以"一致"含糊带过、无定义口径（7 vs 14 vs 文本）。
- **最严重 3 个证据链问题**：
  1. **Canonical Copilot 证据损坏且与 ledger 自相矛盾**（F1）——提交为 READY 的旗舰轨迹显示 Copilot 无响应，且"归档=run1"标签为假。
  2. **"零枚举泄漏"声明被包内 canonical trace 自身反向证伪**（F4/WB-H2/H3）——默认预订界面泄漏 `STRUCTURED_JSON/DETERMINISTIC/DEPARTURE/UNKNOWN/DeepSeek`，而实验室仅测了无旅程/断网的四界面。
  3. **EAC 把 WB-H2–H5「仅部分修复」标记为全部 FIXED/关闭**（任务6）——包内自带复核报告即否定该声明，证据链诚信存疑。
   4.（并列）canonical `plan-compare` 呈现修复前伪造"预算内 CNY 0"且被当成品（F4/任务5 #2 STALE）。
