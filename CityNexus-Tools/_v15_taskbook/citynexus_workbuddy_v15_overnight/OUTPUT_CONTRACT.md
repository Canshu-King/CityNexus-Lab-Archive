# WorkBuddy 输出契约

最终隔离工作区必须至少生成：

- `WORKBUDDY_V15_NIGHT_REPORT.md`
- `COPILOT_SEMANTIC_BENCHMARK.jsonl`
- `COPILOT_BENCHMARK_RESULTS.md`
- `CROSS_CITY_GENERICITY_FINDINGS.md`
- `AUTHORITY_RED_TEAM_FINDINGS.md`
- `CODEX_MERGE_AFTER_V15.md`
- `patches/V15_COPILOT_TESTS_ONLY.patch`
- `patches/V15_REFERENCE_IMPLEMENTATION_OPTIONAL.patch`（只有确实有价值时）
- `evidence/test_results.txt`
- `evidence/scenario_summary.json`

最后打包：

`D:\moodle\CityNexus-Tools\CityNexus-WorkBuddy-V15-NightLab-20260914.zip`

低冲突的 `TESTS_ONLY.patch` 是最重要产物。可选 reference implementation 不允许被包装成“必须覆盖 Codex 代码”。
