# CityNexus 产品与 GitHub 采用背景，供 Overnight Goal 使用

## 产品核心

CityNexus = Adaptive Urban Journey Orchestration Platform。

核心不是普通旅游推荐，而是 Journey Continuity：

```text
Journey Twin
+ durable Commitment / C4
+ verified provider facts
+ deterministic feasibility
+ Opportunity Window
+ dynamic replanning
+ explainable diff
+ user/agent authorization
```

## 当前已完成主线

```text
Backend-connected Vertical Slice        FROZEN_PASS
Valhalla / Frozen Mobility Runtime      FROZEN_PASS
Open-Meteo Weather Runtime              FROZEN_PASS
OR-Tools Solver Runtime V1              LOCAL_PASS / external hardening pending
```

## 下一产品升级

AI 从 explanation Copilot 升级为受约束 Journey Agent：

```text
AI Agent
-> Safe Tools
-> Delegation Policy
-> Deterministic Gate
-> Domain Command
-> Audit
```

## GitHub / 开源项目定位

### 当前直接相关

- `google/or-tools`
  - 当前 Solver Runtime V1。
  - Candidate Generator，不是 authority。

- `NousResearch/hermes-agent`
  - 计划作为 Journey Agent orchestration layer。
  - 建议通过 MCP 连接 CityNexus，不直接揉进 FastAPI。

- `modelcontextprotocol/python-sdk` / Python `mcp`
  - 用于 CityNexus dedicated MCP adapter。
  - optional integration，不能成为核心 app 强依赖。

### 已使用/保留

- `valhalla/valhalla`
  - mobility evidence。

- `open-meteo/open-meteo`
  - weather/context evidence。

- `microsoft/playwright`
  - backend-connected E2E。

- `statelyai/xstate`
  - frontend workflow orchestration。

- `maplibre/maplibre-gl-js`
  - later real map。

- `Turfjs/turf`
  - frontend spatial helpers。

- `shadcn-ui/ui`
  - later UI polish。

### 重新定位

- `BerriAI/litellm`
  - 当前已有 explanation provider foundation。
  - 如果 Hermes provider layer 足够，可降级为 optional，不要形成 Hermes -> LiteLLM -> provider 的无意义套娃。

### Later

- `MasterKale/SimpleWebAuthn`
  - payment/refund/protected action step-up。

- `stripe-samples/accept-a-payment`
  - payment demo adapter。

### 不是产品 runtime

- `miuuyy/codex-chatgpt-web`
  - 开发工具。

- `saerda8/codex-astra-team`
  - 开发工作流实验。
