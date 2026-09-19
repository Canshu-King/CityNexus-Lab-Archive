# CityNexus Solver Runtime V1 外部审查

日期：2026-09-10

## 结论

Solver Runtime V1 主体实现可信，Windows checkpoint 自报：

- ORT-01..20：20 PASS
- focused inherited regression：73 PASS / 1 SKIP
- full backend：230 PASS / 2 SKIP，exit code 0
- compileall：PASS
- Ruff check / format：PASS
- OpenAPI：39/39
- frontend build：PASS
- backend-connected Playwright：PASS

当前外部环境没有 OR-Tools wheel，无法在这里重新执行真实 CP-SAT 分支。因此不把 Windows 结果冒充成本地独立复现。

但对源码与非 OR-Tools 路径做额外对抗审查后，新发现 5 个 hardening gap。它们没有证明 Solver 可以绕过 CityNexus authoritative feasibility，但会影响候选质量、V1 scope honesty、fallback completeness 和 provenance honesty。因此建议在正式 external freeze 前先修复。

## SRH-01 Verified preference 没有真正进入 Solver Problem

`SolverReplacementOption.preference_milli` 支持 verified preference，但 `generate_replan()` 当前对所有 option 写死为 `0`。

影响：

- CP-SAT 声称可以以 verified preference 作为后层 tie-break，实际上 runtime 没喂这个事实；
- `candidate_count` 较小时，高偏好候选可能根本没进入后续 verified scoring。

建议：使用现有 `verified_interest_preference_fit()`，无 verified preference 时沿用 scoring 的 neutral 0.5，即 500 milli。

## SRH-02 Solver V1 对受影响 Activity 位于下一 C4 之后的场景仍会尝试运行

V1 problem 把 window 建模为：

`current execution location -> replacement -> next C4 anchor`

如果真正被关闭的是 C4 之后的 Activity，这个模型边界不成立。

建议 V1 fail closed，交回 deterministic path。未来 V2 再支持跨锚点/多窗口优化。

## SRH-03 Solver V1 对尚未执行的未来 Activity 也会尝试运行，即使中间还有多个未建模 Activity

V1 当前没有为这些 intervening mutable Activities 建变量/约束。虽然最终 deterministic gate 能拒绝坏方案，但 Solver 的问题抽象本身不完整。

建议 V1 只对 `affected == current_execution` 的 single-slot recovery 启用。未来多 Activity Solver 再扩展。

## SRH-04 被 post-gate 拒绝的 Solver assignment 会提前屏蔽同 semantic assignment 的 deterministic fallback

当前 `solver_assignment_keys` 在 authoritative gate 之前就把相同 heuristic assignment 去掉。

因此可能出现：

- OR-Tools 给 Design Library 一个坏 schedule，Gate 正确拒绝；
- deterministic Design Library schedule 原本可行；
- 但它已经被提前删掉，无法救场。

建议：保留所有 heuristic specs。只有某 semantic assignment 真正通过 gate 成为 proposal 后，才抑制相同 assignment 的后续重复项。

## SRH-05 provenance 把正常 candidate-set complement 写成 `ORTOOLS_POST_GATE_FALLBACK`

如果 Solver 成功生成一部分候选，而 heuristic 只是补足其他 semantic options，这不是 post-gate failure。

建议区分：

- `ORTOOLS_CANDIDATE_SET_COMPLEMENT`
- `ORTOOLS_POST_GATE_FALLBACK`
- `ORTOOLS_UNAVAILABLE`
- `ORTOOLS_UNKNOWN`
- `SOLVER_V1_UNSUPPORTED`

## 独立复现

对原 checkpoint 加入 `test_gpt_solver_hardening_next.py`：

```text
5 FAILED
```

在参考修复 copy：

```text
SRH-01..05       5 PASS
selected legacy  15 PASS
provider/weather/golden regression 35 PASS
compileall       PASS
```

由于当前环境缺 OR-Tools，不宣称真实 CP-SAT 回归已经在本机重跑。Windows Codex 必须使用已安装的 `ortools==9.15.6755` 重跑 ORT-01..20 与 full suite。
