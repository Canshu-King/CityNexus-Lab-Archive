# CityNexus Extreme v2 恢复线（2026-09-19）

一句话：Codex Extreme v2 中断前未提交的修复已冻结成可交接补丁，并在当前整合顶端
`7f2f5bb` 上重验；它的突变矩阵经复核后有两个真实缺口被补成门禁，另有一个缺口被确认仍存在。

阅读顺序：

1. `reports/RECOVERY_REPORT.md` — 全部结论、证据与未收口判断
2. `patches/` — `CX-REC-001/002/003`（可单独评审合入）与合并版
3. `tests/` — RX-1 跨 Journey 触发、RX-2 mock 冒充硬真值、RX-3 陈旧游标 fail-closed
4. `raw/` — 全量对照日志、名单 diff、`mutation_audit_targeted.json`、`repro_commands.txt`
5. `verify/citynexus` — 提交态冻结（分支 `qoder/recovery-extreme-v2` @ `f331e43`）

给 owner 的最小动作：把三个补丁按 001 → 002 → 003 顺序合入整合线，附带三条 RX 门禁；
RX-4（generate 路径的 C4 承诺保护）仍缺，见报告 §5 末。

全程只读 `_qoder_integration_20260919`、`_qoder_th_20260918`、`CityNexus`、
`_codex_sol_extreme_v2_20260919`：未修改、未提交、未清理。
