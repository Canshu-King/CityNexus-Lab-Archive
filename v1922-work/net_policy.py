"""Snapshot L — configurable public-provider network policy."""
from pathlib import Path

# 1) provider_config: 新增 network_mode
p = Path("D:/moodle/CityNexus/backend/app/integrations/provider_config.py")
s = p.read_text(encoding="utf-8")
old = '''    ai_enabled: bool = _flag("CITYNEXUS_AI_ENABLED")'''
new = '''    # Public-provider network policy (docs/NETWORK_POLICY.md).
    #   AUTO      - honour the environment/proxy configuration first, then a
    #               bounded direct retry when a public provider fails
    #   ENV_PROXY - always honour the environment proxy configuration
    #   DIRECT    - never use the environment proxy
    # Hardcoding either behaviour was wrong: one execution environment had a
    # broken proxy, and the user's machine runs Mihomo and may need one.
    network_mode: str = os.getenv("CITYNEXUS_PROVIDER_NETWORK_MODE", "auto").strip().lower()

    ai_enabled: bool = _flag("CITYNEXUS_AI_ENABLED")'''
assert old in s, "ai_enabled anchor not found"
s = s.replace(old, new, 1)

helper = '''

def provider_network_mode() -> str:
    """Normalised public-provider network mode."""

    mode = str(ExternalProviderSettings().network_mode or "auto").strip().lower()
    return mode if mode in {"auto", "env_proxy", "direct"} else "auto"


def trust_environment_for_public_providers() -> bool:
    """Whether httpx should honour the environment proxy for public providers.

    ``AUTO`` and ``ENV_PROXY`` honour it; ``DIRECT`` does not.
    """

    return provider_network_mode() in {"auto", "env_proxy"}
'''
s = s.rstrip("\n") + "\n" + helper
p.write_text(s, encoding="utf-8", newline="\n")
import ast; ast.parse(s)
print("provider_config: network policy added")
