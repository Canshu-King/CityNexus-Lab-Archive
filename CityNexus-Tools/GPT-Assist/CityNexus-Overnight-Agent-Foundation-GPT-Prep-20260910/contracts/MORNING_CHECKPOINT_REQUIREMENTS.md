# 晨间 Checkpoint 必须回答的问题

1. SRH-01..05 是否全部 PASS？
2. ORT-01..20 是否仍全部 PASS？
3. full backend 实际数字和 exit code？
4. Agent policy 是否持久化？schema 是否可 fresh extract？
5. MCP 是否只能发现 allowlist tools？
6. Agent 是否能改变自己的 policy？答案必须是否。
7. AI auto accept 是否仍走 existing deterministic accept-time gate？
8. degraded provider / CRITICAL / cost over limit 是否会自动执行？默认必须否。
9. payment/refund/C4 modify 是否暴露给 MCP V1？必须否。
10. Agent mutation audit 是否记录 actor/policy decision？
11. idempotency replay 是否只有一次 mutation？
12. Hermes live smoke 是否运行？若 SKIP，原因是什么？
13. Hermes 不存在时 CityNexus 是否完整运行？
14. frontend 是否被修改？若是，build/Playwright 是否 PASS？
15. 哪些属于 IMPLEMENTED / PARTIAL / SIMULATED / PLANNED？
