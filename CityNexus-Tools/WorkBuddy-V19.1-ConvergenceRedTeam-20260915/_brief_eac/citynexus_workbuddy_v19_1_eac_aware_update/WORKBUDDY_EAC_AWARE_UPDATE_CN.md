更新当前 WorkBuddy V19.1 Convergence Red-Team 任务。

EAC V19.1 AutonomousProductLab 已经完成。

不要重新做 EAC 的完整 shadow lab。

继续以 FINAL V19 冻结快照为主要测试目标，
但把 EAC package 作为 candidate implementation/reference input。

新增重点：

==================================================
1. EAC patch 验证
==================================================

不要相信 EAC 报告里“已修复”三个字。

专门验证：

HARD downgrade
duplicate merge
numeric parsing
negation/history
OSM evidence
feasibility bridge
live/fixture/offline source truth

独立 review 已经发现：

EAC non-main capability patch 仍然会把：

I don't need a wheelchair, I can walk

错误识别成 HARD STEP_FREE_REQUIRED。

以及：

朋友说我可能需要轮椅，但我不这么认为

仍会误报 HARD。

请把这些加入 tests-only patch。

==================================================
2. Provider evidence scope attack
==================================================

必须测试：

仅：
toilets:wheelchair=yes

不能满足：
STEP_FREE_REQUIRED。

仅：
ramp=yes

不能满足 step-free。

仅：
elevator=yes

不能证明 route accessible。

wheelchair=yes + step_count=5
必须 conflict。

list/tuple tag forms 不得被静默当空。

route-level step-free 没有真实证据时必须 unknown。

重点看：

generic overall_state
是否错误跨 subject/code 传播证据。

==================================================
3. Confirm semantics
==================================================

继续确认：

confirm A
confirm B
A 不得消失。

加：

concurrent confirm A/B
duplicate confirm
cross-scope same code
traveler + journey same code

==================================================
4. EAC autonomous endpoint review
==================================================

Audit endpoint：
验证事件完整性和 scope。

Catalog：
验证 canonical defaults 不与真正 server rules 漂移。

Extract endpoint：
如果使用 local fallback，
必须标 candidate-only，
并测试 false HARD。

如果 Codex 后续改成 DeepSeek-first：
验证 model -> canonicalize -> confirm boundary。

==================================================
5. OpenAPI drift
==================================================

EAC 发现 runtime 134 paths，checked-in 124 paths，
且 prefix/schema 漂移。

加入自动 contract check：

runtime OpenAPI
vs checked-in OpenAPI

能力/accessibility 路由不能只活在 runtime。

==================================================
6. 不重复大扫荡
==================================================

不要重跑上一轮 494 cases 全集。

选择 150–220 条高价值 raw-language case：

hard/soft
negation
rumour
history/current contrast
scope
numeric
confirm
evidence

优先能区分 FINAL V19、EAC patch、Codex V19.1 的 case。

==================================================
7. 最终 handoff
==================================================

每个 finding 标：

FINAL_V19
EAC_REFERENCE
CODEX_V19_1_IF_AVAILABLE

如果 Codex V19.1 在你任务后半段完成：
只做一次最终 read-only targeted delta check，
不要整轮重来。

输出继续使用原任务合同，
再额外生成：

EAC_PATCH_VALIDATION.md
ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md
OPENAPI_DRIFT_RESULTS.md

不要修改主树。

现在继续。
