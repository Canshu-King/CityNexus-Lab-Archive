# WORKBUDDY_XIAOMI_FINAL_VERDICT — v2 定向复检终局裁决

- 日期：2026-09-18 00:2x（北京时间）· 模型：GLM-5.3-Flash
- 审计对象：`CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917.zip`
- SHA-256：`ede70c6628f162a3b81c4c7aa1e15bae1a790abac5ce8d945015cdcfc721e73f` —— **与任务书一致 ✓**
- 方法：定向复检（非全量重审）。3 个并行子代理（R1 证据链 / R3-R5 源码 / R2-R7-R9 源码与包）+ 主线程活体受控流（隔离栈，权威仓库零修改）
- 交付：REPLAN_IDENTITY_RESULTS.md / RESIDUAL_FINDINGS_MATRIX.md / FINAL_MOBILE_UI_RECHECK.md / XIAOMI_TRIAL_STEPS.md / 本文件

---

# 最终裁决：`BLOCKED`

## 验收六条件逐条裁决

| # | 条件 | 裁决 | 一句话依据 |
|---|---|---|---|
| 1 | R1 通过身份真值 | **PARTIAL — 不满足** | 引擎真值 PASS（受控流实证被关闭 place 彻底移除）；但提交 trace 零 ID 级字段、同标题字节级存活 → 旗舰闭环主张不可验证；且新发现 R1-a 缺陷使有预订旅程的闭馆流 100% 422 误拒 |
| 2 | 无不可区分的 Live 接受按钮 | **FAIL** | R2 REPRODUCED：pending.map() 无差别渲染，EAC 自家截图两卡逐字相同 + 两个相同「接受新方案」 |
| 3 | Booking/Copilot/Trips 默认无开发者词汇 | **FAIL** | R3 PARTIAL（6 类枚举仍在默认面）、R4 PARTIAL（裸 tool_name 在折叠外默认展开）、R5 REPRODUCED（check_out/departure/museum 无映射） |
| 4 | Copilot dock 不遮挡关键操作 | **FAIL** | R6 PARTIAL：z-index 25 > sheet 20，不避让，AI 规划 sheet 被遮、按钮被挤成窄条（EAC 自家截图） |
| 5 | 无 AI 假成功边缘 | **FAIL** | R8 REPRODUCED：基线快照失败 → 空集 → fail-open → 旧方案可被误判为新产出 |
| 6 | 前序 B1-B6 热修仍有效 | **PASS** | Me 折叠/价格三态/部分价格/预算 advisory/路由别名/plan-ID 快照全部源码级确认有效 ✓ |

**六条件 1 项部分满足、4 项 FAIL、1 项 PASS → BLOCKED。**

## 本轮最重要的三个事实

1. **引擎比证据好。** WorkBuddy 在隔离栈完成了 EAC 证据里缺失的受控流：closure 事件 → F1_OPTIONAL_REMOVAL 提案
   （diff.removed=["place-gulangyu-organ"]）→ accept 200 → active plan 切换、被关闭实体零存活。
   **重规划机制本身是可信的——不可信的是 EAC 的提交证据。** 他们声称的 removed=1/added=1 闭环没有任何 ID 级字段支撑，
   同标题字节级存活无法排除「同一关闭地点换 ID 回归」。修复后的验收证据必须携带 ID。
2. **旗舰演示流在真实数据形态下会断。** 旅行者先导入预订（C4 承诺 activity_id=None）再报闭馆 ——
   `main.py:6591` 的 `None in {None}` 使重规划一律 422「closed activity is protected」。这不是理论边缘：导入预订是该产品的核心入口。
3. **修复速度很快，收尾差最后一公里。** 前序 B1-B6 全部确认有效，价格三态/预算 advisory/Me 折叠都做对了。
   剩余项（提案卡去重与差异展示、三处枚举映射、dock 避让、fail-closed）都是小刀口改动，估 1.5-2.5 个工作日，
   逐条路径已写入 XIAOMI_TRIAL_STEPS.md。

## 附带记录（不阻塞）
- R7 酒店卡弱差异化（产品质量）；R9 陈旧验收证据未标 PRE_HOTFIX/SUPERSEDED + 包缺 db/schema.sql（离线回放必失败）；
  建向导默认视图仍有「使用封存的天津演示」按钮；`?journey=` 深链不被前端识别（无 journey 时所有路由落建向导）。
- 方法说明：本轮全程未修改 D:\moodle\CityNexus；受控流使用的 journey/plan 种子数据全部写入隔离 DB 副本
  （CityNexus-WorkBuddy/overnight-20260917/recheck_rt_be/backend/citynexus.db）。
