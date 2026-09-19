# BASELINE_STATE — 2026-09-17 01:00 (+08)

WorkBuddy 红队基线（只读采集，未触碰权威仓库）。

## 仓库状态

- 路径：`D:\moodle\CityNexus`（只读观察对象）
- 分支：`eac/v19.2.2-realphone-codegate`
- HEAD：`7d22cd0` — 2026-09-05 02:46 "feat(visio): establish CityNexus Visio model specification v1.0"
- 变更：112 项（1 M = `.gitignore`；111 untracked，绝大多数为历史发布 zip / staging 目录 / 报告，非今晚产物）

## EAC 实时活动（00:43–00:59）

今晚 EAC 正在修改（按 mtime）：

- 前端：`frontend/src/app/V8Experience.tsx`(71.9KB 单体)、`styles.css`(84KB)、
  `features/inbox/JourneyInboxWorkbench.tsx`、`i18n/LocaleContext.tsx`(62KB)、
  `features/trip/ActivityDetail.tsx`、`features/trip/TripItinerary.tsx`、`features/agent/AgentComposer.tsx`
- 前端构建：`frontend/dist/` 于 00:59 重建（PWA/service worker 存在）
- 后端：`backend/app/main.py`(385KB 单体)、`services.py`、`stay_mobility.py`(63KB)、
  `integrations/discovery/real_city.py`(46KB)、`integrations/stay_osm.py`、`integrations/provider_config.py`
- 测试：`backend/tests/test_snapshot_m_truth_edges.py`（00:43 新建，对应任务书 Phase 1 Snapshot M 真相缺口）、
  `test_snapshot_j_backend_truth_gaps.py`、`test_snapshot_k_stay_timeline.py` 更新

初步判断：EAC 正按任务书执行（先 Snapshot M 真相缺口，触及 stay/mobility/real_city —— 对应酒店选择保结构、
Activity Detail 坐标、已知免费等要求）。前端仍在 00:59 有活动，非纯后端逃逸模式（暂时）。

## 运行时

- 后端：端口 8000（python，pid 56296）
- 前端：端口 5173（vite dev，pid 30000）
- EAC 浏览器工具痕迹：`repo/.playwright-cli/`
- 红队规则：对 8000/5173 只做只读页面观察；敌意测试须用隔离副本（端口 8011/5181 + 独立 DB）。

## 产品结构（前端）

- 单页应用，主壳 `app/V8Experience.tsx`（71.9KB，单文件巨石）
- 路由表：`routes/v8Routes.ts`
- 关键 feature 模块：agent(AgentComposer/CopilotDock)、planning(PlanComparison/PlanWithAiSheet)、
  stay(HotelsPanel/StayExplorer)、trip(ActivityDetail/TripItinerary)、inbox(JourneyInboxWorkbench/BookingArtifactScanner)、
  execution(LiveRecovery/V10/V12 panels)、recovery(RecoveryRequiredPanel/V14)、setup(JourneyTrialSetup)、
  discovery(RealCityDiscoveryPanel)、mobility(MobilitySheet)、intelligence(ControlTowerPanel)、studio、traveler-twin
- i18n：`LocaleContext.tsx`（62KB，中英双语）
- API 层：`api/citynexus.ts` + `v10Execution.ts` + `v12Authoritative.ts` + `generated/api.ts`

## 现有证据库存（截至 01:00）

- 最新报告：`reports/product-v19-2-1/`（09-15 17:50，均为数行短文件）
- 最新截图：`output/playwright/`（09-15，v183-desktop/mobile 390/430 共 4+ 张）
- 今晚 EAC 尚未产出新的报告/截图（截至 01:00）
- 实拍手机"改前"照片 6 张：红队包 `reference/UIReference/.../evidence/real_phone_before/`（1000053119–125.jpg）
- 10 屏 UI 参考：`reference/UIReference/.../ui_reference/final_10/01..10.png`（Today/多日行程/创建1/创建2/AI输入/AI进度/方案比较/活动详情/酒店对比/Live重规划）
- 设计纠偏规范：`DESIGN_CORRECTIONS_REQUIRED.md`（主导航五项、厦门 demo 统一数据、Step3 必须存在、禁止伪百分比、
  预算诚实、禁内部术语、地图不许厦门变天津、Live 用户视图、禁会员卡）

## 已知开放阻塞（来自历史报告与状态文件）

- `CURRENT_STATUS.md`：V19.2.1 = "SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE"（真机验证未做）
- 真机/PWA/地理定位验证是独立 device gate
- 历史模式风险：后端测试绿但移动端产品体验差（任务书原话）——今晚红队重点即验证是否重演

## 红队工作区

`D:\moodle\CityNexus-WorkBuddy\overnight-20260917\`（baseline/checkpoint-01..04/lab/reports/screenshots/evidence）

## 基线待验证问题清单

1. Today/首页是否仍为工程控制台风（"STILL UP"/"PLANNING READY"类文案）？
2. 创建行程是否存在真实 Step 1/2/3？
3. Copilot 是否仍暴露 REQUEST_PLACE_SEARCH / PlanVersion / C4 / UNVERIFIED 等内部术语？
4. 地图对厦门 Journey 是否仍有天津兜底？
5. 酒店选择是否仍静默压缩活动时长/跨日合并？
6. booking 导入是否仍要求粘贴 raw JSON？
7. Live 重规划是否 material diff，还是新 UUID 换皮？
