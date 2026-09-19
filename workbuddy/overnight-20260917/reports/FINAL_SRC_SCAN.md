# FINAL_SRC_SCAN — CityNexus EAC 最终候选包源码级红队核查

- 审计对象: overnight-20260917/eac_final_pkg/CityNexus-EAC-Overnight-Continuation-Final-20260917/source/
- 审计方式: 只读源码审计（无运行、无浏览器）
- 入口确认: main.tsx:1651-1661 — 默认渲染 V8Experience，仅 /legacy 前缀进入 LegacyApp。以下所有判断基于默认用户路径。
- 日期: 2026-09-17

结论速览:

| 项 | 结论 |
|---|---|
| F2 Copilot 工程词汇泄漏 | PARTIALLY_FIXED |
| F3 Me 页策略内部暴露 | REPRODUCED |
| F5 预订导入 JSON 主路径 | PARTIALLY_FIXED |
| F6 活动价格三态 | REPRODUCED |
| F7 方案比较部分价格假置信 | PARTIALLY_FIXED |
| F9 路由解析健壮性 | REPRODUCED |
| F12 包可回放性 | PARTIALLY_FIXED |

路径缩写: SRC = source/frontend/src，BE = source/backend。

---

## F2 — Copilot 工程词汇泄漏：PARTIALLY_FIXED

### 已修复部分
CopilotDock.tsx 主气泡现在全部经过映射函数：
- humanIntent / humanVerification / humanAction（CopilotDock.tsx:502-515），枚举表 INTENT_LABELS / VERIFICATION_LABELS / ACTION_LABELS（CopilotDock.tsx:467-494，含 DISCOVER→查找地点、UNVERIFIED→未核验、REQUEST_PLACE_SEARCH→搜索更多地点）。渲染点：CopilotDock.tsx:608-622。466 行注释声明 "must never reach the traveller as raw SCREAMING_CASE strings"。
- AgentComposer.tsx:14-23 intent 全枚举映射到 i18n 键，渲染点 AgentComposer.tsx:185；未命中走 agent.intentUnknown。
- DeepSeek provider 名不再渲染：AgentComposer.tsx:220 仅作条件判断，输出为 agent.aiInterpreted（"Understood by the AI assistant" / "由 AI 助手理解"）。RealCityDiscoveryPanel.tsx:113 的 "DeepSeek discovery failed" 也只用于匹配后端错误再转译为 discovery.aiUnavailable。
- V8Experience.tsx:2216-2227 modeLabel 对 WALK/RIDE_HAIL 等做映射。

### 值级泄漏残留（用户可见文案）
| 位置 | 内容 | 泄漏词 | 是否折叠 |
|---|---|---|---|
| SRC/features/agent/CopilotDock.tsx:49 | inspect_twin: { en: "Inspect JourneyTwin", zh: "检查 JourneyTwin" } | JourneyTwin | 否（默认时间线 label） |
| SRC/features/agent/CopilotDock.tsx:52 | request_replan: { en: "Request deterministic replan", zh: "请求确定性重规划" } | deterministic | 否 |
| SRC/features/agent/CopilotDock.tsx:296 | {event.policy_decision ? ` · ${event.policy_decision}` : ""} — 后端 policy_decision 原始字符串直接渲染，无映射 | policy enum | 否 |
| SRC/features/agent/CopilotDock.tsx:449-461 | localizePlanStep 未命中映射时回退英文 operation 原文（含 "Request a deterministic replan proposal"） | deterministic | 否 |
| SRC/features/agent/CopilotDock.tsx:306-315 | cn-agent-raw details 渲染 event_type/source/tool_name/result_summary/policy_decision 原始 JSON | 内部事件 | 是（"运行详情"折叠） |
| SRC/features/agent/AgentComposer.tsx:207-208 | <b>{item.response.what_if.feasibility}</b> — 后端 feasibility 枚举值原文渲染 | feasibility | 否 |
| SRC/features/agent/AgentComposer.tsx:231-243 | semantic_envelope.assertion_status / effective_time / event_type / requested_action 原文渲染 | Semantic 枚举 | 是（"高级详情" details） |
| SRC/i18n/LocaleContext.tsx:366 (en) / :988 (zh) | "discovery.authoritativeSub": "...same JourneyTwin, map...as every other PlanVersion" / "…与所有其他 PlanVersion 一样，可用于 JourneyTwin…" | PlanVersion、JourneyTwin | 否 |
| SRC/i18n/LocaleContext.tsx:337 | "discovery.detGate": "Deterministic gate"（RealCityDiscoveryPanel.tsx:158 渲染） | Deterministic | 否 |
| SRC/i18n/LocaleContext.tsx:353 | "discovery.planversion": "PLANVERSION"（RealCityDiscoveryPanel.tsx:165 渲染为字段标签） | PlanVersion | 否 |
| SRC/i18n/LocaleContext.tsx:511,517,518 | "intel.lede" 含 "DeepSeek"；"intel.deepseek": "DeepSeek"（RealCityDiscoveryPanel.tsx:154 渲染 result.intent.provider 原文；:158 渲染 intel.deepseek）、"intel.hermes": "Hermes" | DeepSeek、Hermes | 否 |
| SRC/i18n/LocaleContext.tsx:522-523 | "intel.policy": "POLICY"、"intel.advisory": "ADVISORY"（Intelligence 页） | 内部枚举 | 否 |
| SRC/main.tsx:946,967,989-990,1386,1514-1515,1556 等 | LegacyApp 大量 "deterministic journey mode" / "DeepSeek interprets..." / "TravelerTwin Control Tower" / "Feasibility envelope" | 多项 | 是（仅 /legacy 可达，默认入口不渲染） |

映射覆盖确认：humanIntent 等 fallback 是"问题/核验状态未知/继续"，不是透传原枚举——CopilotDock 气泡层面枚举全覆盖；但时间线 label（toolLabels 覆盖全部 11 个 tool，后端新增 tool 名则回退 event.friendly_label，CopilotDock.tsx:134-139）与 localizePlanStep 的 fallback 仍可能透传英文原文。

结论: PARTIALLY_FIXED — 气泡层修复扎实；工具时间线、policy_decision、feasibility、discovery 链路文案与 i18n 值仍有值级泄漏。

---

## F3 — Me 页策略内部暴露：REPRODUCED

Me 页组件：SRC/app/V8Experience.tsx:2138-2203（默认路由 /v8/me 直接渲染，无 Advanced/Developer 折叠）。

| 位置 | 代码原文 | 问题 |
|---|---|---|
| V8Experience.tsx:2161 | <strong>{policy?.mode ?? "ADVISORY"}</strong> | 英文内部枚举 ADVISORY/ASSISTED/AUTONOMOUS 直接渲染在默认 Me 卡片，无映射 |
| V8Experience.tsx:2196 | {data.journey.city_code} | 城市以代码 CN-XIAMEN 显示。Me 页未使用 cityFromCode（181-192 行）或 CITY_NAME_BY_SLUG（2229-2241 行，Hub 页 1286 行已用其显示"厦门"） |
| SRC/i18n/LocaleContext.tsx:848 (zh) | "me.kicker": "我的 · 权限边界" | "权限边界"（内部策略术语）渲染在 Me 页默认 kicker（V8Experience.tsx:2153 {t("me.kicker")}）；en 版 :226 为 "Me · authority envelope" |

补充：Delegation 不在 Me 页，出现在 SRC/i18n/LocaleContext.tsx:215（en bookings.authoritySub 含 "Delegation Policy"；zh 版 :837 已译作"委托策略"）与 SRC/features/recovery/V14RecoveryTruthPanel.tsx:140（"Delegation policy"，Recovery 页）。

结论: REPRODUCED — 三项全部原样存在：ADVISORY 枚举直出、城市代码 CN-XIAMEN 直出、"权限边界" kicker 直出，均在默认 Me 页且不在折叠区。

---

## F5 — 钱包/预订次要路由仍 JSON 优先：PARTIALLY_FIXED

### 已修复部分
1. Trips 页预订 tab 主入口改为多模态收件箱（V8Experience.tsx:1185-1204）：
```
{/* Consumer flow first: paste a confirmation or enter it manually,
    review the parsed fields, then confirm.  The raw-JSON workbench is
    kept for developers behind an Advanced disclosure. */}
<JourneyInboxWorkbench journeyId={data.journey.id} onConfirmed={onRefresh} />
<details className="trips-advanced">
  <summary>{zh ? "高级 / 开发者" : "Advanced / developer"}</summary>
  <Bookings ... onImport={onImport} busy={busy} />
</details>
```
2. JourneyInboxWorkbench.tsx 主路径：文本粘贴 → /inbox/text-extract（297-313 行）、图片 → /inbox/vision（319-334 行）、手动表单（205-265 行 submitManual）、扫码解码 BookingArtifactScanner 注入 decodedText（315-317 行）。字段/枚举有 BOOKING_FIELDS / TYPE_LABELS / DECISION_LABELS 完整映射（110-154 行），导入走 preview → confirm 两步。
3. importReservation（V8Experience.tsx:606-634）以 artifact_type: "STRUCTURED_JSON" 提交 /inbox/import，不再是裸 JSON 文本协议。

### 残留问题
1. /v8/bookings 路由（V8Experience.tsx:984-1004）顶层直接渲染 Bookings 组件（不在任何 Advanced 折叠内），其 JSON textarea 仍暴露（V8Experience.tsx:2067-2073）：
```
<label htmlFor="reservation-json">{t("bookings.reservationJson")}</label>
<textarea id="reservation-json" value={input} ... placeholder={'{"reservation_type":"RAIL", "confirmation_ref":"…"}'} />
```
2. JSON.parse 无 try/catch（V8Experience.tsx:2000-2004）：
```
const submit = async () => {
  const value = JSON.parse(input) as Record<string, unknown>;   // 2001 行：非法 JSON 直接抛 SyntaxError
  await onImport(value);
  setInput("");
};
```
调用点 onClick={() => void submit()}（2077 行）— 解析失败成为未处理的 promise rejection，无用户可见错误提示（i18n 值 bookings.lede，LocaleContext.tsx:201，仍写着 "Paste structured reservation JSON"）。

结论: PARTIALLY_FIXED — 消费者主路径已切换为多模态收件箱 + 手动表单；但 /v8/bookings 次要路由顶层仍保留无 try/catch 的裸 JSON textarea，且未标注 Advanced。

---

## F6 — 活动详情价格三态：REPRODUCED

组件：SRC/features/trip/ActivityDetail.tsx。

渲染函数原文（ActivityDetail.tsx:119-120, 175-184）：
```
const cost = activity.estimated_cost;
const costKnown = (cost?.amount_minor ?? 0) > 0;
...
<div>
  <dt>{zh ? "费用" : "Cost"}</dt>
  <dd data-testid="activity-cost">
    {costKnown
      ? `${cost?.currency ?? ""} ${Math.round((cost?.amount_minor ?? 0) / 100)}`
      : zh ? "暂无价格" : "Price unavailable"}
  </dd>
</div>
```
- amount_minor > 0 仍是唯一的"知道价格"判据（120 行）。
- 免费（price = 0 / is_free）没有第三态：0 与未知一律落入"暂无价格"，不会显示「免费」。
- 类型定义中已有 metadata.price_known 与 metadata.cost_evidence（ActivityDetail.tsx:27-29），但渲染逻辑完全未使用。
- 对照组已修复：住宿侧 V8Experience.tsx:1518-1528 stayTotalLabel 与 1630-1637 行对未知房价显示 studio.priceUnknown（不冒充 ¥0.00）；钱包预订卡 V8Experience.tsx:2052-2058 price.amount_minor == null → bookings.priceUnknown。但活动详情本身未修。

结论: REPRODUCED（与基线一致：免费景点显示"暂无价格"，两态而非三态）。

---

## F7 — 方案比较部分价格假置信：PARTIALLY_FIXED

组件：SRC/features/planning/PlanComparison.tsx。

计算函数原文（PlanComparison.tsx:113-131）：
```
const costMinor = plan.total_cost?.amount_minor ?? 0;
// A plan whose stops carry no price evidence must not be presented as
// "within budget": the total is unknown, not zero.  Claiming a budget
// relationship from missing data is a fabricated fact.
const anyPriceKnown = (plan.activities ?? []).some((activity) => {
  const meta = (activity.metadata ?? {}) as Record<string, unknown>;
  return meta.price_known === true || (activity.estimated_cost?.amount_minor ?? 0) > 0;
});
const costKnown = anyPriceKnown || costMinor > 0;
const band = budgetBand(costMinor, budgetMinor);
...
const bandLabel = !costKnown
  ? zh ? "花费未知" : "Cost unknown"
  : band.key === "within" ? zh ? "预算内" : "Within budget"
  : band.key === "near" ? zh ? "接近预算上限" : "Near your limit"
  : zh ? "超预算 ..." : "Over by ...";
```
- 已修复：全新增覆盖率守卫——完全没有任何价格证据时不再输出预算内/超预算，改为"花费未知"（128-131 行），徽标样式走 unknown 类（154 行）。
- 残留：覆盖率检查是 .some()（至少一个活动有价格即可）。若 10 个活动只有 1 个已知价格（部分覆盖），anyPriceKnown=true（或 total_cost>0），仍会用不完整总价打"预算内/接近预算上限/超预算"标签（122、132-142 行）。没有"全部/比例已知"的 coverage 阈值。

结论: PARTIALLY_FIXED — "零价格假置信"已修；"部分价格假置信"未修。

---

## F9 — 路由解析健壮性：REPRODUCED

路由状态初始化与 popstate（V8Experience.tsx:163-165, 373-377, 402-410）：
```
function routeFromPath() {
  return window.location.pathname.replace(/^\/v8\/?/, "") || "hub";
}
...
const onPopState = () => setRoute(routeFromPath());
...
const navigate = (next: string) => {
  const value = next || "hub";
  withViewTransition(() => {
    window.history.pushState({}, "", `/v8/${value}`);
    setRoute(value);
  });
};
```

认识的全部路由键（SRC/routes/v8Routes.ts:1-24）：
- desktopRoutes: hub, live, map, studio, stay, discover, bookings, agent, authoritative, intelligence, twin
- mobileRoutes 额外: trips, me
- 合计 13 个 key；V8Experience.tsx:874-1027 的条件渲染逐一匹配这些 key。

- /v8/today 与 /v8/copilot 无任何别名/重定向（全文件 grep "today"/"copilot" 仅命中 i18n 键 mobile.today / mobile.copilot 与 data-testid，无 route 处理；today/copilot 不是 route key）。
- 不认识的路由落到哪：route === "hub" 等所有分支均不匹配 → <div className="v8-content"> 内主体完全空白。面包屑有 fallback（V8Experience.tsx:794 未知 route 显示 nav.hub），但仅影响标题文字，不重定向、不渲染 404。
- 结论：直接打开 /v8/today 或 /v8/copilot 深链（或被分享/历史记录带入）仍得到空白页面。

结论: REPRODUCED（无别名、无 fallback 页，深链空白与基线一致）。

---

## F12 — 包可回放性：PARTIALLY_FIXED

### 后端 source/backend/
| 检查项 | 结果 | 证据 |
|---|---|---|
| app/ 完整 | 存在 | BE/app/：main.py、agent/、planning/、execution/、intelligence/、operations/、replanning/、db/{models.py,session.py}、schemas.py、services.py 等 |
| 建表 | 无需 schema.sql | BE/app/db/session.py:188 ensure_schema() 自建（SQLite 自动建表；无 alembic migrations 目录、无 db/schema.sql） |
| pyproject.toml | 完整 | fastapi/uvicorn/sqlalchemy/alembic/pydantic/httpx/rapidfuzz/shapely/icalendar + optional ortools/pytest（BE/pyproject.toml:1-27） |
| data/v9/city_operations.json | 缺失 | BE/app/stay_mobility.py:43 DATA_PATH = .../backend/data/v9/city_operations.json；:142 city_fixture() 直接 DATA_PATH.read_text() 无容错。包内 BE/data/ 仅有 mock/wp04_city_services_overlay.json、mock/wp04_commerce_catalog.json，无 v9 目录 → 命中 city fixture 的路径会 FileNotFoundError（除非权威仓库补文件） |
| tests | 存在 | BE/tests/（README 自述 739 passed / 0 failed / 15 skipped） |

### 前端 source/frontend/
- package.json 依赖清单完整（dependencies 15 项：react 19、react-dom、@tanstack/react-query、@dnd-kit、msw、@turf/turf、@zxing/browser、dexie、lucide-react、maplibre-gl、react-hook-form、zod、xstate；devDependencies 10 项：vite、@vitejs/plugin-react、typescript、playwright、storybook、vite-plugin-pwa 等）。
- 包内无 node_modules（符合声明）。回放步骤：npm install → npm run dev -- --host 127.0.0.1；后端 python -m uvicorn app.main:app --host 127.0.0.1 --port 8000（见 README_FIRST.md "How to run"）。

### 文档
- 包根 README_FIRST.md：EAC 自述验收（6 次端到端浏览器跑通、3 视口含 Xiaomi 13 Ultra 412x915@3.5、739 后端测试通过、5 个自主 lab 周期）+ 运行复现说明 + 已知限制声明（含"房价常未知，已显示'暂无价格/花费未知'而非 CNY 0"）。
- evidence/PRODUCT_ACCEPTANCE_RESULTS.md、evidence/VISIBLE_UI_TRACE*.json、evidence/scenario_*.json 等 run 痕迹在包内。
- source/docs/ 只有 frontend/implementation 技术文档（v12 设计文档、WP checkpoint），无 EAC 测试汇总副本——测试自述依赖包根 README_FIRST.md。

结论: PARTIALLY_FIXED — 源码、依赖声明、测试证据、复现步骤齐备；唯一硬缺口是 backend/data/v9/city_operations.json 未随包提供且加载无容错，纯包回放在城市 fixture 路径上有启动期/请求期报错风险。

---

## 附：本次核查方法备注
- 全部结论基于只读 grep + 文件通读，未运行任何服务。
- i18n 键名出现工程词不算泄漏；仅"渲染值"计入（已逐条标注渲染点与是否在折叠区）。
- main.tsx 的 LegacyApp 泄漏因默认入口不可达（仅 /legacy），在 F2 中列为附录级证据。
