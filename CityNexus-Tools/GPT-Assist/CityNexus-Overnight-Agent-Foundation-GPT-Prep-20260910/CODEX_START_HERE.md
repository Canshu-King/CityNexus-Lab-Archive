# Codex Start Here

本包不是让你机械 apply patch。

正确顺序：

1. 读取 `reports/SOLVER_EXTERNAL_REVIEW.md`。
2. 读取 `contracts/OVERNIGHT_GOAL_PLAN.md`。
3. 读取 `contracts/AGENT_RUNTIME_ARCHITECTURE.md`。
4. 在真实 `D:\moodle\CityNexus` 先检查 git status/diff。
5. 只放入 SRH tests，先跑真实工作树。
6. 只 semantic-merge 仍缺失的 solver hardening。
7. Solver 全绿以后才开始 Agent runtime mutation。
8. Agent Foundation 按 AGT matrix tests-first。
9. Hermes live integration 是条件性，不可阻塞核心。
10. 早晨打 fresh-extract checkpoint 后停止。

禁止 reset/rollback 用户现有工作。
