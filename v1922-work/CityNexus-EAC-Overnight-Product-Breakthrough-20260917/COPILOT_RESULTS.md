# COPILOT_RESULTS.md

## Status: PARTIAL

## Fixed in earlier rounds and retained

* `Authority boundary` is no longer primary content; one traveller sentence
  replaces it.
* `Semantic boundary` moved behind a **高级详情** disclosure.
* A sweep of `/v8/hub`, `/v8/trips`, `/v8/map`, `/v8/agent`, `/v8/me`,
  `/v8/live` at both viewports found **no** occurrence of `PlanVersion`,
  `C4_Anchored`, `semantic_key`, `Authority boundary`, `Semantic boundary`,
  `NONESEARCH` or `REQUEST_PLACE_SEARCH`.

## Not done

The acceptance question

> 鼓浪屿好玩吗？

does **not** yet produce a useful Chinese traveller answer with current-trip
context and human action buttons (加入行程 / 安排到第2天 / 地图查看 / 搜索更多).

When the AI provider is unavailable the current behaviour is an honest
"answered offline / I need one more detail" state rather than a useful answer.
Wiring the answer to real place evidence and the current Xiamen trip was not
completed tonight.

## Honest note

The mission asks for a Copilot that does not turn the traveller into a policy
debugger. The vocabulary cleanup achieved that; answer quality did not.
