# CityNexus Agent Runtime V1 架构

## 目标

把现有 `AI Copilot = explanation layer` 升级成一个真正可以调用 CityNexus 能力的受约束 Journey Agent，同时保留所有已冻结的权威边界。

核心关系：

```text
Hermes / other Agent Brain
        |
        v
CityNexus MCP / Agent Tool Gateway
        |
        v
Traveler Delegation Policy
        |
        v
Authoritative CityNexus APIs / Domain Services
        |
        v
Deterministic Feasibility + C4 Protection
        |
        v
Domain Truth / SQLite
```

## 绝对边界

- Hermes 不直接访问 SQLite。
- Hermes 不直接 import SQLAlchemy Session。
- Hermes runtime 不获得 shell、terminal、file edit、browser 控制等 CityNexus 产品权限。
- Agent 不允许修改自己的 Delegation Policy。
- Agent 不能伪造 provider evidence、feasibility result、C4 state、payment state。
- OR-Tools、Valhalla、Open-Meteo、AI 都不是 authority。
- `accept_replan` 最终仍走现有 accept-time deterministic revalidation。

## 三种用户模式

### ADVISORY

AI 可以：
- 查看 Journey/Twin；
- 搜索；
- 请求生成 ReplanProposal；
- 解释和比较。

AI 不可自动激活新 Plan。

### ASSISTED

在显式 policy 范围内，可以自动执行低风险、可逆、已过 deterministic gate 的动作。

V1 只建议开放：
- 低风险 `accept_replan`。

默认仍要求：
- C4 preserved；
- hard constraints PASS；
- cost delta 不超过授权；
- provider evidence 非 degraded；
- 非 CRITICAL event。

### AUTONOMOUS

可以给更高预算阈值或更多低风险权限，但仍不能绕过 protected action boundary。

付款、退款、修改 C4 默认永远不能无确认自动执行。

## V1 Safe Tool Surface

Hermes MCP V1 只暴露：

```text
inspect_journey
inspect_twin
list_replans
search_city_services
request_replan
accept_replan
```

明确不暴露：

```text
set_policy
payment
refund
modify_c4
raw_sql
arbitrary_http
terminal
file
browser
```

## Delegation Policy V1 建议持久化字段

推荐新表 `traveler_agent_policies`：

```text
traveler_id PK/FK
mode
agent_auto_accept_replan
max_auto_replan_cost_delta_minor
allow_auto_when_provider_degraded
allow_auto_on_critical_event
version
created_at
updated_at
```

后续再扩展 booking/payment，不要今晚一次把所有未来权限都塞进去。

## Policy evaluation 必须使用 server-derived facts

`accept_replan` 的判断事实必须来自：

- persisted ReplanProposal；
- persisted ReplanDiff / verified evidence；
- 当前 Journey；
- 当前 C4 Commitments；
- accept-time deterministic revalidation。

模型传进来的布尔值不可信。

Agent 只能提交类似：

```text
proposal_id
request_id
agent_session_id
```

不能提交：

```text
hard_constraints_passed=true
c4_preserved=true
cost_delta=0
provider_ready=true
```

这些必须由服务器自己读取。

## Audit

现有 `audit_logs` 足够 V1 使用，但 `record_audit()` 建议向后兼容地增加：

```text
actor_type
actor_id
```

Agent action audit 至少记录：

- actor_type = AI_AGENT
- actor_id = hermes 或 provider-neutral agent id
- policy version
- authorization decision
- reason codes
- journey id
- proposal id
- before/after state

不要把 API key、prompt 全文、模型密钥写入 audit。

## Idempotency

所有 Agent mutation 必须有稳定 request id / idempotency key。

推荐：

```text
agent.accept_replan:{agent_session_id}:{proposal_id}:{request_id}
```

重复调用必须 replay，不得重复 activate 或重复写 transaction。
