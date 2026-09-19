# EXECUTIVE_PRODUCT_AUDIT.md — 执行级产品审计（Phase 9）

- 审计方：WorkBuddy 独立并发红队（GLM-5.3-Flash），2026-09-17 过夜窗口 00:30–03:10 主审计 + 晨检复核
- 对象：CityNexus 消费者端（V8 体验壳 + Copilot + 票夹 + 规划 + 酒店），以「小米 13 Ultra 真实试用者」为基准人格
- 方法：隔离副本全链路实测（后端 8011 / 前端 5181 / 真 journey / 浏览器内 API 拦截）+ 主仓库 git 只读审计 + 10 屏 UI 参考对比。**未修改权威仓库任何文件**
- 详细报告：BASELINE_STATE / CROSS_LAYER_PRODUCT_MAP / CONSUMER_LANGUAGE_AUDIT / MULTIMODAL_UI_REDTEAM / VISUAL_PARITY_MATRIX / ACCEPTANCE_INTEGRITY_REPORT / PRODUCT_TRUTH_REDTEAM / HOSTILE_USER_TESTS / EAC_PROGRESS_TIMELINE / PATCH_INDEX / TOP_BLOCKERS / TOP_FIXES_FOR_EAC

---

## 一页结论

**产品骨架优秀，成败细节失守。** 权限边界（我的页）、多模态收件箱、诚实空态（行程/地图）、agent 拒绝编造的诚实后端——这些是同类产品少有的正确设计。但**首次使用的主路径（AI 规划）在真实数据下必然空转，而 UI 谎报「方案已准备好」**；预订导入、文本提取、酒店空态全部存在「静默失败/伪数据」；内部术语与供应商品牌（DeepSeek/Hermes/C4/REQUEST_PLACE_SEARCH）成规模泄漏到消费者界面。

12 项真相审查中 2 项谎言级、5 项呈现缺陷、4 项诚实正面（PRODUCT_TRUTH_REDTEAM.md）。16 屏视觉矩阵 4 FAIL / 6 PARTIAL / 4 PASS（VISUAL_PARITY_MATRIX.csv）。

## 试用者首用 10 分钟模拟（当前代码）
1. 打开 App → 「今天」页**空白**（BLK-4）
2. 点「行程」→ 空态良好 → 点「AI 帮我规划」→ 输入需求 → stepper 打勾 →「方案已准备好」→ **实际无任何方案**（BLK-1），行程/地图/酒店全空
3. 复制 12306 短信到票夹导入框 → **无任何反应**（BLK-2）
4. 滚动到多模态收件箱 → 文本提取 → 9 秒后**「DeepSeek Responses request failed」**（BLK-2）
5. 问 Copilot「鼓浪屿好玩吗」→ 回复诚实，但出现巨型 **REQUEST_PLACE_SEARCH** 按钮与 DeepSeek/Hermes 标语（BLK-3）

结论：信任在 10 分钟内被摧毁三次。

## 修复可达性（关键乐观信号）
- 所有 P0/P1 的 UI 侧修复已由 WorkBuddy 影子补丁**实现并验证**（PATCH_INDEX.md，4 个 patch，截图 pt_*）
- 修复总量 ≈ 一个工作日的前端工作 + 后端两处语义修正（mission 状态区分、amount_minor 落库）
- BLK-5（EAC 产出不可追溯）是流程风险而非技术风险

## 判定
详见 `WORKBUDDY_FINAL_VERDICT.md`：**BLOCKED**（截至本报告时点），并附明确的转 ACCEPTS 条件与晨检复核程序。
