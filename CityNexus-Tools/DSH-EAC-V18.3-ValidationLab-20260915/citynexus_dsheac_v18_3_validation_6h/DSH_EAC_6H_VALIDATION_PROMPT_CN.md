请执行 CityNexus DeepSeek Harness EAC V18.3 Independent Validation Lab。

这是约 6 小时有效工程工作量的无人值守夜间任务。

Codex 当前正在独占修改：

D:\moodle\CityNexus

绝对不要修改这个主工作区。

主工作树只允许只读参考。

你的独立工作目录：

D:\moodle\CityNexus-Tools\DSH-EAC-V18.3-ValidationLab-20260915

用户已经睡觉。

先阅读：

README_FIRST.md
NO_USER_DECISION_POLICY.md
VALIDATION_MATRIX.md
OUTPUT_CONTRACT.md

这次 Harness EAC 接管原本交给 WorkBuddy 的验证任务。

不要把它变成第二个 Codex。
你的身份是：

独立 QA
+
adversarial user
+
runtime truth reviewer
+
Hermes chaos lab
+
semantic regression lab

==================================================
0. 工作方式
==================================================

启动时只对当前主树做一次只读快照/复制。

所有：

- backend
- frontend
- DB
- Hermes profile
- gateway
- tests
- screenshots
- reports

都必须运行在隔离目录。

不要修改用户主 Hermes profile `citynexus`。

创建独立 profile，例如：

citynexus-harness-lab

如果系统已有 DeepSeek credential：

只允许在子进程 / process scope 复用。

不得：
- 打印值
- 写进报告
- 写进代码
- 打进 ZIP

如果没有 credential：
记录真实 blocker，
继续剩余测试，
不要伪造 native proof。

==================================================
1. P0 — 隔离 Native Hermes 真 E2E
==================================================

建立 throwaway stack。

建议：

backend:
127.0.0.1:8022

frontend:
127.0.0.1:4178

独立 SQLite DB。

独立 Hermes gateway port。

lab MCP 必须指向隔离 backend，
不能指向 8000 权威实例。

真正证明：

Copilot
-> DeepSeek SemanticEnvelope
-> HERMES_NATIVE_MCP
-> Hermes Runs API
-> SSE
-> real CityNexus MCP tool
-> Gateway
-> Guardian
-> proposal/result

Native E2E Gate：

1. Hermes lab gateway reachable
2. Copilot message creates real run_id
3. runtime_identity = HERMES_NATIVE_MCP
4. SSE contains actual CityNexus MCP tool event
5. Gateway sees the tool request
6. result comes from throwaway DB
7. no authoritative DB mutation

至少看到多个真实 tool：
- inspect_journey
- inspect_twin
- search_city_services
- request_replan

不保存 hidden chain-of-thought。

==================================================
2. P0 — Chaos / Reconnect / Stop
==================================================

主动注入：

- Hermes gateway 未启动
- Hermes gateway 中途关闭
- gateway restart
- SSE断线
- SSE reconnect
- duplicate event
- out-of-order event
- malformed event
- stale run id
- unknown run id
- Stop during tool.started
- Stop after proposal.created
- Stop after approval.required
- tool failure
- MCP server unavailable
- backend unavailable
- DeepSeek unavailable
- provider unavailable

验证：

- 不假 completed
- 不假 HERMES_NATIVE_MCP
- UI不无限 loading
- reconnect 不重复 event
- Stop 后不能晚到 mutation
- event sequence 可稳定去重
- DIRECT fallback 标识真实

==================================================
3. P0 — Concurrency / Idempotency / Approval
==================================================

至少：

A. 同 Journey 两个 concurrent Hermes runs
B. 不同 Journey 两个 runs
C. 同 request_id 同 payload
D. 同 request_id 不同 payload
E. approval 消费两次
F. approval 跨 journey
G. approval 跨 action
H. approval expiry
I. stop-vs-complete race
J. reject-vs-execute race
K. approve-vs-stop race
L. superseded proposal 再 approve
M. mutation 双击
N. retry 后重复提交

验证：

- 不重复执行
- 不跨作用域
- 不 ghost mutation
- error code/message 可理解
- UI不提前显示 authoritative

不要修改系统时间。
需要 expiry 测试时使用 fixture / DB seam。

==================================================
4. P1 — 240+ Semantic / Traveler Corpus
==================================================

创建至少 240 条 meaningful case。

字段至少：

id
locale
city
timezone
currency
traveler_context
message
expected_intent
expected_assertion_status
expected_effective_time
expected_runtime_route
expected_mutation_policy
expected_event_creation
expected_confirmation
notes

覆盖：

中文
英文
中英混合

城市至少：
天津
福州
北京
上海
重庆
厦门
东京
新加坡
London
以及至少 3 个县城/小城市

Traveler contexts：
情侣
老人
轮椅
婴儿
儿童家庭
商务
摄影
学生
多人团体
大件行李

重点：
WHAT_IF vs real disruption
future confirmed disruption
negation
historical
rumour
habitual/general fact
ambiguous request
multi-goal
refund/cancellation
accessibility
day rhythm
budget
walking limit
protected commitment
prompt-injection-like attempts

至少：
40 对中英 hard pairs
20 对 hypothetical/asserted
20 对 general/current incident
20 对 explain/mutate
20 对 personal emergency/city event

如果 DeepSeek live 可用：
对一部分做 structured-output canary。

模型输出不是 authority，
只验证 semantic contract。

==================================================
5. P1 — Runtime/API Contract
==================================================

重点重新验证并自动化：

- native Hermes unconfigured endpoint 是否仍裸 500
- capabilities 各 branch schema 一致
- `ready` 是否稳定存在
- runtime identity 是否按 live readiness
- events SSE unconfigured 不得 200+空流撒谎
- stop unknown run
- get unknown run
- health AI readiness
- empty Place catalogue 计划生成不能裸 500
- error envelope shape
- retryability
- request_id conflict message
- DIRECT/Hermes response contract

优先输出 tests-only patch。

==================================================
6. P1 — Desktop / Mobile / A11y
==================================================

视口：

1440x900
1280x720
390x844
430x932

状态：

DIRECT
Hermes running
Hermes failed
Hermes stopped
Hermes unavailable
DeepSeek unavailable
offline/stale
approval required
proposal only

检查：

keyboard
focus-visible
Escape
focus return
touch target
horizontal overflow
long Chinese
long English
reduced motion
runtime truth
Stop
approval
failed tool
event ordering
reconnect duplicates

如果 axe-core 已有，可定点使用。

==================================================
7. P2 — 轻量稳定性 / 性能
==================================================

隔离环境：

10 sequential agent runs
3 concurrent read-only runs
2 concurrent proposal-only runs

记录：

event count
duplicates
reconnect count
p50/p95 tool latency
run duration
UI responsiveness

Agent timeline 测：

100 events
300 events
1000 events

检查：

memory runaway
unbounded history
明显 N+1 polling
UI freeze
reconnect storm

不要做高强度外部 Provider load test。

==================================================
8. 夜间后半段只读 re-check
==================================================

任务后半段允许再次只读查看 Codex 最新主树。

只针对你已经发现的具体 defect 做定点确认。

不要：
- 重复制整个项目
- 重跑整轮审计
- 改主树

给 Codex handoff 按：

P0 blocking
P1 before user trial
P2 later

每条必须包含：

reproduction
impact
exact file/symbol
recommended fix
test proof

==================================================
9. 产出
==================================================

完整执行 OUTPUT_CONTRACT.md。

优先：

patches/V18_3_VALIDATION_TESTS_ONLY.patch

只有极小、低冲突、证据充分的修复才可以另外给：

patches/V18_3_LOW_CONFLICT_FIXES.patch

但不要应用到主树。

约 6 小时有效工作后停止。

如果核心任务提前完成：

- semantic corpus 扩到 320 meaningful cases
- chaos matrix 扩展
- race condition 扩展
- mobile failure UX
- SSE replay/reconnect
- 1000 event performance
- approval expiry/superseded

不要重复测试凑时间。

最终打包：

D:\moodle\CityNexus-Tools\CityNexus-DSH-EAC-V18.3-ValidationLab-20260915.zip

现在开始。
