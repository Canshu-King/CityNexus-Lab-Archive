# PASS-16 CONTROL LEDGER — CityNexus
维护者：号令者窗口（Qoder 会话 494abfd7）。每轮 `wait/read_chat_session` 或磁盘复核后更新。
本窗口只读三棵受保护树；所有恢复产物在 `D:\moodle\_qoder_recovery_20260919`。

## 观察时刻
2026-09-20 01:29（整合线 HEAD `17c5bb5`，工作树另有 in-flight 未提交改动）
注：项目无版本控制，主线的 in-flight 改动此刻仍在被另一窗口实时编辑，本表所有数字都是该时刻快照。

## 会话与职责
| 会话 | 状态 | 实际在做什么（磁盘核对，非转述） |
|---|---|---|
| `8c66aa92` 继续工作流 | running | Pass-16 Sol convergence 实现线：执行游标权威化、Journey 写串行化、C4 remap、防响应面板 |
| `6af4cf53` 打招呼 | running | GitHub 发布线：源码体积 1.63 GB 分箱、密钥扫描、建第二仓库、分批上传（<100MB/文件） |
| `eb92a402` 日常问候 | ready | 未参与 CityNexus |
| 494abfd7（本窗口） | commander | 派单、独立复核、事实登记；不动共享树 |
| Codex / Astra（非 Qoder 会话） | 中断于额度 | 见"归属变更"，其 Extreme v2 孤儿改动已恢复 |

## 所有权（Owner-based parallelism）
| 区域 | Owner | 其他窗口 |
|---|---|---|
| `backend/app/operations/v9.py` 执行游标 | `8c66aa92` | 只读 |
| `frontend/src/app/V8Experience.tsx` Live 游标 | `8c66aa92` | 只读 |
| `backend/app/main.py` + `commerce/` + `concurrency_guards.py` 串行化 | `8c66aa92` | 只读 |
| `backend/app/replanning/commitment_remap.py` C4 remap | `8c66aa92` | 只读 |
| mobility provenance / physical identity / E2E acceptance policy | FROZEN | 禁止改（GPT 裁决） |
| 本恢复线 `patches/`、`tests/`、`verify/` | 494abfd7 | — |

## 已验证事实（本窗口亲测，解释器 `CityNexus\.venv`，含 ortools）
| 观察对象 | 结果 |
|---|---|
| `7f2f5bb` 未打补丁 | 827 passed / 15 skipped / 0 failed |
| `7f2f5bb` + CX-REC-001/002/003 | 827 / 15 / 0（补丁零回归，失败名单逐条一致） |
| `fec2204` + 其 in-flight 工作集 | 836 passed / 15 skipped / 0 failed |
| `17c5bb5` + 其 in-flight 工作集（01:29 快照） | 865 passed / 15 skipped / 0 failed |
| RX-1 + RX-2 + RX-3 在其最新工作集上 | 9 passed |
| C4 保护谓词 | 仍有 4 处 `CommitmentModel.level == "C4_Anchored",` |
| 把 generate 路径那处换成 C3_Guaranteed 后 | 98 条真值门禁（v1923/v1924/v13/wp06/v12/golden/agent_runtime/**含其新建的 test_sol_concurrency_and_remap.py**）全部通过 → 该路径无看守 |
| `V8Experience.tsx` Live 游标 | 已改为 `liveActivityWindow(...)`（254 行定义，2066/2151 使用） |
| 仍存疑的投影 | 1501 行仍 `activities.find(end_at >= nowMs) ?? activities[0]`，与后端"客户端不得用墙上时间推断"的 docstring 相冲 |

## 归属变更（已通知 `8c66aa92`）
- `CX-REC-001`、`CX-REC-003` **作废**：其实现已是他们的超集（多 `persisted_cursor` 与第二处投影点、`WeakValueDictionary` 锁登记表）。不再向共享树 apply。
- `CX-REC-002` 已落地（前端 `liveActivityWindow`）。
- RX-1 / RX-2 / RX-3 建议进 `backend/tests` 固化（已在其代码上实测通过）。

## OPEN
1. **RX-4（唯一确认无看守的真值缺口）**：`/plans/generate` 前装配硬约束处把 C4 谓词换成 C3 后 98 条门禁全绿。要求：真实付款造 ACTIVE C4 → generate → 断言候选保留该承诺（place + 时间语义），且该用例在 C3 突变下必须失败。
2. **对外裁决口径**：GPT 已接受"17/17 killed / 0 survivors"。本窗口独立复核结论不同——Codex 的 `mutation_runner.py` 把非零退出码当杀掉，而 pytest 收集 0 条测试时退出码即 5，故其原始 15 项中有 3 项从未跑到测试；其中 1 项（ACK≠resolved）实际被 `test_v1923_final_code_gate.py` 杀掉，1 项由 RX-3 补上，1 项（C4 generate）确认仍存活。交接给仲裁时须以此为准。
3. 前端 1501 行墙上时间推断是否也要收进游标权威，需 GPT 判定范围。
4. Astra 厦门纵向切片仍为零产出（空克隆）。

## 口径规则（长期）
- 报后端数字必须注明解释器；缺 ortools 的环境会把全量变成 32–38 条假崩。
- 任何"门禁通过/突变已杀"必须给出收集到的测试条数与 deselected 数，不接受只看退出码。
- 新增对同一片代码的改动前先登记所有权。
