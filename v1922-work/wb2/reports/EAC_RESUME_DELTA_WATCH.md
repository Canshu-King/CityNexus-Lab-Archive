# EAC_RESUME_DELTA_WATCH — 2026-09-17（重启后续监）

模式：DELTA WATCH + FINAL RED-TEAM。基线 = WB-O1（overnight-20260917 报告集）。
规则：不重跑全量审计；只在 EAC 检查点看增量；最终裁决等 EAC 终包
`CityNexus-EAC-Overnight-Continuation-Final-20260917.zip` 出现后按
`docs/WORKBUDDY_NEXT_DELTA.md` 六步执行（截至 10:10 尚未出现）。

---

## ⚠️ 审计方法纠错（先于一切增量结论）

09:05 核实：主仓库 `frontend/`、`backend/` 整目录均为 **git untracked**（repo 只跟踪 docs）。
WB-O1 checkpoint-02（02:50）用 `git diff HEAD` 验证「EAC 零内容变更、mtime 是 reset 假象」
——该方法对 untracked 文件天然失效（diff 恒为空）。**该结论作废**。
真实增量以「01:15 基线快照 vs 当前源码」文件 diff 为准。git commit 状态本身仍成立，
且按 NEXT_DELTA 规则不作为就绪判据。

## 检查点 D1 — 09:05–10:10（重启后首个稳定检查点，UI 复验完成）

### 仓库状态
- 分支 `eac/v19.2.2-realphone-codegate`，HEAD 仍 2026-09-05（0 新 commit）。
- EAC 活动：08:49–09:00:51 密集写入后暂停（10:00 检查时无新写入 → 稳定检查点）。
- 集成包 `CityNexus-EAC-WorkBuddy-Findings-Integration-20260917.zip`（08:36 下载）已解包审阅。

### EAC 真实增量（01:15 快照 vs 当前源码 diff --stat）
| 文件 | 增量 | 对应发现 |
|---|---|---|
| PlanWithAiSheet.tsx | +85/−27 | WB-H1 |
| CopilotDock.tsx | +121/−82 | WB-H3 |
| StayExplorer.tsx | +73/−2 | WB-H5 |
| JourneyInboxWorkbench.tsx | +124/−13 | WB-H2（文本路径） |
| V8Experience.tsx | +68/−59 | WB-H2/H4 部分 |
| LocaleContext.tsx | +2/−14 | 文案键 |
| backend main.py | +346/−26 | 配套后端（未逐行审） |
| services.py / v9.py / semantic_intake.py / stay_mobility.py | 多处 | 配套 |

### WB-H1..H5 复验结果（snapshot_0957 隔离栈 8011/5181 + 昨晚 DB，Playwright 移动视口）
| 发现 | 源码层 | UI 层 | 结论 |
|---|---|---|---|
| **WB-H1** AI 假成功 | **FIXED**：planCount 真实门 + `/plans/generate` 恢复路径 + 诚实终态 `NO_PLANS_PRODUCED` | 复验未完成（hub 的 AI 入口定位失败，Today 空白主体仍在拦截入口） | 源码修复可信，终验留给 NEXT_DELTA |
| **WB-H2** 预订导入 | 部分：卡片「价格未知」中文化 ✅；裸 `JSON.parse`(L1822)、主 JSON textarea、`UNKNOWN_REALTIME`、`受保护 C4` 均在 | 敌意非 JSON 粘贴：无崩溃但**无可见错误反馈**（文本滞留输入框）；内部标签双枚举仍在截图实锤 | **OPEN（部分改善）** |
| **WB-H3** Copilot 泄漏 | **FIXED**：humanAction/Intent/Verification 映射 + 消费者页头 | **UI 验证通过**：/v8/agent（新专用 AgentComposer 页）回复零泄漏；「我没有可靠识别这条请求」诚实但略生硬 | **FIXED ✅** |
| **WB-H4** 空白态 | 部分 | 无 journey 态：**已修**（新建行程三步向导，目的地预填厦门）✅；有 journey 态：**仍空白**（53 字符，零 CTA 零空态）截图实锤 | **PARTIAL** |
| **WB-H5** 酒店伪证据 | **FIXED**：空态「还没有可用的住宿候选…不会给你看一张假的价格卡片」；confidence≤0→「暂无供应商证据」 | **UI 验证通过**（honest=true, pseudo=false） | **FIXED ✅** |

### 正面控制组（守护清单）
- 离线只读：**完整保留** ✅（「离线」banner UI 实测）
- 双击防重：未复测（昨晚 WB-DOUBLE-CLICK-TEST 卡片仍在 DB 中显示正常）
- Trips/Map 诚实空态：未复测（本检查点未触碰相关代码）
- Copilot 诚实拒绝直改方案：源码层保留（「我可以给出建议…都会先等你确认」）

### 新发现 / 回归
- **新增正面**：`/v8/agent` 专用 AgentComposer 页（自然语言 + 建议按钮「为什么这样安排？/如果我多待 60 分钟…/找附近的室内地点」，全消费者语言）
- 回归：未发现新问题。注意点：LocaleContext −14 行删键后页面无报错（pageerror=0）。
- 基建备忘：隔离 DB 必须连 `-wal/-shm` 一起拷贝（昨晚旅程数据在 WAL 里，只拷主库会 404 journey）。

### same-Xiamen 进度
- EAC 仍未产出 VISIBLE_UI_TRACE.json（WB-O1 承诺物持续缺失）。
- 触发条件：EAC 恢复写入 ≥3 文件、或终包 zip 出现 → 立即按 NEXT_DELTA 六步做终局 delta。

### 复验脚本与证据
- lab/verify_delta2.js（本轮）、lab/verify_delta.js（第一轮，被 vite 回收打断）
- screenshots/dlt2_00..06（移动视口 390×844 全套）
- evidence/delta_today_journey_text.txt、delta_stay_text2.txt、delta_verify2_summary.json
- 隔离快照：baseline/app_snapshot_0957/（当前 EAC 代码 + 昨晚 DB+WAL）
