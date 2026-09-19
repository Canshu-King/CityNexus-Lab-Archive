请执行 CityNexus DeepSeek Harness EAC V19 Capability Experience Lab。

这是约 6 小时有效工程工作量的独立前端/体验任务。

Codex 正在独占修改：

D:\moodle\CityNexus

绝对不要修改主工作区。

主树只读参考。

工作目录：

D:\moodle\CityNexus-Tools\DSH-EAC-V19-CapabilityExperience-20260915

先阅读：

README_FIRST.md
NO_USER_DECISION_POLICY.md
EXPERIENCE_CONTRACT.md

==================================================
1. 主任务
==================================================

为 V19 Traveler Capability + Accessibility Intelligence 做一套可被 Codex
低冲突吸收的 Web + Mobile 体验工程包。

不要把它做成“设置里多几个 checkbox”。

目标是让普通旅行者理解：

- 系统知道我的哪些真实出行需求；
- 哪些是必须满足；
- 哪些只是偏好；
- 哪些地点/路线有证据；
- 哪些无障碍信息未知；
- 为什么某个方案被排除；
- Recovery 是否仍保护我的需求。

==================================================
2. Journey Setup UX
==================================================

设计可选：

“Traveler needs / 出行需求”

默认简洁。

Quick chips：

少走路
无障碍/轮椅
避免楼梯
婴儿车
大件行李
中午休息
婴儿午睡

Advanced：

max walking per leg
max continuous walking
rest frequency
nap window
toilet/rest frequency
pace
quiet/sensory

不能像医院病历表。

设计：
desktop
390x844
430x932

==================================================
3. Copilot Detected Needs
==================================================

用户输入：

“我妈膝盖不好，不能走太多，中午最好休息。”

设计一个 Copilot confirmation card：

Detected:
- Low walking
- Midday rest

Class:
HARD / STRONG / SOFT

Scope:
This Journey
Future Journeys

Source:
You told CityNexus

Actions:
Confirm
Edit
Use only this Journey
Dismiss

HARD 需求不允许悄悄持久化。

设计 ambiguity 状态。

==================================================
4. Evidence UX
==================================================

重点设计：

Verified
Unverified
Conflict
Needs live evidence

例：

♿ Step-free requirement

Tianjin Museum:
Verified step-free evidence

Candidate B:
Accessibility not verified

Candidate C:
Known stairs conflict

不要用绿色勾号表示 unknown。

==================================================
5. Plan / Recovery Explainability
==================================================

设计 capability-aware Plan card：

Why selected:
- walking leg 320m < 500m limit
- indoor
- rest window preserved

Rejected:
- route walking 780m exceeds hard limit

Unknown:
- step-free evidence unavailable

Recovery Diff：

BEFORE
AFTER
Capabilities preserved
Capabilities at risk
Evidence gaps

C4 commitments 继续单独显示。

==================================================
6. Traveler Twin / Profile
==================================================

重设计 Twin 能力摘要：

Explicit capability
Explicit preference
Learned soft preference

HARD 无障碍需要：

不要 confidence 0.42 进度条。

显示：

Explicit
Traveler stated
Active
Scope

Learned soft preferences 才允许 strength/confidence。

==================================================
7. Mobile
==================================================

Today 首页如果存在 HARD need：

显示紧凑 Capability Shield：

“2 travel needs protected”

如果当前 next activity 存在 evidence gap：

显示：

“Step-free access not verified”

不是红色恐慌墙，
但主操作必须可见。

Mobile Copilot：
Detected needs confirmation 用 bottom sheet。

Map：
accessible/unknown/conflict marker 视觉区别。

==================================================
8. Map / Visual Language
==================================================

设计：

verified accessibility marker
unknown accessibility marker
conflict marker
rest stop marker
nap/rest window
walking limit warning

不要把 map 变成无障碍图标圣诞树。

Reduced motion 仍有效。

==================================================
9. Adapter / Contract
==================================================

不要直接绑定 fixture。

建立 capability UI adapter/types：

TravelerCapability
CapabilityEvidence
CapabilityConflict
CapabilityImpact
CapabilityConfirmation

如果 Codex 当前 API 未完成：
使用 adapter + recorded fixture，
明确 RECORDED_FIXTURE。

当 API 存在时：
Live adapter 从真实接口映射。

未知 future fields 不得崩。

==================================================
10. Accessibility of Accessibility UI
==================================================

讽刺地说，做无障碍页面本身也得能无障碍。

必须测试：

keyboard
focus
screen reader label
aria-live restraint
200% zoom
320px
390x844
430x932
1280x720
1440x900
reduced motion
touch targets
long Chinese / English

不要只靠颜色区分：
verified / unknown / conflict。

==================================================
11. Traveler scenarios
==================================================

做至少 5 个可重复 reference scenarios：

A 老人
B 轮椅
C 婴儿家庭
D 大件行李
E 普通 soft preference

每个都有：

setup
Copilot
plan explanation
recovery state
mobile state

==================================================
12. Merge Engineering
==================================================

最终拆成低冲突 patch：

01_CAPABILITY_TYPES_ADAPTER.patch
02_SETUP_AND_CONFIRMATION_UI.patch
03_PLAN_RECOVERY_CAPABILITY_UI.patch
04_TWIN_MOBILE_MAP_OPTIONAL.patch

不要整体替换 router/main.tsx/LocaleProvider。

明确：

可以直接合
需要等待 backend contract
仅 reference
不要合

==================================================
13. Testing
==================================================

TypeScript/typecheck
production build
focused component tests
Playwright

覆盖：

desktop
mobile
keyboard
long text
unknown evidence
hard conflict
no capability
recorded/live source honesty

==================================================
14. 任务节奏
==================================================

0:00-0:35
只读主树/API + types

0:35-2:00
Setup + Detected Needs + capability types

2:00-3:20
Plan/Recovery/Twin evidence UX

3:20-4:20
Mobile/Map

4:20-5:10
A11y + bilingual + reduced motion

5:10-6:00
Playwright + patch split + reports + package

如果提前完成：
- 200% zoom
- 320px
- unknown evidence stress
- very long capability list
- offline/stale
- approval/confirmation errors

==================================================
15. Deliverables
==================================================

DSH_EAC_V19_CAPABILITY_EXPERIENCE_REPORT.md
CAPABILITY_UI_CONTRACT.md
ACCESSIBILITY_EVIDENCE_UX.md
MOBILE_CAPABILITY_UX.md
A11Y_VALIDATION.md
CODEX_MERGE_GUIDE_V19.md

reference-app/
tests/
evidence/screenshots/
evidence/build_results.txt

patches/
01_CAPABILITY_TYPES_ADAPTER.patch
02_SETUP_AND_CONFIRMATION_UI.patch
03_PLAN_RECOVERY_CAPABILITY_UI.patch
04_TWIN_MOBILE_MAP_OPTIONAL.patch

Final:

D:\moodle\CityNexus-Tools\CityNexus-DSH-EAC-V19-CapabilityExperience-20260915.zip

现在开始。
