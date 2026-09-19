# Hermes isolated integration notes

目标不是让 Hermes 接管数据库，而是只让它看到 CityNexus 的安全 MCP tools。

建议顺序：

1. CityNexus backend 先独立启动并通过 tests。
2. CityNexus MCP adapter 独立启动。
3. Hermes 只做 MCP tool discovery。
4. 确认没有 terminal/file/browser/payment/set_policy/C4 mutation tools。
5. 才执行 Journey Agent smoke。

如果 Hermes 当前安装版本的 MCP CLI/config 格式与示例不同，以本机版本为准，不要为对齐这份示例去降级 Hermes。
