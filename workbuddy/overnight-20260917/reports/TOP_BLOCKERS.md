# TOP_BLOCKERS.md — 顶级阻塞项（Phase 9）

按「小米 13 Ultra 真实试用者首次使用」的命中顺序排序。每项均含隔离副本实测证据。

## BLK-1 · [P0] AI 规划假成功 —— 核心流程首用即断裂
- 现象：真实新 journey 提交规划请求 → UI stepper 全打勾 +「方案已准备好」；实际 `plan_versions=0`、方案页/行程/酒店全空
- 根因：`PlanWithAiSheet.tsx` mission 缺失时硬编码 `COMPLETED`；且 mission COMPLETED 不校验 plan 是否真实 materialize
- 命中率：预置演示数据之外的任何真实请求（agent 诚实拒绝编造 → 必然空转）
- 证据：`fa_*` 截图、`evidence/db_counts.txt`、`db_agent_runs.txt`、`api_plans_0250.json`
- 状态：影子补丁 **P2** 已验证修复可行（诚实警示卡）；后端 mission 语义需 EAC 跟进

## BLK-2 · [P1] 预订导入三重静默失败
- 非 JSON 粘贴 → `JSON.parse` unhandled rejection，零反馈（最常见输入直接坏）
- JSON 中价格字段被静默丢弃，违背「受保护」承诺
- 文本提取失败 → 裸英文「DeepSeek Responses request failed」直接展示
- 证据：`bk_04`、`ibx_01`、pageerror 记录、wallet API
- 状态：UI 侧 **P1/P1b/P3** 已验证修复；后端 amount_minor 落库需 EAC 核实

## BLK-3 · [P1] 消费者界面系统性泄漏内部术语与供应商品牌
- Copilot：REQUEST_PLACE_SEARCH 巨型按钮、DISCOVER 徽章、DeepSeek/Hermes 标语、Semantic/Execution/Truth 状态条
- 票夹：UNKNOWN_REALTIME、「受保护 C4」；权威记忆 "Journey Memory"、"Travel fact · UNKNOWN…"；酒店页 "0% confidence"、"explicit"
- 汉堡菜单暴露开发者路由面板（TODAY/PLAN/TRAVEL/SYSTEM、「恢复与执行」「智能守护」）
- 证据：`cp_06`、`bk_02`、`ibx_00`、`ht_01`、`tab_menu_open`
- 状态：Copilot 域 **P3** 已修；其余为小改动量文案/渲染修复（见 TOP_FIXES）

## BLK-4 · [P1] 无方案空态 = 空白页
- 「今天」tab（默认落地页）主体零内容零 CTA；`/v8/copilot` 路由同样空白且面包屑错位
- 对照：行程/地图 tab 有合格空态 → 能力存在，属遗漏
- 证据：`cp_04_today_diag` + API 拦截（experience 200 但 options=[]）
- 状态：未出补丁（产品决策项，复用行程空态组件即可）

## BLK-5 · [P2] 实施方（EAC）产出不可追溯
- 截至 02:50：分支 `eac/v19.2.2-realphone-codegate` 存在但 0 commit；tracked 内容仅 .gitignore 变更；reflog 8 次同点 reset 制造 mtime 假象
- 风险：晨检时无法评估整夜实施的真实进度与质量
- 证据：`reports/eac_checkpoint_02_snapshot.txt`、`eac_git_branches_0250.txt`、`eac_diff_verify_0250.txt`
- 状态：待 final checkpoint（07:00）复核

## 非阻塞正面记录（避免误伤）
- 双击防重有效（unique index 兜底）；缺字段导入有审核提示；行程/地图诚实空态；Copilot 回复内容诚实（「搜索结果不会直接写入方案」）；多模态收件箱三路导入设计完整
- **离线态设计成熟**（补测 TC-13）：offline-snapshot + Dexie + 「离线·只读 / 财务操作已禁用」完整语义
- **Copilot 重规划路径双诚实**（补测 TC-06）：明确告知「不会由 Copilot 直接改写当前方案」+ 友好按钮「调整行程方案」，零泄漏
