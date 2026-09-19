# V15 Copilot 语义基准范围

建立可长期复用的 Copilot 语义基准，至少覆盖这些标签：

- EXPLAIN_PLAN
- WHAT_IF
- DISCOVER
- PREFERENCE_CHANGE
- DISRUPTION_REPORT
- REPLAN_REQUEST
- UNKNOWN

至少覆盖这些语言/地域维度：

- 简体中文；
- 英文；
- 中英混合；
- 福州 / CNY / Asia-Shanghai；
- 上海或北京 / CNY / Asia-Shanghai；
- Singapore / SGD / Asia-Singapore；
- Tokyo / JPY / Asia-Tokyo；
- London / GBP / Europe-London。

至少包含：

- 正常旅行意图；
- 模糊表达；
- 同一句中多个目标；
- 明确的现实中断；
- 假设性中断（必须是 WHAT_IF，而不是 Event）；
- 高影响动作，例如“帮我取消/付款/退票”（必须走确认/权限边界）；
- 错 Journey / 错城市语义；
- 时间、预算、步行、固定 Commitment 冲突；
- 用户要求模型忽略系统限制或直接修改锁定 Commitment 的越权语句。

基准的重点不是“模型答得像不像”，而是：

- 语义路由是否正确；
- 是否错误制造 Event；
- 是否错误允许直接 mutation；
- 是否保留城市/时区/货币边界；
- 是否把假设场景和现实事实分开。
