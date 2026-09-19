# EAC_PROGRESS_TIMELINE — WorkBuddy 独立检查点

## Checkpoint 01 — 2026-09-17 03:00（+2h）

### 变更规模（01:00 → 03:00，排除 node_modules/.venv/缓存）
- 共 17 个文件变更。前端 3 源文件 + dist 重建（01:21）；后端 4 源文件 + 1 测试。
- 前端：`V8Experience.tsx`(01:17, 73.4KB)、`PlanWithAiSheet.tsx`(01:17)、`HotelsPanel.tsx`(01:29)、`frontend/dist` 重建（01:21）
- 后端：`main.py`(01:20, 386KB)、`stay_mobility.py`(02:28, 65KB)、`operations/v9.py`(02:29, 55KB)、
  `tests/test_snapshot_m_truth_edges.py`(01:29, 12.3KB)
- DB：根目录 `citynexus.db`(01:20, 5.4MB) —— 注意：**仓库内有两个 DB**（根 5.4MB vs backend/ 37.8MB），
  EAC 运行时用哪个取决于 uvicorn cwd；审计其验收证据时必须先确认连的是哪个 DB。

### 证据产出
- 仓库内**尚无**新的 reports/、output/playwright/、根目录 md 产物（截至 03:00）。
- 检测到 EAC 的 Chrome 自动化进程自 02:20 起活跃（多个 chrome 实例）—— 正在跑浏览器流程。
- Snapshot M 回归测试已更新（01:29），符合任务书 Phase 1 优先级。

### 阶段判断
- 前后端并行推进中，未见 BACKEND_ESCAPE_PATTERN（前端 01:17-01:29 有实质活动，dist 已重建）。
- 02:28-02:29 回到后端（stay_mobility/operations v9）。
- 尚无法判断其 same-Xiamen 验收是否完成；等其产出 VISIBLE_UI_TRACE.json / 截图后做 Phase 3 反作弊审计。

### WorkBuddy 同期独立发现（供对照）
- **P0**：新 journey + AI 规划请求 → UI 宣称「方案已准备好」+ stepper 全打勾，但后端
  `plan_versions=0 / activities=0 / stay_journey_options=0 / real_place_candidates=0`；
  agent 内部结论显示厦门 `search_city_services` 候选池为空（鼓浪屿/沙茶面/海边均无候选）。
  即：**首次用户在无预置城市数据的新 journey 上，AI 规划必然空转，而 UI 谎报成功**。
  EAC 若用预置好的演示 DB 跑验收，将完全掩盖此缺陷 —— 这是 Phase 3 重点核查项。
- setup 页（新建行程三步）与主壳样式割裂（近无样式裸表单），与参考 03/04 差距巨大。
- Today 页含违禁文案：还没休息(STILL UP)、规划就绪(PLANNING READY)、厦门 · journey；
  巨大 EN 按钮占主视口第二行；Copilot 浮条常驻遮挡底部卡片。
- 查看方案 → 行程工作台：无候选方案/无逐日行程/无活动卡片；"Provider price unavailable"、
  "min" 英文泄漏；「步行暴露」「方案健康度/受保护·0分钟余量/已通过全部安全检查」内部语义见客。

## Checkpoint 02 — 2026-09-17 02:50（+4h 前）

### Git 硬证据（只读审计）
- 分支 `eac/v19.2.2-realphone-codegate`（自 master 7d22cd0 切出）；**今晚 0 commit**（HEAD 仍是 09-05 的 7d22cd0）。
- `git diff HEAD` 全 tracked 仅 `.gitignore` +20 行；PlanWithAiSheet.tsx / main.py / HotelsPanel.tsx 等 mtime
  虽新（02:41-02:42），但**内容与 HEAD 零差异**。
- reflog：checkout 分支后 **8 次 `reset: moving to HEAD`** —— 解释了 mtime 大面积刷新：这是 reset 刷 stat，
  不是代码修改。**纠正 Checkpoint 01 的判断**：当时把 mtime 活动（V8Experience 01:17、HotelsPanel 01:29、
  dist 重建等）记为「变更规模」，经 diff 验证其中 tracked 源码部分**不构成内容变更**；dist/pyc 等构建产物
  的重建仍可能真实发生。
- 111 个 untracked 项经抽样核实为历史版本 zip（V7-V13.1.2 各 Final 包）与 09-12/09-13 旧报告，非今晚产物。
- `stay_mobility.cpython-312.pyc` 02:42 重建 → EAC 的后端进程在活跃运行（可能跑测试）。

### 结论（截至 02:50）
- 可观测事实：分支存在 + 进程活跃 + **零可追溯代码产出 + 反复同点 reset**。
- EAC 若在最终阶段一次性 commit，则现阶段无法评估其真实进度；Phase 3 报告已按「无可验收证据」记录。
- WorkBuddy 侧同期完成：Bookings 敌意三例、多模态收件箱两路、Copilot 真人问句、四 tab 巡检、
  酒店 stay 页 —— 全部截图+trace 双证据落盘（screenshots/ + evidence/）。

## Checkpoint 03 — 2026-09-17 03:04（+6h 前置复核）

- git 状态与 checkpoint-02 完全一致：0 commit、tracked 仅 .gitignore、reflog 继续 reset 循环（累计 11 次）。
- `stay_mobility.pyc` 02:42 后无新编译产物；EAC 后端进程活跃度下降。
- WorkBuddy 本轮已定稿裁决 BLOCKED（07:00 晨检仍保留翻案程序，见 WORKBUDDY_FINAL_VERDICT.md）。
