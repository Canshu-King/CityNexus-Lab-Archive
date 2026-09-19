# FINAL_TRACE_AUDIT — 终版 same-Xiamen 证据链审计（TRACE_INTEGRITY_GATE）

被审证据：EAC 终包 evidence\（VISIBLE_UI_TRACE.json 11:17 / VISIBLE_UI_TRACE_run1.json 14:55 /
OVERNIGHT_RUN_LEDGER.jsonl 15:05 / LAB_CYCLES.jsonl / scenario_*.json / viewports_*.json）+
144 张截图（11:20–14:55）+ reports\（AUTONOMOUS_CYCLE_1-5、WORKBUDDY_FINDINGS_REVALIDATION）。

## 七项关键特性门

| # | 特性 | 修复时间（源码 mtime） | 证据时间 | 证据晚于修复？ | journey | 判定 |
|---|---|---|---|---|---|---|
| 1 | AI planning success gate | PlanWithAiSheet 14:5x | C1_06/07 截图 14:52 | ✅ | C1 系列 | **PASS**（其环境方案可生成；注意其 trace 环境与回放环境 places 池行为不一致） |
| 2 | plan select | 14:5x | canonical trace 11:17 | ❌ **早于修复** | 与 run1 不同 | **STALE**——canonical 显示修复前伪造「预算内」标签 |
| 3 | hotel select | 14:5x | C1 酒店步 14:53 | ✅ | C1 | PASS（但 check-in/out 字段 undefined 见 F11） |
| 4 | booking confirm | 14:5x | C1_14/15/16 14:53 | ✅ | C1 | PASS（卡面 truth 有改善） |
| 5 | Copilot place answer | copilot_contract.py **14:56:24** | canonical 11:17 / run1 14:55 | ❌ **两份均早于修复** | — | **MISSING**——修复后人类化回答仅存在于 ledger 叙述，包内零可见证据 |
| 6 | Live material replan | 14:5x | C1 后段 14:53-55 | ✅ | C1 | PASS |
| 7 | replan accept | 14:5x | C1 终态 | ✅ | C1 | PASS |

**统计：5 PASS / 2 STALE / 1 MISSING。**

## 关键发现

1. **canonical trace 对 F1 既 stale 又损坏**：VISIBLE_UI_TRACE.json（11:17，包自称 canonical）中
   「鼓浪屿好玩吗？」步骤 `status:"empty"`、result 仅回显问题、**无任何回复**。
   run1（14:55）`status:"answered"` 但内容是修复前的优雅拒绝（「我没有可靠识别这条请求」）。
   两份文件 journey/状态/时间均不同，**ledger 称「归档=run1」为假**。
2. **修复后证据缺失**：Copilot 分类修复（好玩/值得/怎么样 → DISCOVER）落在 14:56:24，
   晚于全部包内 trace；包内没有任何一张截图或 trace 展示修复后的人类化回答。
   WorkBuddy 活体复测（16:07，晚于修复）证明修复**有效果但不彻底**：诚实拒绝+人类按钮+零枚举 ✅，
   但仍给不出「鼓浪屿」的实质回答（城市真相池空）。
3. **「零枚举泄漏」声明被包内证据反向证伪**：canonical trace 默认预订界面含
   STRUCTURED_JSON / DETERMINISTIC / DEPARTURE / UNKNOWN / DeepSeek；
   活体复测 bookings 页含 Journey Memory / 受保护 C4 / UNKNOWN_REALTIME。
4. **诚信问题**：EAC 将 WB-H2–H5 标为全部 FIXED/关闭，但其包内自带的
   WORKBUDDY_FINDINGS_REVALIDATION.md 即承认仅部分修复——自述与验收文档自相矛盾。
5. **F11 弱断言**：stay 证据 undefined 入住/退房字段仍判 SELECTED；
   triple-agreement 三量纲（UI 可见 7 / 后端 14 / live 文本）无定义口径即宣布「一致」。
6. **正面记录**：C1 循环（14:52-14:55）的 AI 规划→选方案→酒店→预订→replan 链路在其环境
   全程有截图、同 journey 连续、无 demo/reset 替代——五门 PASS 的证据质量本身是合格的。

## 结论

产品实现与证据新鲜度必须分开评级：**实现侧**五门已过；**证据侧** canonical trace 损坏、
旗舰 Copilot 修复零可见证明、plan select 证据 stale。按 TRACE_INTEGRITY_GATE：
「实现修复但最终可见证明缺失 → 不得授予完整试用验收」。
