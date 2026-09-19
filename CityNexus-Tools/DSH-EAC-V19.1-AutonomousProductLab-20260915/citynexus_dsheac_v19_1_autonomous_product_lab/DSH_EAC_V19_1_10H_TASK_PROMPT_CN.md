请执行 CityNexus DeepSeek Harness EAC V19.1 Autonomous Product Lab。

这是约 10 小时有效工程工作量的无人值守任务。

Codex 正在独占修改：

D:\moodle\CityNexus

绝对不要修改主工作区。

你的独立工作目录：

D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915

用户可能离开电脑。

依次阅读：

README_FIRST.md
AUTONOMY_CHARTER.md
KNOWN_MOVING_BASELINE_FINDINGS.md
SHADOW_INTEGRATION_CONTRACT.md
ACCESSIBILITY_EVIDENCE_PROVIDER_LAB.md
SELF_DIRECTED_BACKLOG.md
OUTPUT_CONTRACT.md

这次任务比上一轮重。

上一轮已经证明你能做漂亮且诚实的 capability reference UI。
这次不要再停留在 fixture demo。

==================================================
0. 先建立当前主线的只读快照
==================================================

只读检查当前 D:\moodle\CityNexus 一次。

复制到隔离 workspace。

不要边跑边依赖不断变化的主树。

建立：
- isolated backend
- isolated DB
- isolated frontend
- isolated cache

建议端口：
backend 8052
frontend 4202

如果主树在 Codex 运行期间继续变化，
任务后半段只允许再做一次定点 read-only delta check。

==================================================
1. P0 — 真实 Shadow Integration
==================================================

把上一轮 EAC 的 capability experience 真正对接到当前 V19 backend contract。

不要要求 backend 配合旧的 proposed API。

以当前实际接口为准。

建立：

LIVE_CAPABILITY_CONTRACT_MAP.md

至少映射：

- traveler capabilities
- journey capabilities
- capability update/confirmation
- capability plan impact
- recovery capability impact
- TravelerTwin capability/soft preference
- evidence/provenance
- scope
- audit

如果某个 live endpoint 不存在：

不要 silently fixture fallback。

明确：
CONTRACT_NOT_AVAILABLE

然后提供一个最小、低冲突 contract proposal 给 Codex。

==================================================
2. P0 — Live/Fixture/Offline 三态必须诚实
==================================================

实现或验证：

LIVE_SHADOW
RECORDED_FIXTURE
OFFLINE_STALE

任何状态切换都不能保留错误标签。

Live 断线：

保留已收到的 authoritative data
+
显示 stale timestamp
+
有限重试

不能：
拿 fixture 冒充 live。

Recorded fixture：
每个主要 surface 都有明显 source 标识。

==================================================
3. P0 — Accessibility Provider Evidence Lab
==================================================

这是本轮重任务之一。

研究 CityNexus 已有：
Nominatim
Overpass
MapLibre
provider/frozen evidence

建立保守的 accessibility evidence adapter/reference。

如果网络可用：
研究官方/权威 provider tagging documentation。

重点：

step-free
wheelchair
stairs
elevator
ramp
accessible toilet
entrance/path evidence

原则：

UNKNOWN != ACCESSIBLE

无 tag != yes

短路线 != step-free

现代建筑 != 有电梯

把实际 provider facts 映射成：

ACCESSIBILITY_VERIFIED
ACCESSIBILITY_UNVERIFIED
ACCESSIBILITY_CONFLICT
NEEDS_LIVE_EVIDENCE

每条 evidence 保留：

provider
raw key/tag
place/city identity
captured_at
provenance

如果 route-level evidence 当前做不到：
明确 NEEDS_LIVE_EVIDENCE，
不要造。

建立：

unit tests
frozen fixtures
Web/Mobile rendering
low-conflict patch/reference

==================================================
4. P1 — Capability-aware Web/Mobile Live UX
==================================================

上一轮的：

JourneySetupNeeds
CopilotNeedsConfirmation
CapabilityPlanExplanation
RecoveryDiffCapability
TwinCapabilitySummary
MobileCapabilityShield
CapabilityMapOverlay

尽可能在 shadow integration 中消费真实 V19 contract。

不要整体替换当前前端。

目标是：

真实 capability
+
真实 evidence
+
真实 scope
+
真实 confirmation

如果某条仍只能 fixture：
明确标记。

==================================================
5. P1 — Planner / Recovery Explainability
==================================================

前端必须能区分：

hard conflict
soft ranking
unknown evidence
provider unavailable
protected commitment conflict

做真实/影子场景：

wheelchair
elderly
infant
luggage
normal traveler

特别检查：

Recovery 后 capability 是否仍被保护。

不要只展示“符合/不符合”。

展示：
为什么
哪条 capability
哪条 evidence
哪一个活动/route
哪个 protected commitment 冲突

==================================================
6. P1 — Performance / PWA / Offline / A11y
==================================================

继续上一轮工程化：

- measure actual shadow bundle
- lazy MapLibre if useful
- no MapLibre/WebGL on non-map first paint
- offline/stale truth
- reconnect
- existing vite-plugin-pwa only
- no second service worker

A11y：

keyboard
focus
screen reader
aria-live restraint
200% zoom
320x720
390x844
430x932
1280x720
1440x900
reduced motion
touch target
long bilingual text

Capability/evidence 状态不能只靠颜色。

==================================================
7. P1 — Real user flow
==================================================

至少跑 8 个完整 shadow flows：

A 老人 + walking limit + midday rest
B wheelchair + verified place
C wheelchair + unknown place
D wheelchair + conflict place
E infant + nap + stroller
F large luggage
G normal soft preference
H conflicting family needs

流程至少：

setup
capability confirmation
plan
Copilot
What-If
recovery
mobile view

记录：
PASS
BLOCKED
NEEDS_EVIDENCE
BUG
CONTRACT_GAP

==================================================
8. P2 — Autonomous Product Work
==================================================

完成 mandatory work 后：

你自己找事做。

必须至少选择 3 个额外高价值任务。

按照 SELF_DIRECTED_BACKLOG.md：

evidence
→ rank
→ choose
→ implement
→ test
→ patch
→ merge recommendation

不要问用户选哪个。

不要花时间重复调颜色。

优先能明显改善真实用户体验或稳定性的东西。

==================================================
9. 允许研究，但不允许撒谎
==================================================

如果你搜索网络/文档：

把研究来源和当前实现分开。

不要因为文档说 provider 可能支持某 tag，
就声称当前 CityNexus 已经拥有该 evidence。

所有 product claims 必须来自当前实际数据。

==================================================
10. 合并工程
==================================================

不要一个 5000 行大 patch。

按 concern 拆分。

每个 patch：
- dependency
- apply-check
- merge risk
- current-tree conflict
- tests

主树只读。

==================================================
11. 工作节奏
==================================================

0:00–0:45
snapshot + current contract map

0:45–2:30
shadow live integration

2:30–4:30
accessibility provider evidence lab

4:30–6:00
Web/Mobile live capability integration

6:00–7:00
performance/PWA/offline/a11y

7:00–8:00
8 complete traveler flows

8:00–9:15
autonomous backlog: top 3–5 tasks

9:15–10:00
tests, patch split, reports, package

如果提前完成：
继续自己寻找高价值问题，最多扩展到 12 小时有效工作；
不要空等，不要重复同一测试凑时长。

==================================================
12. Stop
==================================================

最终完成 OUTPUT_CONTRACT.md。

Final:

D:\moodle\CityNexus-Tools\CityNexus-DSH-EAC-V19.1-AutonomousProductLab-20260915.zip

现在开始。
