# RESIDUAL_SRC_SCAN_B — 残留发现源码级复核（R2 / R6 / R7 / R9）

扫描对象（只读）：`D:\moodle\CityNexus-WorkBuddy\overnight-20260917\hotfix_pkg\CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917\`
扫描方式：纯源码检索 + 截图判读，未运行任何服务。除本报告外未创建/修改任何文件。
扫描时间：2026-09-17

---

## R2 — Live 多张不可区分的重规划卡片：**REPRODUCED**

### 代码证据

渲染组件为 `source\frontend\src\features\execution\LiveRecovery.tsx`（`features\live\` 目录不存在，Live 组件位于 `features\execution\`；由 `app\V8Experience.tsx:11` 导入、`:954` 在 `route === "live"` 挂载）。

1) pending 定义（LiveRecovery.tsx:106-108）——把 PRESENTED 与 GENERATED 全部收进来：
```tsx
const pending = proposals.filter(
  (p) => p.status === "PRESENTED" || p.status === "GENERATED",
);
```

2) 渲染（LiveRecovery.tsx:188-251）——仍是 `pending.map()` 无差别渲染，每个 proposal 一张卡：
```tsx
{pending.length > 0 ? (
  pending.map((proposal) => {
    const removed = proposal.diff?.removed ?? [];
    const added = proposal.diff?.added ?? [];
    return (
      <article className="live-proposal" key={proposal.id} data-testid="live-proposal">
        <b>{zh ? "推荐怎么改" : "Suggested change"}</b>
        <p className="live-unchanged" data-testid="live-unchanged">
          {proposal.locked_commitments_preserved ? "已确认的预订和到达/离开时间保持不变。" : "注意：部分已确认内容会受影响。"}
        </p>
        {(removed.length > 0 || added.length > 0) && (
          <p className="live-diff">
            {removed.length > 0 && (<span>{`移除 ${removed.length} 项 · `}</span>)}
            {added.length > 0 && (<span>{`新增 ${added.length} 项`}</span>)}
          </p>
        )}
        <div className="live-actions">
          <button ... onClick={() => void accept(proposal.id)}>{zh ? "接受新方案" : "Accept new plan"}</button>
          <button ...>{zh ? "仅调整今天" : "Adjust today only"}</button>
          <button ...>{zh ? "稍后提醒" : "Remind me later"}</button>
        </div>
      </article>
    );
  })
) : ( ... )}
```

### 三项检查结论
- (a) 去重逻辑：**无**。全文件无按 diff 摘要合并/去重的代码；只有 disruptions 列表按 `item.id` 做了 Map 去重（:95-97），与 proposal 卡无关。
- (b) 方案间差异展示：**无**。卡片正文只显示两样内容——`locked_commitments_preserved` 布尔文案 + diff 的**数量**（`移除 N 项 · 新增 M 项`），不显示 removed/added 的具体条目、目标、时间。若两个方案 diff 数量相同，卡片逐字相同。
- (c) proposal_id 级区分：**仅存在 `key={proposal.id}`**（React key，:193）与 `busy === proposal.id` 的按钮态（:222）， traveller 不可见任何 proposal 标识；标题、正文、按钮文案对每张卡完全一致。

对照：`features\recovery\V14RecoveryTruthPanel.tsx:58` 是"单选一条"的另一种做法（`items.find(PRESENTED) ?? items[0]`），说明仓库内已有收敛渲染的先例，但 Live 页未采用。

### 截图证据
- `screenshots\12_live_disruption.png`：**页面上同时出现两张完全相同的"推荐怎么改"卡片**——标题相同、正文均为"已确认的预订和到达/离开时间保持不变。"、差异行均为"移除 1 项 · 新增 1 项"、按钮组相同。视觉上零区分。
- `screenshots\11_live.png`（无提案时）与 `13_live_accepted.png`（接受后）仅各一张/无卡，不构成反证。

### 结论
`pending.map()` 无差别多卡渲染原样保留；无去重、无内容级差异展示、无可见 proposal 区分。**REPRODUCED**。

---

## R6 — Copilot dock 与核心内容抢空间：**PARTIALLY_FIXED**

### 展开 / 收起逻辑（source\frontend\src\features\agent\CopilotDock.tsx）

1) 默认折叠（CopilotDock.tsx:527）：
```tsx
const [open, setOpen] = useState(false);
```
2) 折叠态只渲染一条 56px 高的边缘按钮，展开态渲染完整面板，由同一 `open` 状态切换（:582-589）：
```tsx
<aside className={`cn-copilot-dock ${open ? "open" : "collapsed"}`} data-testid="v18-copilot-dock">
  {!open ? (
    <button className="cn-copilot-edge" type="button" onClick={() => setOpen(true)} ...>
```
3) dock 的 props 只有 `data` 与 `onNavigate`（:517-523）——**不接收任何 sheet/modal 打开状态**，因此不存在"modal 打开时让位"的机制。

### 与 sheet/modal 的层叠关系（source\frontend\src\styles.css）

- dock：`styles.css:320` → `.cn-copilot-dock { position: fixed; right: 22px; bottom: 22px; z-index: 25; ... }`；移动端 `:400` → `bottom: 72px`。
- AI 规划 sheet（PlanWithAiSheet.tsx:245 使用 `v8-sheet-backdrop`）：`styles.css:265` → `.v8-sheet-backdrop { position: fixed; inset: 0; z-index: 20; ... }`。
- 抽屉 `z-index: 31`（:299）高于 dock；但 **sheet 背景层 z-index 20 < dock 25**，dock 悬浮在 sheet 之上。
- 全 styles.css 无任何 `.sheet-open .cn-copilot-dock` / `aria-modal` 联动隐藏规则；`V8Experience.tsx:1058` 的 `<CopilotDock ... />` 无条件渲染，`sheetOpen`（:253）与 `planAiOpen`（:1059）都不影响它。

### 截图证据（dock 是否遮挡主操作区）
- `screenshots\01_create.png`：创建流程 + AI 规划 sheet 打开——"CityNexus Copilot" 边缘条悬浮在 sheet 示例 chips 行之上将其遮住，左下"稍后"按钮被挤压成一条窄片。
- `screenshots\02_ai.png`：同样场景——边缘条盖住"已生成 3 个可选方案/去今天对比…"与底部操作行之间区域，"稍后"按钮被裁切。
- `screenshots\12_live_disruption.png`：Live 页两张方案卡堆叠，底部边缘条直接盖住第三张卡的开头文字。
- `screenshots\08_booking.png`：booking 表单页，边缘条占据底部横带（未盖住关键控件，但持续占位）。
- `screenshots\09_copilot.png`：用户主动展开时面板占据下半屏约 45%（属用户预期行为，不计为缺陷）。

### 结论
相对"常驻大面板"有真实缓解：**默认折叠为一条边缘按钮，仅在用户点击后展开**。但 sheet/modal 打开时 dock 完全不让位（无状态联动、z-index 25 高于 sheet 20），截图证实 AI 规划 sheet 与 Live 页内容被遮挡/挤压。**PARTIALLY_FIXED**。

---

## R7 — 酒店卡片弱差异化：**REPRODUCED**

### 代码证据

两处住宿渲染：
- `features\stay\HotelsPanel.tsx`（`V8Experience.tsx:1211` 挂载，即截图 06/07 对应页面）
- `features\stay\StayExplorer.tsx`（`V8Experience.tsx:939`，stay 探索页）

1) HotelsPanel 卡片字段（HotelsPanel.tsx:177-210）：价格（未知时如实显示"暂无价格"，:179-186）、步行分钟（:189-191）、到达/离开衔接百分比（:193-195）、退改二值（:197-199）、推荐理由（:201-210）：
```tsx
<p className="hotel-reason">
  {zh ? "推荐理由：" : "Why: "}
  {option.hard_constraints_passed
    ? zh
      ? `与行程冲突最少，步行负担 ${option.walking_min} 分钟，预留缓冲 ${option.protected_margin_min} 分钟。`
      : `Fewest itinerary conflicts, ${option.walking_min} min walking, ${option.protected_margin_min} min protected margin.`
    : zh ? "与当前硬约束存在冲突，仅供参考。" : "Conflicts with current hard constraints; shown for reference only."}
</p>
```
- 推荐语是**固定模板**嵌入两个真实数值（walking_min / protected_margin_min）；"与行程冲突最少"这句是每张通过卡都一样的样板话。卡上**不显示**区域/地址（StayOption.location 仅有经纬度且未渲染）、**不显示供应商身份**、**不显示 rank**。
- 全前端源码检索"证据不足/不足以排名/无法排名"：仅 `discovery.notRanked: "未排名"`（LocaleContext.tsx:984，用于发现页）——**酒店页没有任何"证据不足以排名"的明示**。列表介绍只说"按与行程的关系排序"（HotelsPanel.tsx:151-152）。

2) StayExplorer 相对更完整：卡片含房型、退改、步行/余量/交通方式（:38），详情面板有供应商证据标签——`evidenceLabel`（:141-149）在无置信度时显示"暂无供应商证据"，退改摘要未知时显示"退改政策未知"（:131-139）。但该差异化只存在于 stay 探索页，不在截图对应的 HotelsPanel。

### 截图证据
- `screenshots\06_hotels.png`：三张卡（如家酒店 / 舒曼精品酒店 / 厦门鹭基酒店）除名称外**逐字段相同**：价格均为"暂无价格"、步行均"22 分钟"、到达/离开衔接均"1% / 1%"、退改均"不可取消"、推荐理由均为同一句"与行程冲突最少，步行负担 22 分钟，预留缓冲 417 分钟。"。"1% 衔接"与"冲突最少"同屏出现，自相矛盾且无任何排序依据说明。
- `screenshots\07_hotel_selected.png`：选中态仅增加"已选择"徽标，无额外差异信息。

### 结论
字段虽为真实数据，但推荐语是固定模板、无区域/供应商/排名依据、无"证据不足以排名"明示；实测截图中各卡完全同质。**REPRODUCED**（StayExplorer 的供应商证据标签是局部改进，但未覆盖本发现指向的酒店比较页）。

---

## R9 — 包内陈旧验收证据：**REPRODUCED**

### evidence\ 全部 16 文件（大小字节 / mtime 2026-09-17）

| 文件 | 大小 | mtime |
|---|---|---|
| CHANGED_FILES.txt | 2,289 | 18:52 |
| FINAL_FINDINGS_REVALIDATION.md | 3,903 | 18:43 |
| FINAL_HOTFIX_RESULTS.md | 2,974 | 18:50 |
| FINAL_TRACE_MAPPING.md | 2,087 | 18:50 |
| LAB_CYCLES.jsonl | 2,433 | 14:51 |
| LAB_PROBE_RESULTS.json | 3,815 | 14:47 |
| OVERNIGHT_RUN_LEDGER.jsonl | 17,383 | 18:54 |
| PRODUCT_ACCEPTANCE_RESULTS.md | 8,173 | **14:38** |
| TEST_RESULTS.md | 1,529 | 18:52 |
| VIEWPORT_EVIDENCE.json | 4,568 | 14:37 |
| VISIBLE_UI_TRACE_FINAL.json | 11,578 | 18:49 |
| scenario_bookingfirst.json | 1,086 | 11:26 |
| scenario_budget.json | 2,415 | 11:21 |
| scenario_degraded.json | 2,666 | 11:27 |
| scenario_hostile.json | 2,357 | 14:35 |
| scenario_longtrip.json | 2,418 | 11:21 |

### reports\ 全部 6 文件

| 文件 | 大小 | mtime |
|---|---|---|
| WORKBUDDY_FINDINGS_REVALIDATION.md | 41,199 | **10:38** |
| AUTONOMOUS_CYCLE_1.md | 6,751 | 14:46 |
| AUTONOMOUS_CYCLE_2.md | 1,127 | 14:51 |
| AUTONOMOUS_CYCLE_3.md | 926 | 14:51 |
| AUTONOMOUS_CYCLE_4.md | 1,181 | 14:51 |
| AUTONOMOUS_CYCLE_5.md | 750 | 14:51 |

### 是否标注 PRE_HOTFIX / SUPERSEDED
全包检索 `SUPERSEDED|PRE_HOTFIX|superseded`：命中全部来自**产品代码/测试/领域文档**（PlanVersion 状态机等），**README_FIRST.md 与 PRODUCT_ACCEPTANCE_RESULTS.md 及所有 14:38 之前生成的证据文件均无任何陈旧标记**。README_FIRST.md（:14-24）的阅读顺序只指向最终轮文档，声明本包"NOT the previous package"（:7-8），但未对同包内的旧验收文件做失效声明。

### 与最终 trace 的矛盾点
1. **同一裁决口径、不同事实**：PRODUCT_ACCEPTANCE_RESULTS.md:115-117（14:38，修复前）就宣告 `READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL`；FINAL_HOTFIX_RESULTS.md:6-8（18:50）再次宣告同一结论。旧文档在最终轮发现 B1 陈旧 Copilot 证据、stay 日历/可行性闸门腿时长不一致、materialiser 信任陈旧邻接事实这三个缺陷**之前**给出的"可试用"结论未被标记失效。
2. **测试基数矛盾**：PRODUCT_ACCEPTANCE_RESULTS.md:80 声称 `739 passed, 0 failed, 15 skipped`；TEST_RESULTS.md / FINAL_HOTFIX_RESULTS.md 为 `748 passed`。旧数字以同等权威口吻并存于同一 evidence 目录。
3. **Copilot 证据自相矛盾**：PRODUCT_ACCEPTANCE_RESULTS.md:46 记录 `copilot-question | empty`（Copilot 答案为空），但 :66 断言 `Copilot answer judged useful: True`——这正是 B1"stale final Copilot evidence"（FINAL_FINDINGS_REVALIDATION.md:9）确认并修复的病灶，旧文档原文仍在且无勘误。
4. **stay-truth 用 undefined 当 PASS**：PRODUCT_ACCEPTANCE_RESULTS.md:41 记录 `stay-truth | SELECTED | undefined in=undefined out=undefined`；FINAL_FINDINGS_REVALIDATION.md:16 明言 "`undefined` can no longer be a PASS value"。旧验收口径与新规则直接冲突，原文未改。
5. **journey 指纹不同**：旧验收跑 `618fca41`（:30），最终 trace 为 `d3f0cf26-7e62-47a7-8c39-111c61adeb95`（FINAL_TRACE_MAPPING.md:8）。旧 trace 对应的是修复前构建。
6. **WB-H1..H5 全 FIXED 表过早**：PRODUCT_ACCEPTANCE_RESULTS.md:103-113 声明 WB-H1..H5 全部 FIXED；而其时间戳之后最终轮又发现了两个真实缺陷（FINAL_HOTFIX_RESULTS.md:23-35）。该表的"全部关闭"结论不适用于最终候选包。
7. LAB_PROBE_RESULTS.json、LAB_CYCLES.jsonl、VIEWPORT_EVIDENCE.json、scenario_*.json（11:21-14:51）与 WORKBUDDY_FINDINGS_REVALIDATION.md（10:38）全部早于最后一次源码编辑，同样无陈旧标注。

### 结论
最终轮文档本身合格（18:43-18:54 生成、口径一致），但包内 14:38 及更早的验收/循环证据未做 PRE_HOTFIX / SUPERSEDED 标注，其中含与最终 trace 直接矛盾的旧验收声明。**REPRODUCED**。

---

## 总表

| 项 | 结论 | 一句话 |
|---|---|---|
| R2 Live 重复方案卡 | **REPRODUCED** | LiveRecovery.tsx:188 仍 `pending.map()` 无差别渲染，无去重/无差异展示/无可见 proposal 区分；12_live_disruption.png 双卡逐字相同 |
| R6 dock 抢空间 | **PARTIALLY_FIXED** | 默认折叠为边缘条（真实缓解），但 z-index 25 > sheet 20 且无状态联动，AI 规划 sheet 与 Live 内容仍被遮挡 |
| R7 酒店卡弱差异化 | **REPRODUCED** | 推荐语为固定模板，06_hotels.png 三卡除名称外逐字段相同，无"证据不足以排名"明示 |
| R9 陈旧验收证据 | **REPRODUCED** | 14:38 前证据无任何失效标注；PRODUCT_ACCEPTANCE_RESULTS.md 含 739/748、empty-but-useful、undefined-as-PASS、双 journey 指纹等矛盾 |