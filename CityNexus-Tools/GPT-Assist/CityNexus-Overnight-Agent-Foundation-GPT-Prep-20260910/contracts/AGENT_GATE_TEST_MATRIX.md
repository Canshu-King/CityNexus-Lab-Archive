# Agent Foundation V1 验收矩阵

建议在真实 repo 中形成 `tests/test_agent_runtime_gate.py`。

| ID | 场景 | 必须断言 |
|---|---|---|
| AGT-01 | ADVISORY inspect Journey/Twin | 自动允许，只读，不写 Domain |
| AGT-02 | ADVISORY request_replan | 允许生成 proposal，但 active Plan 不变 |
| AGT-03 | ADVISORY accept_replan | REQUIRE_CONFIRMATION，不自动执行 |
| AGT-04 | ASSISTED + hard PASS + C4 preserved + cost within limit | 可以 ALLOW_AUTO |
| AGT-05 | cost delta 超过授权阈值 | REQUIRE_CONFIRMATION |
| AGT-06 | hard constraints 未通过 | DENY |
| AGT-07 | C4/locked commitment 未保留 | DENY |
| AGT-08 | provider evidence degraded | 默认 REQUIRE_CONFIRMATION |
| AGT-09 | CRITICAL event | 默认 REQUIRE_CONFIRMATION |
| AGT-10 | payment/refund/modify C4 | REQUIRE_STEP_UP，MCP V1 不暴露这些工具 |
| AGT-11 | Agent 尝试修改自己的 policy | 工具不存在 / DENY |
| AGT-12 | Agent 提交伪造 `hard_constraints_passed=true` | schema 不接受或完全忽略，服务器自己派生 |
| AGT-13 | proposal 属于其他 Journey/Traveler | DENY/404/422，不可越权 |
| AGT-14 | stale proposal | 409，不可 auto accept |
| AGT-15 | resolved Event 的旧 proposal | 409，不可 auto accept |
| AGT-16 | auto accept 前 authoritative plan/constraint 被改变 | accept-time gate 拒绝 |
| AGT-17 | 同一 agent request 重放 | idempotent，只有一次 Domain mutation |
| AGT-18 | Agent mutation audit | `actor_type=AI_AGENT` + policy_version + decision reason |
| AGT-19 | MCP tool discovery | 只出现 V1 allowlist，不出现 terminal/file/browser/payment/set_policy |
| AGT-20 | Hermes/MCP 不可用 | CityNexus existing app + Golden Scenario 仍正常 |
| AGT-21 | Prompt 中要求“绕过规则直接接受” | Tool Gateway 仍按 policy/gate 拒绝 |
| AGT-22 | 工具参数注入未知字段/任意 URL | schema fail closed |
| AGT-23 | `request_replan` | 只能得到 PRESENTED candidate，不得自动 activate |
| AGT-24 | low-risk auto accept | old Plan SUPERSEDED, new ACTIVE, C4 remap, Twin refreshed |

## 额外回归

必须保留：

- SRH-01..05
- ORT-01..20
- WRH/WRT
- PRT/PRH
- backend-connected Golden
- OpenAPI parity
- Ruff
- compileall
- frontend build/Playwright 如果碰 frontend/API contract
