请执行 CityNexus WorkBuddy V19.1 Moving-Baseline Convergence Red-Team。

这是约 6 小时有效工程工作量的独立验证任务。

Codex 可能仍在修改：

D:\moodle\CityNexus

绝对不要修改主工作区。

你的工作目录：

D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915

先阅读：

README_FIRST.md
MOVING_BASELINE_PROTOCOL.md
VERIFIED_DELTA_TARGETS.md
ACCEPTANCE_MATRIX.md
OUTPUT_CONTRACT.md

==================================================
0. 不要再重做上一轮
==================================================

上一轮已经完成：

494 raw-language DeepSeek cases
168 field flows
大规模 baseline scan

这轮不要再照抄。

目标是：

针对当前 Codex V19 新实现，
把已发现缺陷逐个关掉或证明仍存在，
然后补完整 capability lifecycle E2E。

==================================================
1. Snapshot A
==================================================

任务开始时：

只读复制当前主树到 Snapshot A。

记录：

timestamp
relevant files
backend import
tests present
capability API symbols

第一件事：

python -c "import app.main"

如果失败：
记录 exact blocker，
继续 module-level tests，
不要停整个任务。

跑上一轮的 23 个 post-fix contract assertions，
但不要为了让它们适配新实现而偷偷改期待结果。

分类：

FIXED
STILL_FAILING
STALE_TEST
NEW_FAILURE

==================================================
2. P0 — Canonicalization
==================================================

重点：

hard accessibility 不能降级

STEP_FREE_REQUIRED / AVOID_STAIRS：
model/API 发：
HARD
STRONG
SOFT
missing severity

检查 canonical result。

重复 code：
HARD + SOFT
STRONG + HARD
duplicate same

最终一个 code 只能一个 authoritative canonical row。

优先 strongest valid severity。

Negation/history：

不要全文 marker。

测试：

“wheelchair 必须 step-free，没有例外”
“I don't need a wheelchair, I can walk”
“我以前不用轮椅，但现在必须无障碍”
“朋友说我可能需要轮椅，但我不这么认为”
“不是地铁，我需要出租车因为行李很多”

要求 clause-local / entity-local semantics。

==================================================
3. P0 — Numeric / Time Boundaries
==================================================

Walking：

0
1
100
499
500
501
1000
10000
negative
huge
"500"
"500m"
null
missing
km form
m form
Chinese numerals if supported

Rest/Nap：

12:00-14:00
1pm-3pm
cross-midnight
outside Journey
overlap C4
invalid end before start
DST/timezone where relevant

要求：

malformed values early reject
valid values materially affect feasibility/schedule

不能所有值都同一个结果。

==================================================
4. P0 — Feasibility / Evidence
==================================================

检查 current gate 是否真正消费 capability。

Wheelchair HARD：

A verified step-free
B unknown
C conflict/stairs

目标：

verified:
can pass if other feasibility passes

unknown:
NEEDS_LIVE_EVIDENCE / review / fail-closed
but not “accessible”

conflict:
fail

检查：

initial plan
What-If
replan
recovery

必须共享逻辑。

==================================================
5. P0 — Mid-trip lifecycle
==================================================

ACTIVE Journey 中新增/修改 capability。

场景：

用户受伤
同行老人突然需要少走路
wheelchair requirement mid-trip

产品不能：

直接拒绝后让 Journey stranded，
也不能 silently mutate selected plan。

正确行为可以是：

capability recorded/pending
+
affected-plan analysis
+
recovery proposal / needs review

以当前产品合同为准，
但必须安全且可解释。

==================================================
6. P0 — Capability vs C4
==================================================

场景：

paid cruise C4
+
hard accessibility conflict

train C4
+
rest window

dinner C4
+
infant nap

系统不能：

删除 C4
忽略 hard capability

必须输出明确 conflict：

哪个 capability
哪个 commitment
什么 evidence
可选后续动作

==================================================
7. P1 — Raw-language hard-pair canary
==================================================

上一轮 494 已跑。

这轮不要追求数量。

选 120–180 条最高价值 raw text。

重点：

hard/soft
negation
historical
ambiguity
numeric
scope
mid-trip
conflict

真正经过：

raw text
-> DeepSeek
-> canonicalize
-> policy/gate

如果 provider busy：
最多重试两次，
然后 deterministic tests 继续。

记录 model 和 server 分歧。

==================================================
8. P1 — Scope / Audit
==================================================

验证：

JOURNEY
TRAVELER

“仅这次旅行”
“以后每次”
“这是永久情况”
“今天临时”

create/update/deactivate/delete

需要 audit/provenance。

下一 Journey 不得被 journey-only 需求污染。

Traveler scope 必须是明确确认后才持久化。

==================================================
9. P1 — Hermes
==================================================

如果当前 V19 已给 Hermes read-only capability：

验证：

inspect_journey / inspect_twin / capability context

包含：
capability
severity
scope
evidence

Hermes 不能：

改 HARD
把 unknown 说成 verified
绕过 evidence
删除 capability

如果当前仍无 read channel：
记录 P1 gap，
不要自己新造第二套 agent tool。

==================================================
10. P1 — Web/Mobile
==================================================

如果 Codex V19 frontend 已落地：

真实检查。

HARD / SOFT / UNKNOWN / CONFLICT / VERIFIED

不能只靠颜色。

测试：

390x844
430x932
1280x720
1440x900

long list
keyboard
focus
reduced motion
200% zoom

如果还未落地：
不要拿旧 fixture UI 假装验证 production。

==================================================
11. Snapshot B
==================================================

大约任务过半，
或确认 Codex发生一次明显更新后：

只读复制一次 Snapshot B。

只重跑：

- 23 contract assertions
- import
- 关键 P0 reproductions
- 新发现的 targeted tests

不要整个任务从头再来。

最终每项标：

FIXED_IN_CURRENT
STILL_REPRODUCIBLE
REGRESSED
NEW
INCONCLUSIVE

==================================================
12. Tests-only patch
==================================================

优先生成：

V19_1_TESTS_ONLY.patch

测试应针对 contract，
不要绑死内部函数名。

只有：

极小
低冲突
证据明确

才允许：

V19_1_LOW_CONFLICT_FIXES.patch

但不应用主树。

==================================================
13. 工作节奏
==================================================

0:00–0:30 Snapshot A + import + 23 tests
0:30–1:30 canonicalization / negation / dedupe
1:30–2:30 numeric/time + feasibility/evidence
2:30–3:30 mid-trip + C4 conflict
3:30–4:20 live hard-pair + scope/audit
4:20–5:00 Hermes/UI if available
5:00–5:30 Snapshot B targeted rerun
5:30–6:00 handoff + patches + package

如果提前完成：

增加：
race/concurrent capability updates
cross-city evidence
repeated recovery
malformed provider evidence
stale evidence
mobile long-list

不要重复老 corpus 凑时间。

==================================================
14. Stop
==================================================

完成 OUTPUT_CONTRACT.md。

Final:

D:\moodle\CityNexus-Tools\CityNexus-WorkBuddy-V19.1-ConvergenceRedTeam-20260915.zip

现在开始。
