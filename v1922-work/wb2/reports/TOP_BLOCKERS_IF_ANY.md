# TOP_BLOCKERS_IF_ANY — 终局阻塞项

按「试用首路径伤害 × 是否有包内反证」排序。前三项任一存在即足以维持 BLOCKED。

## B1 — 证据链诚信：旗舰修复零可见证明（F1 + GATE #2/#5）
READY 声明的核心叙事（Copilot 能好好回答旅行者问题）在包内**没有任何修复后证据**：
canonical trace（11:17）该步骤 `status:"empty"` 无回复；run1（14:55）是修复前旧文案；
真正的修复落在 14:56:24，晚于全部包内 trace。且 ledger「归档=run1」标签与事实不符，
「零枚举泄漏」被包内 canonical trace 自身反向证伪。
**修复成本：低（补一轮修复后 trace + 更正 ledger）。但在补齐前，READY 不可信。**

## B2 — Me 页把工程内部当主 UI（F3，REPRODUCED）
默认 Me 页 kicker「我的 · 权限边界」+ 大字 `ADVISORY` 枚举（EAC 自己的截图即如此）。
旅行者第一眼看不懂、也不该看懂这个词。已有「厦门」映射却仍显示 `CN-XIAMEN` 类代码。
**修复成本：低（折叠到 Advanced + 人类化文案）。**

## B3 — 真相缺陷三连：价格与预算说了谎（F6/F7/F8）
- 免费景点显示「暂无价格」（`amount_minor > 0` 当"知道价格"）——试用期最常见门票类型直接出错
- 部分价格覆盖仍打「预算内/超预算」——假置信
- 39 天/2 人/¥3000 无任何预算提示——任务书明确要求的 advisory 缺失
**修复成本：中（三个独立小函数 + 一个新提示组件）。**

## B4 — Wallet 默认面内部标签 + 崩溃风险（F4/F5）
`Journey Memory`/`UNKNOWN_REALTIME`/`受保护 C4` 见客；/v8/bookings 裸 `JSON.parse`
无 catch（粘贴自然语言即静默无反馈，曾实测 pageerror）。Trips 主路径已修好，
但用户刷新/深链到 wallet 路由就掉回旧世界。
**修复成本：低-中（P1/P1b/P3 影子补丁已验证可复用，见 PATCH_INDEX.md）。**

## B5 — 有 journey 深链白屏（F9）
`/v8/today`、`/v8/copilot` 不在 routeFromPath 的 13 键里：刷新即白屏（53 字符）。
试用者分享链接或刷新页面即触发。
**修复成本：极低（两个别名映射）。**

## B6 — 旧方案假成功结构风险（F10）
`planCount > 0 → COMPLETED` 不区分新运行产物与既有方案；本环境无法构造前置
（places 池为空——这也意味着真实厦门数据下 AI 规划依然空转，其环境方案可生成
与回放环境行为不一致本身就是一个待解释项）。

## 非阻塞
- F12 包缺 `data/v9/city_operations.json`（仓库有）：工程债，记 PATCH/发布流程整改
- F11 弱断言：证据口径问题，随 B1 一并补
