# HOSTILE_USER_TESTS.md — 敌意用户 / 失败态测试（Phase 6）

- 执行环境：隔离副本（后端 8011 / 前端 5181），playwright-core + chromium-1243，390×844 @2x zh-CN
- journey：`2bbe2657-…`（真实创建流产物），测试数据均带 `WB-` 前缀
- 判定：PASS = 行为可接受；FAIL = 损害消费者信任；PARTIAL = 可用但有明确缺陷

| # | 场景 | 步骤 | 预期 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|------|
| TC-01 | 有效预订 JSON 导入 | 粘贴完整 RAIL JSON → 审核并保护 | 成功反馈 + 卡片关键事实可核对 | toast「预订已确认并受保护」✓；但价格被丢弃（价格未知）、出发地/目的地不显示 | PARTIAL | bk_02 + wallet API |
| TC-02 | 缺字段 JSON | `{"reservation_type":"HOTEL"}` | 明确告知缺什么 | toast「预订需要审核后才能成为承诺」——不告知缺哪些字段、草稿不可见不可续填 | PARTIAL | bk_03 |
| TC-03 | 非 JSON 自然语言 | 粘贴 12306 短信文本 → 审核并保护 | 友好错误或转文本提取 | `JSON.parse` 抛 SyntaxError（unhandled rejection），界面零反馈 | **FAIL** | bk_04 + pageerror 记录 |
| TC-04 | 双击提交防重 | 两次快速点击「审核并保护」 | 只创建一条 | 仅 1 条记录（unique index + busy 状态兜底） | PASS | bk_05 + refs |
| TC-05 | Copilot 消费问句 | 「鼓浪屿好玩吗？适合下午去吗？」 | 中文答复 + 可理解的动作 | 中文回复诚实（「搜索结果不会直接写入方案」）✓；但附带 REQUEST_PLACE_SEARCH 巨型枚举按钮 + DISCOVER 徽章 | PARTIAL | cp_06 |
| TC-06 | Copilot 重规划问句 | 「下暴雨了，帮我调整明天的安排」 | 诚实响应 | v2 脚本发送机制失效（未点中「询问 Copilot」），v3 未重跑此问句 | 未完成 | — |
| TC-07 | 直接刷新每个 tab | goto /v8/{trips,map,me} | 各页正常渲染 | 全部正常（无白屏、无路由丢失） | PASS | tab_*.png |
| TC-08 | 无方案空态遍历 | 新 journey 无 plan 浏览 Today/Copilot | 空态 + 引导 | **Today 主体纯空白零 CTA**；/v8/copilot 路由内容空白（面包屑仍是「今天」） | **FAIL** | cp_04_today_diag |
| TC-09 | 无酒店候选 | 菜单→住宿选择 | 诚实空态 + 引导采集 | 渲染「费率证据」伪卡（Provider price unavailable · explicit / — → — / captured hotel · 0% confidence） | **FAIL** | ht_01 |
| TC-10 | 开发者面暴露 | 点「菜单」 | 消费者级导航 | 暴露 TODAY/PLAN/TRAVEL/SYSTEM 路由分类 +「恢复与执行」「智能守护」「旅行者画像」等内部页 | **FAIL** | tab_menu_open |
| TC-11 | 文本提取服务失败 | 粘贴确认文本 → 提取文本草稿（DeepSeek 不可用） | 中文失败态 + 指引 | 裸英文「DeepSeek Responses request failed」直接展示，~9s 无中间态 | **FAIL** | ibx_01 + trace |
| TC-06 | Copilot 重规划问句 | 「下暴雨了，帮我调整明天的安排」 | 诚实响应 | 「已识别为重新规划请求。需要通过现有确定性可行性和授权路径生成方案，不会由 Copilot 直接改写当前方案。」+ 友好按钮「调整行程方案」，零泄漏 | **PASS** | of_03 + offline_replan_trace.json |
| TC-12 | 手动表单提交 | 填 RAIL 全字段 → 预览这条预订 | 草稿创建反馈 | 草稿静默创建，自动切回粘贴 tab，无任何成功消息 | PARTIAL | ibx_04 + submitManual 源码 |
| TC-13 | 断网离线态 | 在线预热 → setOffline → 硬刷新 | 离线提示 + 只读缓存 | 「离线·只读」「你未来 24 小时已保存」「网络不可用·正在显示只读的已保存行程」「离线状态下财务操作已禁用」——完整诚实离线设计 | **PASS（亮点）** | of_01 |

## 失败模式归纳（按伤害排序）
1. **静默失败族**（TC-03/11/12）：错误被吞或裸抛，用户无法区分「坏了」和「没点上」——同一页面两种错误处理标准（extractText 有 catch，JSON 框没有）
2. **空态缺失族**（TC-08/09）：把「无数据」渲染成空白或伪证据卡，而不是可行动的引导；行程 tab 证明团队会做空态（「先让 AI 帮你规划」+CTA），Today/酒店/方案比较三处未做
3. **内部语言族**（TC-05/10）：枚举按钮、路由分类、承诺等级 C4、供应商品牌 DeepSeek/Hermes 直接见客

## 未覆盖（诚实声明）
- 断网/飞行模式切换、GPS 权限拒绝、荒谬预算（setup 表单边界值）、跨日期回退预订——受时间窗限制未执行；setup 表单本身样式与参考割裂问题见 CONSUMER_LANGUAGE_AUDIT / checkpoint-01 记录
