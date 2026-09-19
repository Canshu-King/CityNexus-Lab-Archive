# REPLAN_IDENTITY_RESULTS — R1 重规划身份门审计（v2 复检）

日期：2026-09-18 00:2x（北京时间）· 审计对象：`CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917.zip`（SHA-256 匹配 ✓）· 权威仓库未修改

## 结论：R1 = PARTIALLY_FIXED（引擎真值正确，但 EAC 提交的证据不可验证 + 两个健壮性缺陷）

---

## A. 包内证据审计（子代理全文审计，详见 REPLAN_IDENTITY_RESULTS_RAW.md）

**判定：INSUFFICIENT_EVIDENCE。**

1. 最终 trace 声称 `CLOSURE -> 鼓浪屿风琴博物馆(临时展馆)` → removed=1/added=1 → UI 接受 → plan 变更
   （`active_plan_before_disruption=1f0469d5` → `active_plan_after_accept=994ac179`，断言 1 可证）。
2. 但全 16 个 evidence 文件中 **`activity_id` 出现 0 次**；提案仅有 `removed_count=1/added_count=1`，
   **无 diff.removed[]/added[]/semantic_key/place_id 任何 ID 级字段**。
3. `stop_titles_before_sample` 与 `stop_titles_after_sample` **逐元素完全相同**，同标题字节级存活；
   无法排除「同一被关闭 Place 换 activity_id 静默带回」（断言 6 无法证实）。
4. 生产 diff 代码 `replanning/feasibility.py` + `intelligence/replan_diff.py` 的语义键即
   `place_id or city_service_id or activity_id`（main.py:7757）——若真做了替换，标题必然不同；
   **标题不变 + removed=1 强烈暗示他们的 added 项复用了同一 place**，或标题样本是陈旧快照。
5. EAC 自家复核报告已标注「before/after titles 完全一致，存疑」却仍判 PASS——自我矛盾。
6. 附带发现：包内 `source/backend` 缺 `db/schema.sql`（F12 类打包缺口，离线回放会启动失败）。

## B. WorkBuddy 活体受控流（隔离栈：hotfix 源码 + 隔离 DB 副本，权威仓库零接触）

按 REPLAN_IDENTITY_GATE 记录一次受控流（全新 journey `841a1c79-249d-4844-95ed-647279acd603`）：

### Before
| 项 | 值 |
|---|---|
| journey_id | `841a1c79-249d-4844-95ed-647279acd603` |
| base_plan_id | `f19d1146-712d-4020-b634-5bf3bc61f6f0`（ACTIVE, INITIAL） |
| 受影响 activity_id | `f19d1146-a2`（当前时段活动） |
| 受影响 place_id / 语义键 | `place-gulangyu-organ`（OSM 风格种子，坐标 24.4435/118.0652） |
| title | 鼓浪屿风琴博物馆(临时展馆) |
| locked/protected | false / 无 C4 承诺（干净旅程） |

### Proposal（`POST /journeys/{id}/replans`，trigger_event `658a0e16-7a0b-4b13-be9b-b9dc6eb631a7`）
| 项 | 值 |
|---|---|
| proposal_id | `a6c2b18d-d67e-4ef6-9cb0-c063467405bf`（后续 idempotent 重跑为 8a115275） |
| proposed_plan_id | `afce0ec8-f1d9-40aa-9985-affc072fd7e9` |
| diff.removed 精确语义键 | `["place-gulangyu-organ"]` |
| diff.added | `[]`（candidate_family=`F1_OPTIONAL_REMOVAL`：直接移除，无替换） |
| diff.kept | `["place-gulangyu-pier","place-longtou-food"]` |
| 事件级证据 | incident_recovery_evidence 含 event_id、mobility_snapshot（RUNTIME_CAPTURE、mock-mobility、未降级） |

### After accept（`POST /replans/{id}/accept`，带 Idempotency-Key → 200）
| 项 | 值 |
|---|---|
| active_plan_id | **`afce0ec8-…`**（journeys.active_plan_version_id 已切换） |
| 旧 plan 状态 | `SUPERSEDED`；proposed plan `ACTIVE`，parent=base ✓ |
| 接受后全部活动 | `5f1e84dc`(pier) + `03226c7c`(lunch)，**无任何 organ 活动** |
| 全部 place_ids | `place-gulangyu-pier`、`place-longtou-food`，**organ place 消失** |

### 七断言判定（受控流）
1. active plan 变更 — **PASS**（f19d1146 → afce0ec8，DB 直读）
2. removed 键对应被关闭目标 — **PASS**（=place-gulangyu-organ，即事件目标）
3. 被关闭活动身份未存活 — **PASS**（activity 与 place 均不存在）
4. added 有 grounded 身份 — **N/A**（added=[]，恢复契约为移除；无编造替换）
5. 受保护承诺存活 — **PASS**（本旅程无承诺；preserved_protected=[] 一致）
6. 无关闭 Place 借新 ID 回归 — **PASS**（接受后 place 集合中无 organ）
7. UI 摘要与 diff 一致 — **PASS**（源码 LiveRecovery.tsx:206-211 按计数渲染，"移除 1 项" 与 removed=1 一致；注意 added=0 时 UI 显示尾随间隔符的次要瑕疵）

### 受控流暴露的两个新缺陷（健壮性，非身份门本身）
- **缺陷 R1-a（P1）**：`main.py:6591` `trigger_event.affected_activity_id in {row.activity_id for row in c4_rows}` ——
  自由文本闭馆事件未解析目标时 `affected_activity_id=None`，而预订导入产生的 C4 承诺 `activity_id=None`（真实顺序：先导预订后规划），
  `None in {None}` 恒真 → **任何有导入预订的旅程，闭馆重规划一律 422「closed activity is protected」误拒**。实测复现（r1_proposal.json）。
- **缺陷 R1-b（P2）**：语义编译器（deepseek-v4-flash, confidence 0.9）对同一闭馆命令，第一次正确解析出 mutable 目标，
  第二次（新旅程）`unresolved_references=["gulangyu_organ_museum_temporary_hall"]`、mutable=[] —— 目标解析**非确定性**。

## C. R1 总判定

**PARTIALLY_FIXED**：
- **引擎真值：PASS** —— 在可工作的受控流中，被关闭实体按恢复契约被真正移除，无同题替换、无 ID 漂移回归；这是产品机制层的硬证据。
- **提交证据：FAIL** —— EAC 的 canonical trace 无 ID 级字段、同标题字节级存活，其「CLOSURE 闭环」主张不可验证，不能作为验收证据。
- **健壮性：FAIL** —— R1-a 使真实预订旅程的旗舰闭馆流直接 422；R1-b 造成目标解析不稳定。
