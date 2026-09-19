# CityNexus DeepSeek Harness EAC V19.1 Autonomous Product Lab — 10H

This is a heavy autonomous engineering task.

Authoritative main worktree:

`D:\moodle\CityNexus`

Harness EAC MUST NOT modify that worktree.

Isolated workspace:

`D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915`

The previous EAC V19 CapabilityExperience package was useful and clean:
- 7/7 Playwright passed;
- 0 axe violations in the reference lab;
- all four additive patches passed `git apply --check`;
- it correctly kept `UNKNOWN != ACCESSIBLE`;
- it did not pretend local UI state was planner authority.

But it remained mostly a reference UX because the V19 backend contract was moving during the run.

This task moves beyond a fixture lab.

Primary goals:

1. shadow-integrate the latest V19 capability backend in an isolated clone;
2. build a real capability evidence/provider reference path using existing CityNexus provider architecture;
3. make Web/Mobile consume live capability contracts when available;
4. harden performance/PWA/offline/accessibility;
5. autonomously identify and implement additional high-value product improvements after mandatory work is complete.

Read:

1. `AUTONOMY_CHARTER.md`
2. `KNOWN_MOVING_BASELINE_FINDINGS.md`
3. `SHADOW_INTEGRATION_CONTRACT.md`
4. `ACCESSIBILITY_EVIDENCE_PROVIDER_LAB.md`
5. `SELF_DIRECTED_BACKLOG.md`
6. `OUTPUT_CONTRACT.md`
7. `DSH_EAC_V19_1_10H_TASK_PROMPT_CN.md`
