# Hermes 接入 CityNexus 的边界

## 推荐集成方式

不要把 Hermes 仓库揉进 FastAPI。

采用：

```text
Hermes Agent
  -> MCP client
  -> CityNexus dedicated MCP server
  -> CityNexus Agent Tool Gateway
  -> existing HTTP/API/domain authority
```

这样未来换 Hermes、GPT Agent、Claude Agent 或其他 MCP host 时，CityNexus 核心不需要重写。

## MCP Server 建议位置

```text
agent-mcp/
  pyproject.toml
  citynexus_mcp/
    server.py
    client.py
    schemas.py
  tests/
```

建议它作为独立 adapter package，默认连接：

```text
CITYNEXUS_API_BASE_URL=http://127.0.0.1:8000
```

MCP adapter 不准直接 import `app.db.*`。

## Hermes 配置

优先让 Hermes 作为 MCP client 连接 CityNexus server。

如果本机 Hermes 已安装：

1. 先读取当前安装版本的 MCP 文档/CLI；
2. 只添加一个 `citynexus` MCP server；
3. 通过 server 自身 allowlist 缩小工具面；
4. Hermes runtime profile 禁用 terminal/file/browser 等不需要的工具；
5. 先做 tool discovery smoke，再做一条 Journey Agent smoke。

不要让 `Hermes API Server` 的完整默认工具面直接成为 CityNexus product runtime，因为其工具面可能包括 terminal/file/browser。

## V1 Hermes smoke

最小 smoke 不要求 LLM 真接真实 provider。

优先验证：

```text
Hermes sees citynexus tools
-> inspect_twin
-> request_replan
-> receives structured result
```

只有本地已有模型凭证时，再做：

```text
自然语言：
“不要影响已付款游船，帮我处理 Tech Art 关闭。”

Hermes
-> inspect_twin
-> request_replan
-> compare
-> accept_replan only if policy allows
```

如果 Hermes 安装/网络/模型凭证不可用：

- 标记 live smoke SKIPPED_EXTERNAL_DEPENDENCY；
- 不能因此让 CityNexus tests 失败；
- 仍要完成 MCP contract 和 mock integration tests。
