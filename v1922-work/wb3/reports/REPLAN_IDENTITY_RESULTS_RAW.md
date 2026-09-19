# R1 身份门审计 · REPLAN_IDENTITY_GATE · 原始证据报告

- 子代理：CityNexus 红队 R1（身份门）
- 只读研究；本报告为唯一输出文件，未修改/创建/删除任何其他文件
- 审计对象：`CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917`
- journey_id（final trace）：`d3f0cf26-7e62-47a7-8c39-111c61adeb95`
- 结论（先给）：**R1 = FAIL(P0)** —— trace 缺 ID 级身份证据，且被关闭场馆标题在 accept 后字节级存活，无法证明「已关闭场馆被重规划替换」。

---

## 一、证据摘录（原文片段）

### 1.1 Closure 事件（无 event_id / place_id / activity_id）

VISIBLE_UI_TRACE_FINAL.json（evidence/），trace[13]：
```json
{
  "ts": "2026-09-17T10:48:42.342Z",
  "journey_id": "d3f0cf26-7e62-47a7-8c39-111c61adeb95",
  "action": "disruption-event",
  "status": "201",
  "result": "CLOSURE -> 鼓浪屿风琴博物馆(临时展馆)"
}
```

PRODUCT_ACCEPTANCE_RESULTS.md（evidence/）第 49 行：
```
| disruption-event | 201 | CLOSURE -> 鼓浪屿风琴博物馆(临时展馆) (id ok) |
```
> 注意：声称「(id ok)」但**未给出任何 id**。全证据库中 closure 事件不含 event_id、place_id 或 activity_id。

scenario_degraded.json（evidence/）第 58-60 行：
```json
{ "action": "disruption+replan", "status": "201 preserved=true -1/+1",
  "result": "target=鼓浪屿风琴博物馆(临时展馆)" }
```
> 受影响目标仅以**标题字符串**表达。

### 1.2 Replan 提案（只有 count，无 diff 对象）

VISIBLE_UI_TRACE_FINAL.json，trace[14]（与 assertions.replan 同值）：
```json
{
  "ts": "2026-09-17T10:48:42.568Z",
  "action": "replan-proposal",
  "status": "201",
  "result": "preserved=true -1/+1",
  "replan": {
    "proposal_id": "593b49bd-6a77-46ef-a88b-a1cc5ed6f72f",
    "status": "PRESENTED",
    "http": 201,
    "locked_commitments_preserved": true,
    "removed_count": 1,
    "added_count": 1,
    "material_diff": true
  }
}
```
> 提案记录**仅有 proposal_id + removed_count/added_count**。全包检索 `removed[]/added[]/diff/moved[]/semantic_key/activity_key/dedupe_key` —— 除 count 外**无任何 ID 级 diff 对象**。

### 1.3 Before / After 样本（字节级相同）

VISIBLE_UI_TRACE_FINAL.json，`final_state`（trace[17]，行 219-240）：
```json
"final_state": {
  "journey_id": "d3f0cf26-7e62-47a7-8c39-111c61adeb95",
  "active_plan_before_disruption": "1f0469d5-e40f-45d4-af6e-320190c2651e",
  "active_plan_after_accept": "994ac179-64ae-4240-97fb-bddcab6ffa02",
  "plan_changed": true,
  "locked_before": 6,
  "locked_after": 6,
  "locked_preserved": true,
  "stop_titles_before_sample": [
    "厦门高崎国际机场",
    "鼓浪屿风琴博物馆(临时展馆)",
    "OSM museum",
    "Check in · 如家酒店"
  ],
  "stop_titles_after_sample": [
    "厦门高崎国际机场",
    "鼓浪屿风琴博物馆(临时展馆)",
    "OSM museum",
    "Check in · 如家酒店"
  ],
  "live_next": "下一站：厦门高崎国际机场"
}
```
> **关键**：`stop_titles_before_sample` 与 `stop_titles_after_sample` 逐元素完全相同，被关闭场馆标题 `鼓浪屿风琴博物馆(临时展馆)` 在 accept 后**仍出现在样本中**。

PRODUCT_ACCEPTANCE_RESULTS.md 第 53 行（final-truth after-replan）：
```
| final-truth | 14 activities | changed=true lockedKept=6 / 厦门高崎国际机场 / 鼓浪屿风琴博物馆(临时展馆) / OSM museum / Check in · 舒曼精 / 琴园 /
```
> 接受重规划后，行程样本**仍列出** `鼓浪屿风琴博物馆(临时展馆)`（by title）。

### 1.4 EAC 自身审计已对该歧义存疑

reports/FINAL_TRACE_AUDIT_RAW.md 第 139 行（EAC 自家 TRACE 审计）：
```
| 6 | Live material replan | ... | canonical disruption-event201 → replan-proposal preserved=true → accept-replan accepted (11:17) | 09-17 11:17 | 618fca41… | — | trace | PASS（注：canonical replan 对象 before/after_titles 完全一致，removed/added 未在标题体现，存疑minor） |
```
> EAC 审计员**自己标注**：「before/after_titles 完全一致，removed/added 未在标题体现，存疑minor」——仅以「minor」放过，仍记为 PASS。这正是 R1 门要拦截的信号。

### 1.5 生产代码：diff 仅基于 semantic_key 字符串，不携带任何 ID

source/backend/app/intelligence/replan_diff.py：
```python
@dataclass(frozen=True)
class ReplanDiff:
    kept: tuple[str, ...]
    moved: tuple[MovedActivity, ...]
    removed: tuple[str, ...]      # 仅 semantic_key 字符串
    added: tuple[str, ...]        # 仅 semantic_key 字符串
    ...
```
- `removed`/`added` 是 `tuple[str, ...]` 的 **semantic_key 字符串**，**不含 activity_id / place_id / title / provider 证据**。
- semantic_key 来源：source/backend/app/operations/v9.py:275 `_canonical_node_semantic_key` → `return key`（即 planner 节点 key，由 place id/OSM 节点派生；v9.py:1376 `policy["semantic_key"] = node.place_id`）。
- 含义：两个同名但不同 place 的实体会得到**不同** semantic_key；但若同一 place 仅以新 activity_id 重新挂入，其 semantic_key 仍源自同一 place → 会被 diff 判为「同 key（kept/moved）」而非 removed/added。

---

## 二、身份链表（Identity Chain）

| 环节 | 应有字段（ID/语义键） | trace 实际提供 | 缺口 |
|---|---|---|---|
| Closure 目标 | event_id / place_id / activity_id / semantic_key | 仅标题 `鼓浪屿风琴博物馆(临时展馆)` | **全缺** |
| 提案 proposal | proposal_id ✓；diff.removed[]/added[] 完整对象 | 仅 proposal_id + removed_count=1/added_count=1 | **diff 对象全缺** |
| 被关闭 activity | affected_activity_id / semantic_key | 无 | **全缺** |
| 被关闭 place | affected_place_id / provider_id | 无 | **全缺** |
| accept 后 active plan | active_plan_id ✓；活动全量 id/key | active_plan_id ✓；仅标题样本 | **活动 id/key 全缺** |
| before/after 同标题实体对比 | 各自 place_id / activity_id | 仅标题（字节级相同） | **无法对比 ID** |

- `activity_id` 在**全部 evidence 中 0 次出现**。
- `place_id` 在 evidence 中仅出现于 OVERNIGHT_RUN_LEDGER.jsonl 第 8 行，且是缺陷描述文字（「C4 commitment remap comparing place_id to a canonical semantic key」），非 closure 身份数据。
- 包内 `backend/data` 只有 `wp04_city_services_overlay.json` 与 `wp04_commerce_catalog.json`；`real_place_candidates` 是**运行时从 OSM 捕获**的表（main.py:1360、session.py:564），包内**无静态风琴博物馆条目**，无法离线确认「是否存在两个同名风琴博物馆」。
- 源码中精确字符串 `风琴博物馆` 在 `app/` 下**不存在**，证明风琴博物馆是运行时 OSM 实时发现数据，不在包内。

---

## 三、七断言逐条判定（REPLAN_IDENTITY_GATE）

**断言 1 · active plan 是否真的变了（对比 plan_id）**
- before=`1f0469d5-e40f-45d4-af6e-320190c2651e` → after=`994ac179-64ae-4240-97fb-bddcab6ffa02`，`plan_changed=true`。
- 判定：**PASS**。
- 附注（trace 完整性疑点）：`selected_plan_id`=`53d340c6-...`（用户所选候选之一），但 `active_plan_before_disruption`=`1f0469d5-...` **不在候选列表**（候选为 53d340c6 / 69320b5c / 1ab67621）。即「disruption 时的 active plan」并非「用户所选 plan」——存在 plan 版本追踪与所选不一致，属 TRACE_INTEGRITY 疑点，但不影响「plan 变了」本身。

**断言 2 · removed key 是否对应被关闭目标或正当恢复目标**
- 无 diff.removed[]、无 semantic_key、无 place_id/activity_id。无法确认 removed 项就是 `鼓浪屿风琴博物馆(临时展馆)`。
- 判定：**UNVERIFIABLE**（缺 ID 级证据）。

**断言 3 · 被关闭的 activity 身份是否原样存活**
- 无任何 activity_id / semantic_key 可对比。但标题样本中 `鼓浪屿风琴博物馆(临时展馆)` 前后均存在 → 该**标题**存活。
- 判定：**UNVERIFIABLE（ID 级）；标题级信号 = 存活**（与「已移除」主张冲突）。

**断言 4 · added key 是否有 grounded 身份**
- 无 diff.added[]、无 semantic_key、无 place_id/provider 证据。无法证明新增项有真实 grounded 来源。
- 判定：**UNVERIFIABLE**（缺 ID 级证据）。

**断言 5 · 受保护承诺是否存活**
- `locked_commitments_preserved=true`，`locked_before=6`/`locked_after=6`。
- 判定：**PASS**（仅以数量计；未对具体受保护 key 做身份核验，但数量一致且命题自身记录为 preserved）。

**断言 6 · 已关闭 Place 是否通过新 Activity ID 被悄悄带回来（关键）**
- 要求：对比 before/after 同标题 `鼓浪屿风琴博物馆(临时展馆)` 的 place_id 与 activity_id。
- 现实：trace **无 place_id / activity_id**；且 before/after 标题样本**字节级相同**，该标题在 accept 后存活。
- 因缺 ID，无法排除「同一 place 以新 activity_id 重新挂入（同语义键 → diff 判 kept/moved，而非 removed/added）」这种静默带回。
- 包内无静态 place 数据，无法确认存在「两个同名风琴博物馆」以证成正当替换；亦无法证成「仅一条 → same-ID 存活」。
- 判定：**FAIL（P0 风险）**——在「声称 removed=1 替换被关闭场馆」的同时，被关闭场馆标题在 accept 后字节级存活，且全链路无任何 ID 级证据能反驳「同身份静默存活/带回」。EAC 自身审计亦标注此标题一致性「存疑」。

**断言 7 · UI 摘要（移除 1 项 · 新增 1 项）与真实 diff 是否一致**
- UI/摘要：removed=1 / added=1（material_diff=true）。
- 真实 diff（ID 级）：**缺失**；可用身份信号（标题）前后完全一致 → 标题维度「无变化」。
- 判定：**UNVERIFIABLE / 标题维度矛盾**。UI 摘要声称 -1/+1，但唯一可用的身份信号（标题）显示被关闭场馆标题仍存活，二者无法在 ID 级对账，且方向上与被关闭场馆「已移除」不一致。

---

## 四、同标题不同实体可能性（任务 5）

- 包内 `real_place_candidates` 为运行时 OSM 捕获表，源码无静态 `风琴博物馆` 条目；离线无法确认是否存在两个同名风琴博物馆。
- 因 trace 无 place_id / activity_id，**无法对比 before/after 同标题实体的 ID 是否相同**。
- 若按 R1 门规则「after 同标题实体 ID 不可分 + 标题存活 ⇒ 视为 same-ID 存活」：本包满足该条件（有存活同标题、无 ID 可证不同），故落入 **R1 FAIL(P0)** 分支。
- 即便退一步假设存在「另一同名 grounded 场馆」替换，trace 也**未提供该替换项的 place_id/provider_id/semantic_key 来证明来源真的不同地点**——故「正当替换」同样未被证据支持。

---

## 五、最强间接证据汇总

1. **标题前后字节级相同**（VISIBLE_UI_TRACE final_state + PRODUCT_ACCEPTANCE final-truth）：被关闭场馆 `鼓浪屿风琴博物馆(临时展馆)` 在 accept 后仍存在。
2. **提案仅含 count、无 diff 对象**：全包无 `removed[]/added[]/semantic_key/activity_id`。
3. **生产 ReplanDiff 设计上不带 ID**（replan_diff.py）：身份对比能力本就未被产物化。
4. **EAC 自身审计存疑**：FINAL_TRACE_AUDIT_RAW.md 第 139 行明确「before/after_titles 完全一致，removed/added 未在标题体现，存疑minor」。
5. **历史身份混淆缺陷**：OVERNIGHT_RUN_LEDGER.jsonl 第 8 行记录 C4 缺陷「commitment remap comparing place_id to a canonical semantic key」——同代码路径存在 place_id↔semantic_key 混淆史。
6. **plan 版本追踪不一致**：selected_plan_id(53d340c6) ≠ active_plan_before_disruption(1f0469d5)，TRACE_INTEGRITY 疑点。

---

## 六、最终 R1 结论

**R1 = FAIL(P0)**

理由：
- EAC 声称的「闭环证据 = 已关闭场馆被重规划替换（removed=1, added=1，用户接受）」**在身份级无法成立**：trace 完全缺失 activity_id / place_id / semantic_key / diff 对象，全部可用身份信号仅为标题字符串。
- 唯一可用的身份信号（标题）显示被关闭场馆 `鼓浪屿风琴博物馆(临时展馆)` 在 accept 后**字节级存活**，与「已移除/替换」主张方向冲突。
- 无法排除「同一被关闭 Place 通过新 Activity ID 被静默带回来」（断言 6 的 P0 场景）；且包内无静态 place 数据、无 ID 级 diff 来证伪。
- EAC 自家审计已对同一现象标注「存疑 minor」，仍放过为 PASS——红队不采信该「minor」判定。

建议（给 EAC，非本次任务范围）：在 trace 中产物化 proposal 的 `diff.removed[]/added[]/moved[]` 完整对象（含 activity_id、place_id、semantic_key、title、provider_id），并重规划前后对「被关闭标题实体」的 place_id 做显式不一致校验，方能闭合 R1。
