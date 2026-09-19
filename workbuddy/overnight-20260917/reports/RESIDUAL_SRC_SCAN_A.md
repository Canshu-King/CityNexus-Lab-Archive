# CityNexus 消费者语言源码扫描 A（残留 R3/R4/R5 源码级复核）

- 审查对象：`D:\moodle\CityNexus-WorkBuddy\overnight-20260917\hotfix_pkg\CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917\source\frontend\src\`
- 扫描方式：只读静态源码审查，未运行服务/浏览器。
- 行号基于 hotfix 候选包内文件原文。
- "默认面"定义：消费者常规操作路径下不经折叠（<details>）即渲染的区域。

## 结论速览

| 项 | 结论 | 一句话依据 |
| --- | --- | --- |
| R3 预订审查默认面渲染内部枚举 | PARTIALLY_FIXED | 新增了 BOOKING_FIELDS/TYPE_LABELS/DECISION_LABELS 人话映射，但 artifact_type、draft.status、extraction_mode、anchor_role、payment_status、item.role 仍在默认面直接渲染；workbench 未被挪进 Advanced 折叠 |
| R4 Copilot 任务时间线原始 tool_name | PARTIALLY_FIXED | 新增 toolLabels 映射并用于步骤主标签，但 `event.tool_name ? <code>{event.tool_name}</code> : event.status` 原样保留在每步 detail 行，且该行在"高级详情"折叠之外 |
| R5 Trips 页泄漏内部活动角色键 | REPRODUCED | TripItinerary 默认卡片直接渲染 activity.type，ActivityDetail 直接渲染 meta.category，通知弹层直接渲染 disruption type；均无 check_out→退房 等映射 |

---

## R3 — JourneyInboxWorkbench 消费者路径

**结论：PARTIALLY_FIXED**

### 已修复的部分（新增映射 / humanize 函数）

文件：`features\inbox\JourneyInboxWorkbench.tsx`

| file:line | 内容 | 判定 |
| --- | --- | --- |
| JourneyInboxWorkbench.tsx:110-125 | `BOOKING_FIELDS`/`FIELD_LABELS`：confirmation_ref→订单号、scheduled_departure_at→出发时间 等字段名映射 | 新增，人话 |
| JourneyInboxWorkbench.tsx:127-135 | `TYPE_LABELS`：FLIGHT→航班、RAIL→火车、HOTEL→住宿 等 | 新增，人话 |
| JourneyInboxWorkbench.tsx:137-143 | `DECISION_LABELS`：AUTO_APPLY→"可以自动加入行程"、NEEDS_REVIEW→"需要你补充信息" 等 | 新增，人话 |
| JourneyInboxWorkbench.tsx:145-154 | `fieldLabel()` / `decisionLabel()` humanize 函数 | 新增 |
| JourneyInboxWorkbench.tsx:178-190 | `renderFact()`：对象取 name/location/title、枚举走 TYPE_LABELS、ISO 时间走 timeLabel | 新增 |
| JourneyInboxWorkbench.tsx:633-641 | 预订事实 dl 使用 `zh ? field.zh : field.en` + `renderFact(...)` | 默认面，已人话 |
| JourneyInboxWorkbench.tsx:642-650 | unresolved_fields 经 `fieldLabel()` 映射后展示 | 默认面，已人话 |
| JourneyInboxWorkbench.tsx:609-614 | 锚点角色下拉 option 用 `t("inbox.roleUnknown")` 等键 | 默认面，下拉已人话（但见下方 EN 文案残留） |

### 仍在默认面直接渲染内部枚举的位置（核心残留）

JourneyInboxWorkbench 的草稿审查区（`v10-inbox-draft`）与记忆面板（`v13-2-memory`）均不在任何 `<details>` 折叠内，属于默认消费者视图：

| file:line | 代码原文 | 判定 |
| --- | --- | --- |
| JourneyInboxWorkbench.tsx:596 | `<b>{draft.artifact_type} · {draft.status}</b>` | 默认面直接渲染原始 artifact_type（如 STRUCTURED_JSON）与 draft.status（如 CONFIRMED） |
| JourneyInboxWorkbench.tsx:597 | `<small>{draft.extraction_mode}</small>` | 默认面直接渲染原始 extraction_mode |
| JourneyInboxWorkbench.tsx:601 | `<span>{draft.interpretation?.anchor_role ?? "UNKNOWN"} · {confidence(draft.interpretation?.anchor_role_confidence)}</span>` | 默认面直接渲染原始 anchor_role / "UNKNOWN"，无映射函数 |
| JourneyInboxWorkbench.tsx:603 | `<span>{t("inbox.payment")} {String(draft.interpretation?.payment_status ?? "UNKNOWN")}</span>` | 默认面直接渲染原始 payment_status / "UNKNOWN" |
| JourneyInboxWorkbench.tsx:581 | `<strong>{item.title} · {item.role}</strong>` | 记忆面板默认面直接渲染原始 item.role（ARRIVAL/UNKNOWN 等），无映射 |
| JourneyInboxWorkbench.tsx:246 + 120 + 638 | `provider_key: "manual-entry"` 写入 payload；`provider_key` 在 BOOKING_FIELDS 中标签为"来源/Source"，值经 renderFact 原样显示 | 默认面预订事实列表会把 "manual-entry" 当作"来源"值显示 |
| JourneyInboxWorkbench.tsx:148 | `return key.replaceAll("_", " ");` | fieldLabel 对未收录字段名的兜底仍是内部字段名（仅把下划线换空格） |

### Advanced 折叠容器检查

V8Experience.tsx:1215-1231（Trips > bookings 页签）：

```tsx
1217  //              review the parsed fields, then confirm.  The raw-JSON workbench is
1218  //              kept for developers behind an Advanced disclosure. */}
1218          <JourneyInboxWorkbench
1219            journeyId={data.journey.id}
1220            onConfirmed={onRefresh}
1221          />
1222          <details className="trips-advanced">
1223            <summary>{zh ? "高级 / 开发者" : "Advanced / developer"}</summary>
1224            <Bookings
...
1231          </details>
```

判定：**注释声称 raw-JSON workbench 已挪入 Advanced 折叠，但代码事实相反**——`<details className="trips-advanced">` 内放的是 `<Bookings>`，`<JourneyInboxWorkbench>` 在折叠之外，属于默认面。另在 route==="bookings"（V8Experience.tsx:1024-1030）也默认挂载同一组件。组件内部亦无任何"高级/开发者"折叠把 596/597/601/603/581 这些枚举渲染挪进去。

### i18n 文案残留

- LocaleContext.tsx:493-496（EN）："UNKNOWN · review required" / "ARRIVAL · Journey start" / "MID_TRIP · protected activity" / "DEPARTURE · Journey end" —— 下拉 option 的英文文案本身仍内嵌原始枚举；zh 版（1115-1118："未知 · 需要审核" 等）已人话。

**R3 判定：PARTIALLY_FIXED** —— 字段名/类型/决策三类已人话，但 artifact_type、draft.status、extraction_mode、anchor_role、payment_status、item.role 六类枚举仍在默认面原样渲染，且未按注释挪入 Advanced 折叠。

---

## R4 — NativeMissionTimeline 工具名

**结论：PARTIALLY_FIXED**

组件位置：`features\agent\CopilotDock.tsx` 内的 `NativeMissionTimeline`（CopilotDock.tsx:150）。

### 挂载路径（什么条件触发 mission timeline）

- V8Experience.tsx:1058：`<CopilotDock data={data} onNavigate={navigate} />` —— 全局常驻 Dock（默认面）。
- CopilotDock.tsx:626-633：打开 Dock 后，只要最近一条消息带 `agent_run`（`latestNativeRun`）即渲染 `<NativeMissionTimeline ...>`，无 Advanced 门控。

```tsx
626          {latestNativeRun && (
627            <NativeMissionTimeline
628              data={data}
629              run={latestNativeRun}
630              onNavigate={onNavigate}
631              onExecutionChange={setExecuted}
632            />
633          )}
```

### 新增的映射（已修复部分）

| file:line | 内容 | 判定 |
| --- | --- | --- |
| CopilotDock.tsx:47-59 | `toolLabels` 映射表：inspect_journey→"检查当前行程"、create_booking→"创建预订" 等 11 个工具 | 新增 |
| CopilotDock.tsx:134-139 | `summaryText()`：步骤主标签优先 `toolLabels[event.tool_name]`，否则 lifecycleLabels / `event.friendly_label` | 新增，主标签已人话 |
| CopilotDock.tsx:389 | Advanced 折叠内 current tool 也走 `toolLabels[currentTool] ?? currentTool` | 折叠内，可接受 |
| CopilotDock.tsx:306-315 | 原始 JSON（含 tool_name）在 `<details className="cn-agent-raw"><summary>运行详情</summary>` 折叠内 | 折叠内，可接受 |

### 残留：默认面仍渲染原始 tool_name

CopilotDock.tsx:291-319（steps 构造）：

```tsx
291  const steps = useMemo<AgentRailStep[]>(() => events.map((event, index) => {
292    const detail: ReactNode = (
293      <span className="cn-agent-event-detail">
294        {event.tool_name ? <code>{event.tool_name}</code> : event.status}
295        {event.duration_ms != null && ` · ${formatDuration(Number(event.duration_ms))}`}
296        {""}
297      </span>
298    );
```

该 detail 随 `<AgentRunRail steps={steps} />`（CopilotDock.tsx:375-376）渲染，而 AgentRunRail 默认展开每一步的 detail：

AgentRunRail.tsx:16-19：

```tsx
16          <div>
17            <b>{step.label}</b>
18            {step.detail && <small>{step.detail}</small>}
19          </div>
```

判定：
- 原文 `event.tool_name ? <code>{event.tool_name}</code> : event.status` **仍在，且在"高级详情"折叠之外**（折叠是 CopilotDock.tsx:383-393 的 `<details className="cn-native-plan">`，只覆盖 run_id/mission_id/steps/current/duration/execution）。
- 只要事件带 tool_name（tool.started/completed/failed 等），无论是否命中 toolLabels，detail 行都以 `<code>` 原样展示内部工具名；未收录的新工具同样裸露。
- 注意：`event.status` 兜底路径（approval_required / completed 等英文枚举）同样未人话。

**R4 判定：PARTIALLY_FIXED** —— 主标签与折叠内字段已映射，但默认时间线每步 detail 行的原始 tool_name/status 渲染原样保留。

---

## R5 — Trips/ActivityDetail 角色键

**结论：REPRODUCED**

`check_out / departure / museum` 等值由后端数据（activities[].type、metadata.category、disruptions[].type、memory items[].role）传入，前端源码中不存在任何 `check_out→退房`、`departure→出发`、`museum→博物馆` 的本地化映射（全源码 grep `museum|check_out` 仅命中 stories 假数据 `activity_type: "check_in"`，V12ExecutionStates.stories.tsx:34；LocaleContext 的 values 中无活动类型键文案）。

### 直接渲染原始键的位置

| file:line | 代码原文 | 位置/判定 |
| --- | --- | --- |
| TripItinerary.tsx:232-234 | `{activity.type && activity.type !== "visit" && (<span className="trip-stop-type">{activity.type}</span>)}` | Trips 默认逐日行程卡片，直接渲染 activity.type 原始键（check_out/departure/museum 等将原样显示），无任何映射 |
| ActivityDetail.tsx:208-213 | `{meta.category && (<div><dt>{zh ? "类型" : "Category"}</dt><dd>{meta.category}</dd></div>)}` | 活动详情默认面，直接渲染 meta.category 原始值 |
| V8Experience.tsx:874-878 | `<b>{item.severity}</b><span>{item.type.replaceAll("_", " ").toLowerCase()}</span>` | 顶栏通知弹层（所有路由默认可见），disruption type 仅做下划线替换+小写（"check_out"→"check out"），无中文翻译 |
| V8Experience.tsx:2201 | `{zh ? bookingTypeLabel(item.type) : item.type} ·{" "}` | Bookings 卡片：zh 有映射（bookingTypeLabel，V8Experience.tsx:2102-2105，未命中时兜底 `key.replaceAll("_", " ").toLowerCase()` 仍露内部键），en 完全裸露；但该组件整体位于 trips-advanced 折叠内（V8Experience.tsx:1222-1231），Advanced 之后 |

### 对比：已有映射但未覆盖此处

- V8Experience.tsx:2102-2105 `bookingTypeLabel`（BOOKING_TYPES）只用于（折叠内的）预订卡，且不覆盖 activity.type。
- JourneyInboxWorkbench 的 TYPE_LABELS（R3 节）同为预订类型，不覆盖活动类型。
- LocaleContext 中与活动类型相关的键只有 `hub.departure`（"出发"）这类固定标签（LocaleContext.tsx:739），不是对数据值的映射。

**R5 判定：REPRODUCED** —— 默认 Trips 行程卡、活动详情、通知弹层仍直接渲染内部角色/类型键，无本地化映射；唯一改善是 Advanced 折叠内的 Bookings 中文路径新增了 bookingTypeLabel。

---

## 附：检查过的其他相关文件（无新增发现）

- features\agent\AgentComposer.tsx：message item.role 仅用于 key/className/角色名（190-194），语义细节在 `<details className="v15-copilot-semantic">` 折叠内（248-259）；UNKNOWN 处理为映射到 i18n 键（23、36）。未见默认面枚举泄漏。
- features\trip\TripItinerary.tsx 其余部分（时长/受保护/受影响/当前徽标）均为人话文案。
- ActivityDetail 其余字段（费用 cost_status 三态、营业时间）均已人话。
