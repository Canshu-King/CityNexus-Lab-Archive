# Literal Hermes Runtime Proof

V6 should try to make Hermes a real primary runtime, not a label.

Current external research indicates Hermes Agent is actively maintained.
Use a current stable Hermes release rather than the old 0.19-era assumption when possible.

Target proof:

Chinese standing/recovery mission
→ literal Hermes Agent runtime
→ DeepSeek model provider
→ CityNexus MCP V2
→ Hermes chooses inspect/search/plan/action tools
→ Agent Gateway
→ CP-SAT V2
→ Policy
→ Domain mutation

Requirements:
- capture exact Hermes version;
- no terminal/file/browser/raw SQL capability in the product CityNexus tool surface;
- persist normalized AgentRun steps;
- preserve NativeDeepSeekRuntime fallback;
- report Hermes and Native DeepSeek separately.

Do not fake the proof by pointing the existing native loop at an endpoint and renaming provider_key.
