# Luna Max Overnight Goal 施工计划

## 总目标

在不破坏 CityNexus 已冻结核心的前提下，一夜完成两个层级：

1. Solver Runtime V1 post-freeze hardening，并重新通过所有 Solver/Provider/Weather/Golden gates；
2. 建立 Hermes-ready Agent Foundation V1，包括 persisted delegation policy、safe Agent Tool Gateway、低风险自动 Replan 接受、audit/idempotency、MCP adapter contract 和可复现 E2E。

Hermes live model integration 是条件性 stretch，不允许成为核心 blocker。

## Phase 0：工作树保护

必须先执行：

```powershell
git status --short
git diff --stat
git log --oneline -n 12
```

保存到：

```text
reports/overnight/00_WORKTREE_BASELINE.txt
```

禁止：

```text
git reset --hard
git checkout -- .
git clean -fd
```

## Phase 1：Solver SRH-01..05

只先加入测试：

```text
test_gpt_solver_hardening_next.py
```

先跑，记录真实失败数。

再 semantic merge：

- verified preference signal；
- V1 scope only current disrupted slot；
- post-gate same-assignment heuristic rescue；
- truthful complement/post-gate fallback provenance。

Windows 上必须跑真实 OR-Tools：

```text
SRH-01..05
ORT-01..20
full backend
compileall
Ruff
OpenAPI
```

Phase 1 不通过，不得开始 Agent mutation。可以继续写 Agent docs/tests/scaffold，但不能把 Agent runtime 接进主业务。

## Phase 2：Agent contracts + persisted policy

增加最小 policy，不做未来大而全权限系统。

V1 只真正控制：

- request_replan
- accept_replan

三模式：ADVISORY / ASSISTED / AUTONOMOUS。

Policy 更新只能由普通 user-facing API 完成，MCP 不暴露 set_policy。

## Phase 3：Safe Agent Tool Gateway

实现严格 allowlist：

```text
inspect_journey
inspect_twin
list_replans
search_city_services
request_replan
accept_replan
```

所有工具使用 Pydantic/typed schema。

禁止 arbitrary endpoint/URL/raw SQL。

`accept_replan` 的 policy facts 必须服务器自己从 persisted proposal/journey/C4/evidence 派生。

## Phase 4：低风险 autonomous replan

实现真正一条自动闭环：

```text
Journey ACTIVE
-> Closure Event
-> request_replan
-> proposal PRESENTED
-> Delegation Policy evaluation
-> if ALLOW_AUTO
-> existing accept-time deterministic gate
-> accept
-> old Plan SUPERSEDED
-> new Plan ACTIVE
-> C4 preserved/remapped
-> Twin refreshed
-> audit actor AI_AGENT
```

不要新写第二套 accept 逻辑。尽量抽现有 `accept_replan` 的 domain/service function 复用。

## Phase 5：MCP adapter

如果当前 repo/环境有 MCP Python SDK，做独立 `agent-mcp/` adapter。

如果没有：

- optional dependency；
- mock tests；
- config example；
- live MCP smoke SKIP。

不要为了 pip/GitHub 网络卡一晚上。

## Phase 6：Hermes isolated smoke

只有本机 Hermes 已安装/可稳定启动时执行。

先 tool discovery，不先开全工具 agent。

Hermes 只获得 CityNexus MCP tools。不要给 product runtime terminal/file/browser。

若模型凭证可用，再做一次自然语言 smoke。否则跳过，写明原因。

## Phase 7：Agent Golden E2E

即使没有 Hermes/LLM，也必须用 deterministic/fake agent driver 做真实 backend E2E，证明 Tool Gateway + Policy + Domain authority 闭环。

这是核心 Gate，不允许拿“live Hermes 没 key”当借口跳过。

## Phase 8：可选 frontend stretch

只有 Phase 0-7 全绿而且仍有时间才做：

- 展示 Agent Mode；
- policy cost limit；
- last agent action/decision；
- 不新增复杂聊天 UI；
- 不做 MapLibre；
- 不做 payment automation。

## Phase 9：晨间 checkpoint

输出：

```text
CityNexus-Overnight-Agent-Foundation-Checkpoint-YYYYMMDD.zip
```

必须附：

- CURRENT_STATUS.md
- BLOCKERS.md
- TEST_RESULTS.md
- AGENT_RUNTIME_ARCHITECTURE.md
- DELEGATION_POLICY.md
- HERMES_INTEGRATION_STATUS.md
- CHANGED_FILES.txt
- NEXT_RECOMMENDATION.md
- source/tests/schema/fixtures/OpenAPI

不得包含：

- .venv
- node_modules
- dist
- __pycache__
- *.pyc
- *.db / *.sqlite*
- .pytest_cache
- .ruff_cache
- test-results

## Hard stop

本夜禁止开始：

- payment/refund autonomous execution
- C4 automatic modification
- WebAuthn
- full Hermes memory/skills/cron/delegation
- MapLibre rebuild
- microservices
- Postgres migration
- PPT / Visio

这些留到下一次外部 review 后。
