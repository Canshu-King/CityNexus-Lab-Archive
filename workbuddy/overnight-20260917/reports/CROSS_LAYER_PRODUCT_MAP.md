# CROSS_LAYER_PRODUCT_MAP — 基线 v1（01:10，EAC 仍在修改中）

说明：EAC 正在实时重构，本图为 01:10 快照；每项能力标注「链路是否闭合」与疑点。

## 共同骨架

- 前端壳：`app/V8Experience.tsx`（71.9KB 单体，pushState 路由 `/v8/<route>`）
- 数据聚合入口：`GET /api/v1/journeys/{id}/experience`（V8Data：journey/options/mobility_facts/…）
- 权威方案真相：`useAuthoritativePlans`/`useAuthoritativeTwin`（TanStack Query ← `api/v12Authoritative.ts` ← generated client）
- 钱包：`GET /journeys/{id}/wallet`；离线：`GET /journeys/{id}/offline-snapshot` + Dexie 本地缓存
- 后端：FastAPI 单体 `backend/app/main.py`（385KB，9000+ 行），领域逻辑在 `services.py`/`stay_mobility.py`，
  真实城市数据 `integrations/discovery/real_city.py`，住宿 `integrations/stay_osm.py`
- 持久化：SQLite `backend/citynexus.db`（37.8MB）
- ⚠️ V8Experience 内部 `authoritativePlan` 显示时「回退到第一个 plan」，但 `hasChosenPlan` 单独判断
  ACTIVE/SELECTED —— 存在「未选择却显示某方案」的 UI 真相风险点（待 Phase 5 验证）

## 能力链路

### 1. 创建行程
UI: `features/setup/JourneyTrialSetup.tsx`(22KB) → POST `/travelers` → POST `/journeys` → POST `/journeys/{id}/stay-options/generate`
后端: main.py:1613/2230/2369；Journey(city_code/start/end/budget/stay_budget/party_size/arrival_anchor/departure_anchor)
⚠️ 仍有 `createTianjinDemo`（天津 demo）并存 —— 验收时需确认 same-Xiamen 不被天津数据污染。
疑点：Step 1/2/3 是否真实存在（任务书要求 3 步 + 确认页）。

### 2. 自然语言 AI 规划
UI: `features/planning/PlanWithAiSheet.tsx` → 生成走 POST `/journeys/{id}/plans/generate`（citynexus.ts:715）
后端: main.py:3862 → services 生成 3 候选；真实地点来自 real_city.py（provider evidence + snapshot_id 冻结）
疑点：AI intent 输入与进度 stepper 是否诚实（无伪百分比）。

### 3. 候选比较/选择
UI: `features/planning/PlanComparison.tsx`
后端: POST `/journeys/{id}/plans/{plan_id}/select`（main.py:3949）
链路状态：闭合。后端有 STALE_RECOMPOSE_REQUIRED(409) 冻结证据检查 + evaluate_feasibility 门(422) + 幂等重选。
⚠️ 意味着证据过期时 UI 可能弹错误 —— 需测 UI 如何呈现 409/422（Phase 6）。

### 4. 多日行程
UI: `features/trip/TripItinerary.tsx`(9.4KB) ← authoritativeTwin/plans
后端: GET `/journeys/{id}/twin`、`/plans`、`/multiday`
疑点：长行程 Day chips 是否周分组；酒店选择后 day 结构是否保持。

### 5. 活动详情
UI: `features/trip/ActivityDetail.tsx`(9.5KB，00:18 EAC 刚改过)
后端: twin 内 activity + Place 坐标（real_city）
疑点：known-free vs unknown price、"nearby" 空间证据、地图联动。

### 6. 酒店比较/选择
UI: `features/stay/HotelsPanel.tsx`(8.4KB) / StayExplorer.tsx
后端: POST `/journeys/{id}/stay-options/{option_id}/select`（main.py:2452）→ `materialize_stay_option`（stay_mobility.py，EAC 00:39 修改）
链路状态：闭合，带 deterministic gate + 失败 rollback + protected_commitments_preserved 字段。
疑点：gate 失败时 UI 是否展示冲突，还是静默重写。

### 7. 预订导入（consumer booking import）
UI: `features/inbox/JourneyInboxWorkbench.tsx`(19.7KB，00:51 刚改) + BookingArtifactScanner.tsx
后端: POST `/journeys/{id}/inbox/import`(2927) / `inbox/text-extract`(3010) / `inbox/vision`(3047) /
  PATCH `inbox/{draft_id}`(3093) / `inbox/{draft_id}/confirm`(3323) / `smart-apply`(3134)
链路状态：存在 draft→confirm 两段式（好迹象：先预览后确认）。
疑点：EAC 今晚正在改这个工作台 —— 是否已是消费者文案界面，还是仍要求 JSON。

### 8. 地图
UI: `components/v8/MapPanel.tsx` + `components/JourneyMap.tsx`
后端: Place 坐标 / offline-snapshot
疑点：无坐标时是否空状态而非天津兜底。

### 9. Copilot
UI: `features/agent/CopilotDock.tsx`(24.6KB) + AgentComposer.tsx
后端: POST `/journeys/{id}/copilot/messages`(main.py:8950)
疑点：回复是否暴露 REQUEST_PLACE_SEARCH/PlanVersion/C4/UNVERIFIED；是否有「加入行程/地图查看」等行动按钮。

### 10. Live/重规划
UI: `features/execution/LiveRecovery.tsx` + V10LiveExecutionPanel + V12AuthoritativeJourneyPanel
后端: POST `/journeys/{id}/replans`(创建) → POST `/replans/{id}/accept`(8307) / reject(8528)
后端 accept 处理器巨大（8307→8528 差 220 行），有 protected commitment 逻辑。
疑点：material diff；UI 是否把 Event/ReplanProposal/HARD 内部枚举直接抛给用户。

### 11. 失败恢复
UI: `features/recovery/RecoveryRequiredPanel.tsx` + V14RecoveryTruthPanel
后端: POST `/journeys/{id}/recovery/acknowledge`(2024)、resilience、guardian
疑点：后端离线时 Dexie 兜底是否告知「行程数据安全」。

## 初步红旗清单（待验证）

R1. `authoritativePlan` 显示回退到第一个 plan —— UI 可能展示用户从未选择的方案
R2. 天津 demo 与厦门验收并存 —— 城市污染风险
R3. select 409/422 错误的 UI 呈现未知
R4. inbox 工作台是否消费者化（EAC 正在改）
R5. Copilot 术语泄漏
R6. 单体壳 71.9KB + 主导航 five-tab 正确（mobileRoutes 已按设计规范改为 Today/Trips/Map/Copilot/Me）✓
