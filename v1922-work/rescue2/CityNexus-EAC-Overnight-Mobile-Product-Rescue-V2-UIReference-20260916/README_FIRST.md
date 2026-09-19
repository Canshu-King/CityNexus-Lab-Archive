# CityNexus EAC Overnight Mobile Product Rescue V2

这是一份面向 EAC 的 **完整通宵产品重构包**。

目标不是“把现有前端换个皮肤”，而是让 CityNexus 变成一个普通旅行者真正知道怎么用的移动产品。

## 今晚的核心判断

后端已经有大量真实能力：

- Journey
- PlanVersion
- Provider truth
- Capability / HARD constraints
- C4 commitments
- Booking simulation
- Mobility
- DeepSeek semantics
- Hermes / agent execution
- Recovery / ReplanProposal
- Twin / live state

但第一次真实 Xiaomi 13 Ultra 使用证明：

> 这些能力没有被组织成一个正常人的产品流程。

因此 V2 通宵任务把 **真实手机使用证据 + 10 张重新设计的产品 UI + 当前后端 truth hotfix** 放进同一个包。

## EAC 执行顺序

1. 阅读 `docs/EAC_OVERNIGHT_MASTER_MISSION.md`
2. 阅读 `docs/DESIGN_CORRECTIONS_REQUIRED.md`
3. 阅读 `docs/PRODUCT_FLOW_SPEC.md`
4. 查看 `evidence/real_phone_before/`
5. 查看 `ui_reference/final_10/`
6. 完成 `reference/backend_truth/` 中的 V19.2.5 窄 hotfix
7. 再进行整晚 Mobile Product Rescue
8. 按 `docs/MORNING_ACCEPTANCE_GATE.md` 自己扮演真实用户验收

## 重要

这 10 张图片是 **产品设计方向和信息架构参考**，不是要求逐像素机械复刻。

图片生成中仍存在少量演示数据不一致，已经在
`docs/DESIGN_CORRECTIONS_REQUIRED.md`
中明确修正。

EAC 必须以修正规则为准，不得把图片里的矛盾忠实实现进代码。
