# Codex merge handoff template

WorkBuddy最终的 `CODEX_MERGE_AFTER_V15.md` 至少回答：

1. 哪些 findings 已被新测试稳定复现；
2. `V15_COPILOT_TESTS_ONLY.patch` 修改哪些文件，是否低冲突；
3. 哪些测试预期 Codex 当前实现会通过/失败；
4. optional reference patch 中哪些思路值得采纳，哪些不要采纳；
5. 跨城市 timezone/currency/city 泄漏是否发现实锤；
6. DeepSeek V4 Flash 在哪些意图上最稳定，哪些需要 server deterministic guard；
7. 明早合流顺序建议，最多 8 项；
8. 不要要求重新跑一整晚审计。
