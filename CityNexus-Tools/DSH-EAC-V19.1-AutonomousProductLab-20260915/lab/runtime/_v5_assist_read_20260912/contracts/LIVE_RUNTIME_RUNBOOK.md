# Live Runtime Runbook

Do not persist credentials in the repository or checkpoint.

Expected environment variables:
- DEEPSEEK_API_KEY or CITYNEXUS_AI_API_KEY
- CITYNEXUS_HERMES_API_URL
- CITYNEXUS_HERMES_API_KEY
- CITYNEXUS_HERMES_MODEL
- optional CITYNEXUS_LIVE_VALHALLA_URL

The V5 final report must distinguish:
1. Native DeepSeek model-backed run
2. Literal Hermes model-backed run
3. MCP protocol verification
4. deterministic Guardian fallback

A tool-discovery test is not a Hermes model E2E.
A native DeepSeek tool loop is not Hermes.
A deterministic Guardian run is not model-backed.

Use process-only secrets and run a final secret scan.
