# ACCEPTANCE_INTEGRITY_REPORT.md — 验收诚信 / 反作弊审计（Phase 3）

- 审计者：WorkBuddy（独立并发红队）
- 证据时点声明：本报告的产品行为证据全部来自**隔离副本快照**（`baseline/app_snapshot_0115/`，后端 8011 / 前端 5181），对应主仓库 ~01:15 状态；主仓库审计基于 git 只读命令（02:50）
- 立场：`/demo/reset`、直接 API 代打、无 journey 上下文的 curl 截图**均不构成** same-Xiamen 验收证据

---

## 1. 产品自身的诚信缺陷（隔离副本实测）

### 1.1 [P0] AI 规划「假成功」链路 —— UI 成功叙事与后端真相脱钩
- 现象：AI 规划流程 UI stepper 全部打勾、终态文案「方案已准备好」（`fa_*` 截图与 `flow_ai2.js` trace），但后端 `plan_versions` 表仍为 0 行、`/api/v1/journeys/{id}/plans` 返回 `[]`、`active_plan_version_id: null`（`evidence/db_counts.txt`、`evidence/api_plans_0250.json`、`copilot_trace_v3.json apiLog`）
- 内部真相（`evidence/db_agent_runs.txt`）：agent_runs 记录显示候选池为空（鼓浪屿/沙茶面/海边全部 search 为空），agent **诚实拒绝编造** —— 后端 AI 层行为正确，是**前端把失败包装成成功**
- 影响：小米 13 Ultra 试用者会以为拿到了方案，随后「行程/地图/酒店」全部为空 —— 三连懵
- 修复方向（影子补丁 P2 已实现，见 `lab/patches/`）：stepper 终态必须反映 plan 实际存在；失败态给出诚实空态 + 下一步动作

### 1.2 [P1] 「你的真实预订，受保护」承诺与实现不符
- Bookings JSON 框导入时用户提交的 `price` 字段被静默丢弃（wallet API 返回 `price:{amount_minor:null,status:"UNKNOWN"}`，`copilot_trace_v3.json`）——「已确认」的价格事实没有被保护
- 导入成功卡片不显示出发地/目的地（数据在库：`origin:"厦门北",destination:"福州南"`），消费者无法核对导入的关键事实是否正确
- 非 JSON 输入零反馈（B1）——「审核并保护」按钮在最常见的用户输入（自然语言）下静默失败

### 1.3 [P2] 消费者可见的「证据」含未核实的占位数据
- 酒店页无候选时渲染「费率证据」空壳卡：`Provider price unavailable · explicit`、`供应商 captured hotel · 0% confidence`（`ht_01_after_select.png`）——把「无数据」渲染成「证据卡片」，与「已采集证据」的 kicker 矛盾

## 2. EAC 产出审计（主仓库，git 只读，02:50）

### 2.1 Git 事实
| 项目 | 状态 |
|---|---|
| 当前分支 | `eac/v19.2.2-realphone-codegate`（自 master 7d22cd0 切出）|
| 今晚新 commit | **0**（HEAD 仍是 2026-09-05 的 `7d22cd0`）|
| tracked 内容变更 | 仅 `.gitignore` +20 行 |
| reflog | `checkout: master → eac/...` 后 **8 次 `reset: moving to HEAD`** |
| 工作树 | 112 项 = 1 M(.gitignore) + 111 untracked（历史版本 zip/旧报告，非今晚产物）|
| 进程活动 | `stay_mobility.cpython-312.pyc` 02:42 重建 → EAC 后端进程活跃 |

### 2.2 推断与纠正
- **纠正 checkpoint-01 记录**：此前记录「EAC 01:29 修改 HotelsPanel.tsx / 01:17 V8Experience.tsx」——经 02:50 `git diff HEAD` 验证，这些文件**内容与 HEAD 零差异**，mtime 变化系 git reset 刷新 stat 所致，不构成修改证据
- 文件 mtime 时间线（PlanWithAiSheet 02:41、main.py 02:41）结合 0 内容变更 + 反复 reset，存在两种解释：(a) EAC 在 read-modify-verify 循环中重写了相同内容；(b) reset 循环掩盖了失败的实验。**无论哪种，截至 02:50 无可验收的代码产出**
- `git reset: moving to HEAD` 同点重置本身不丢工作树文件（未发现 --hard 痕迹），但 8 次重置提示 EAC 的变更管理流程不稳定

### 2.3 验收结论（截至 02:50）
1. EAC 未产出任何 same-Xiamen / same-journey 可验收证据（无 VISIBLE_UI_TRACE、无验收包、无 commit）
2. 「EAC 正在修复」无法证伪也无法证实——唯一可观测事实是分支存在 + 进程活跃 + 零产出
3. 对 final 裁决的影响：若晨检（07:00）EAC 仍无 commit + 无验收证据，WorkBuddy 倾向 **BLOCKED**（理由：产品 P0 假成功链路未修复 + 实施方无可追溯产出）

## 3. WorkBuddy 自身证据链完整性自检
- 所有 UI 断言均有截图 + trace JSON 双证据（`screenshots/`、`evidence/`）
- 数据库断言直接查隔离副本 SQLite（`db_counts.txt`）
- API 断言来自浏览器内网络拦截（非外部 curl 代打），与 UI 会话同 journey
- 未使用 /demo/reset；未修改主仓库；测试数据均标注 `WB-` 前缀便于清理
