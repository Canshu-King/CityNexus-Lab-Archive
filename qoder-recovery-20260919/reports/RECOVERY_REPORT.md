# CityNexus — Extreme v2 孤儿工作恢复与突变门禁补强报告

日期：2026-09-19　执行者：Qoder（独立恢复线）
写入范围：仅 `D:\moodle\_qoder_recovery_20260919`
只读输入：`_qoder_integration_20260919`、`_qoder_th_20260918`、`CityNexus`、`_codex_sol_extreme_v2_20260919`
（三棵受保护树与 Codex 树均未修改、未提交、未清理）

---

## 1. 为什么要做这件事

Codex 的 Extreme v2（轨 I–M）在写报告之前因额度耗尽中断：`reports/`、`artifacts/`、
`candidate_patches/`、`survivor_regressions/` 全部为空，也没有交付 ZIP。它真正有价值的
产出只剩两处易失形态——`replay_cases/` 里的 JSON，以及 `_codex_sol_extreme_v2_20260919/snapshot/citynexus`
里 **7 个从未提交的改动文件**。任何一次目录清理都会把它们永久抹掉。

本次恢复做三件事：把孤儿改动冻结成可交接补丁；在**当前**整合线顶端重新验证；把 Codex 报告里
"2 个突变存活" 背后的真实缺口补成可执行门禁。

---

## 2. 恢复出来的补丁

基线：`0fa1f6c`（Codex 当时的冻结提交）。它们已全部提交进本目录的
`verify/citynexus`，分支 `qoder/recovery-extreme-v2`，提交 `f331e43`，因此不再依赖任何工作树。

| 补丁 | 关切 | 文件 |
|---|---|---|
| `CX-REC-001-backend-stale-cursor-fail-closed.patch` | 后端把"游标缺失"与"游标存在但未知"合并回退，后者会伪造 Now | `backend/app/operations/v9.py` |
| `CX-REC-002-frontend-live-cursor-window.patch` | Live 主卡/次卡写死 `activities[0]/[1]`、`legs[0]` | `frontend/src/app/V8Experience.tsx` + 新增 e2e 与独立 playwright 配置 |
| `CX-REC-003-journey-write-serialization.patch` | 同 Journey 并发写：重复幂等键抛约束异常、两个提案同时 ACCEPTED 留下双 ACTIVE 方案、付款捕获把旧方案的承诺升成 C4 | `backend/app/main.py`、`backend/app/commerce/service_impl.py`、新增 `backend/app/concurrency_guards.py` |
| `CX-REC-ALL-extreme-v2-recovery.patch` | 三者合并 | — |

可应用性（`git apply --check`，全部通过）：

- 基线 `0fa1f6c`：APPLIES
- 当前整合顶端 `7f2f5bb`（`0fa1f6c` 之后又有 3 个提交）：APPLIES，只有 4–9 行行偏移
- 三个补丁涉及文件互不重叠，可以单独评审、单独合入

恢复期间 Qoder 线又把整合顶端推进到 `7870270`（pass-9 报告）。对它重新拉取并复检：
三个补丁仍 APPLIES；且该顶端上三条缺陷**原样存在**——`v9.py` 里没有任何 `stale_cursor` 处理，
`V8Experience.tsx` 的 Live 仍是 `activities[0]/[1]`、`legs[0]`（2028–2030 行）与
LiveSecondary（2102–2103 行），1469 行还在用墙上时间推 Now，`C4_Anchored` 四处查询未变。
所以这份补丁不是"已经有人做了"的重复劳动。

真实回归（CityNexus venv，含 ortools，清空外部 AI key）：

| 树 | 结果 |
|---|---|
| `7f2f5bb` 未打补丁 | 827 passed / 15 skipped / 0 failed |
| `7f2f5bb` + REC-001/002/003 | 827 passed / 15 skipped / 0 failed |
| 上述 + RX-1、RX-2 两条新门禁 | 831 passed / 15 skipped / 0 failed |

（RX-3 未并入该次全量，它在 `wt_tip_clean` 上单独跑补丁前/补丁后/突变三态，见 §5。）

即：恢复补丁在当前顶端**零回归**。带 ortools 的环境里补丁前后同为 0 失败；缺 ortools 的
Codex 快照环境里，补丁前后也是同一份 32 条失败名单（`raw/baseline_names.txt`、
`raw/patched_names.txt` 逐条相同），没有一条由补丁引入。

---

## 3. 顺带纠正了两个已经被写进结论的事实

**其一：`827 passed` 是真的，Codex Extreme v2 的数字不是同一环境。**
在 Codex 快照自带的 `backend/.venv` 里 `ortools` 缺失，全量跑成 32–38 失败
（`ORToolsUnavailable` 会让 solver 与一批 open-meteo 用例连带失败，包括
`assert 'DEETERMINISTIC_HEURISTIC' == 'ORTOOLS_CP_SAT_V2'`）。换用 `CityNexus/.venv` 后
`7f2f5bb` 精确复现 827/15/0。这条线以后报数必须写明用哪个解释器。

**其二：Codex 报的 "13 KILLED / 2 SURVIVED" 里只有 7 个是真杀掉。**
逐条看 `evidence` 末行就能分出来（`raw/../mutation_kill_audit` 见 §4）：

- 3 个"杀掉"其实是门禁选空：`J-ACK-RESOLVED`（21 deselected，0 跑）、
  `J-STALE-CURSOR-FALLBACK`（6 deselected，0 跑）、`J-PROTECTED-C4-DROPPED`
  （`ERROR: file or directory not found`）。`mutation_runner.py` 把非零退出码一律记成 KILLED，
  而 pytest 的"没跑到测试"退出码正是 5。
- 3 个"杀掉"证据自相矛盾：`J-ACK-CLOSES-UNRELATED`、`J-PARTIAL-BUDGET-FULL`、
  `J-LIVE-FIXED-INDEX` 都是 Playwright 返回 1 但同一行写着 `1 passed`——失败原因不属于断言，
  不能算证明。
- 7 个有真实断言失败佐证：`J-PROVENANCE-LAUNDER`、`J-NONE-QUALITY-HARD`、
  `J-NONE-NONE-PHYSICAL`、`J-COORDINATE-ONLY-SAME`、`J-CROSS-PROVIDER-NUMERIC`、
  `J-AMBIGUOUS-ADMITTED`、`J-MATERIALITY-DIFF`。

这不是道德瑕疵，是量具缺陷：**"非零退出=杀掉" 会把"没测"读成"测过了"**，方向恰好最危险。
（下面 §5 已把其中 3 个空跑项重测到定论：1 个其实被别的门禁杀掉、1 个由 RX-3 补上、
1 个 `J-PROTECTED-C4-DROPPED` 确认为真实存活。）

---

## 4. 两个存活突变：现在真的有关卡了

`tests/test_rx1_cross_journey_trigger_gate.py`、`tests/test_rx2_mock_hard_laundering_gate.py`
（本目录 `tests/`，并已放进 `verify/wt_tip/backend/tests/` 与 `verify/wt_mut/backend/tests/` 做过双向验证）。

### RX-1 跨 Journey 触发事件

结论：仓库里**已有**一条名字完全对上的测试
`test_wp05_integrity_next.py::test_replan_trigger_event_must_belong_to_same_journey`，
但它是空转的。它发的是不带 `affected_activity_id` 的 `WEATHER` 事件，而这类事件在后面的目标
解析阶段本来就会被拒成 **HTTP 422 `REPLAN_TARGET_UNRESOLVED`**；断言只写了 `status_code == 422`，
于是删掉 journey 归属校验它照样绿。实测：

```
变异体 CROSS status 422 {"error":{"message":"REPLAN_TARGET_UNRESOLVED"}}
干净态 CROSS status 422 {"error":{"message":"trigger event is not on this journey"}}
```

两者状态码相同，所以那条老断言毫无区分力。RX-1 改为断言守卫自己的 message，
再补两条：被拒后 A 的 trigger 仍是 `DETECTED/ACKNOWLEDGED` 且没有留下任何 proposal；
同一个事件在**自己**的 Journey 上必须 201（证明拒绝只因边界，不是事件不可解析）。
第二、三条 Journey 全部通过真实产品路径建立（`/journeys` → `/plans/generate` → `/select` → `/start`），
没有直接写库。

验证：干净态 4 passed；`J-CROSS-JOURNEY-TRIGGER` 变异态该用例失败并打印上面那句诊断 → 杀掉。

### RX-2 mock 冒充硬移动真值

结论：`tests/test_qoder_live_hard_fallback.py` 之所以杀不掉 `fallback=None if hard_capture else mock`
的反转，是因为它捕获的 `("a","b")`/`("b","c")` **根本不在 fixture 矩阵里**，
`MockMobilityProvider(strict=True)` 自己就抛 `KeyError`——它证明的是 fixture 的严格性，
不是 fallback 没接上。真正危险的恰是矩阵里的显式条目。RX-2 只捕获一条显式矩阵边
（自动挑一条数值不等于 `default_minutes=20` 的，避免 20 分钟歧义），live 供给者对所有边失败：

- 正确代码：硬捕获没有 mock 可退 → `MobilitySnapshotCaptureError`
- 变异体：mock 递上 15 分钟 → `Failed: DID NOT RAISE` → 杀掉

同文件保留一条软捕获对照，确保没把合法的降级一起打死。

---

## 5. 追加：RX-3 与三项"假杀掉"的复核

### RX-3 陈旧游标（`tests/test_rx3_stale_cursor_fails_closed.py`）

`CX-REC-001` 本身在 Codex 的记录里也被标成 KILLED，但它的门禁 `-k stale` 收集到 0 条测试。
现在有了真门禁，5 条用例覆盖缺失/首/中/末/陈旧五种游标。**在未打补丁的当前顶端实测**：

```
AssertionError: a present-but-unknown cursor was resolved into a fabricated Now: act-0
AssertionError: assert 'act-2' is None      （已完成前缀的场景，看起来完全合理，因而更危险）
```

打上 `CX-REC-001` 后 5 passed；再把 `elif stale_cursor:` 改成 `elif False:`，2 failed → 突变杀掉。
即：**这个缺陷今天仍在 `7f2f5bb` 上活着，且此前没有任何一条测试能发现它。**

### 三个"从未跑到测试"的复核（`raw/mutation_audit_targeted.json`）

| 突变 | Codex 判定 | 复核结果 |
|---|---|---|
| `J-ACK-RESOLVED`（ACK 直接置为 RESOLVED） | KILLED（exit 5，21 deselected） | **确实被杀掉**，但门在别处：`test_v1923_final_code_gate.py::test_v1923_acknowledge_never_resolves_or_hides_recovery` 等 2 条失败。产品没问题，Codex 选错了文件。 |
| `J-STALE-CURSOR-FALLBACK` | KILLED（exit 5，6 deselected） | 原先无人看守 → 现由 RX-3 杀掉。 |
| `J-PROTECTED-C4-DROPPED`（把受保护承诺查询从 C4 换成 C3） | KILLED（exit 4，路径写错从未运行） | **存活**。79 条真值门禁（v1923/v1924/v13/wp06/v12/golden/agent_runtime）全绿，Codex 自己那条 `protected` 用例也通过。 |

第三行是这次恢复里最值得升级的发现：`main.py` 里 `CommitmentModel.level == "C4_Anchored",` 共 4 处，
第 4344 处属于**候选生成前**的硬约束装配（`active_c4_hard_constraints`）。把它换成 C3 后，
生成候选时不再把已锚定的 C4 承诺当硬约束——即行程可以在用户不知情的情况下生成与已付款承诺冲突的方案，
而后端整套真值门禁一致表示没问题。"受保护承诺 survives" 这条契约只在 accept 路径上有看守，
在 generate 路径上没有。

**下一步（RX-4，本次未做）**：走真实付款路径造出 ACTIVE C4 承诺，调 `/plans/generate`，断言候选保留该承诺
（及其 place/时间），并要求该场景在 C3 突变下失败。这条补上后，Codex 那份突变矩阵才算真正 15/15。

## 6. 仍未收口 / 交给 owner 的判断

1. `CX-REC-001` 让 API 在多出一个 `cursor_status` 字段并把 `now_state` 取值为 `STALE_CURSOR`。
   这是内部枚举，前端与文案必须显式映射成旅行者语言，否则违反"内部枚举不得进主 UI"的既有契约。
   合入前应决定：UI 上"游标不可信"要说什么。
2. `CX-REC-003` 的串行化是**进程内**互斥。多进程部署（多个 uvicorn worker）下不成立，
   需要 DB 级锁或唯一约束兜底。补丁可以作为隔离候选先进，但它不是分布式答案。
3. 三条 Playwright 突变（`J-ACK-CLOSES-UNRELATED`、`J-PARTIAL-BUDGET-FULL`、`J-LIVE-FIXED-INDEX`）
   需要重跑并读断言结果，而不是读退出码。命令形如
   `npx playwright test e2e/extreme-live-projection.spec.ts --config=playwright.extreme.config.ts`。
4. `mutation_runner.py` 的判定规则建议改成： collected==0 → `NOT_RUN`；退出码 5/4 → 不是杀掉；
   Playwright 需解析报告而非退出码。
5. 厦门纵向切片（Astra 线）**仍未开始**：`_astra_xiamen_vertical_20260919` 是一个干净的克隆，
   没有任何 trial factory、runner 或脚本。

## 6. 目录内容

- `patches/` — 4 个补丁（3 个关切 + 合并）
- `tests/` — RX-1、RX-2 两条新门禁
- `verify/citynexus` — 已提交冻结（`qoder/recovery-extreme-v2` @ `f331e43`），worktree：
  `wt_base`(0fa1f6c) / `wt_tip`(补丁态) / `wt_tip_clean`(未补丁) / `wt_mut`(变异态)
- `raw/` — 基线与补丁全量日志、名单 diff、`mutation_audit.json`
- 复现命令见 `raw/repro_commands.txt`
