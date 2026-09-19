# CityNexus Overnight Agent Foundation GPT Prep

本包基于 `CityNexus-Solver-Runtime-Checkpoint-20260910.zip` 的外部审查制作。

包含：

- Solver Runtime V1 额外 SRH-01..05 对抗测试；
- 已验证 reference solver hardening patch；
- Agent Foundation V1 架构；
- Delegation Policy reference code；
- Hermes MCP boundary；
- AGT-01..24 test matrix；
- Luna Max overnight Goal 施工计划；
- 一份可直接粘贴给 Codex Goal 模式的完整 Prompt。

参考 policy code 已在当前环境验证：10 PASS。
Solver hardening reference：SRH 5 PASS，selected legacy 15 PASS，Provider/Weather/Golden 35 PASS，compileall PASS。

当前环境缺 OR-Tools，真实 CP-SAT 分支必须由 Windows Codex 再跑。
