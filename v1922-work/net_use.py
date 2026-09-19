"""Use the configurable network policy at every public-provider client."""
from pathlib import Path

# real_city.py 两处
p = Path("D:/moodle/CityNexus/backend/app/integrations/discovery/real_city.py")
s = p.read_text(encoding="utf-8")
old = '''        # ``trust_env=False``: a machine-wide proxy makes these public endpoints
        # time out (ConnectTimeout) even though they are reachable.
        self.client = client or httpx.Client(
            timeout=settings.real_city_timeout_seconds, trust_env=False
        )'''
new = '''        # Public-provider network policy (docs/NETWORK_POLICY.md): honour the
        # environment/proxy configuration by default so a Mihomo setup works,
        # and let the operator pin DIRECT or ENV_PROXY explicitly.
        self.client = client or httpx.Client(
            timeout=settings.real_city_timeout_seconds,
            trust_env=trust_environment_for_public_providers(),
        )'''
count = s.count(old)
s = s.replace(old, new)
if "from app.integrations.provider_config import" not in s:
    s = s.replace(
        "from app.core.config import settings",
        "from app.core.config import settings\n"
        "from app.integrations.provider_config import trust_environment_for_public_providers",
        1,
    )
p.write_text(s, encoding="utf-8", newline="\n")
import ast; ast.parse(s)
print(f"real_city.py: {count} client(s) updated")

# stay_osm.py
p2 = Path("D:/moodle/CityNexus/backend/app/integrations/stay_osm.py")
s2 = p2.read_text(encoding="utf-8")
old2 = "timeout=max(30.0, settings.real_city_timeout_seconds), trust_env=False"
new2 = ("timeout=max(30.0, settings.real_city_timeout_seconds),\n"
        "            trust_env=trust_environment_for_public_providers(),")
assert old2 in s2, "stay_osm client not found"
s2 = s2.replace(old2, new2, 1)
if "trust_environment_for_public_providers" not in s2.split("class OsmAccommodationProvider")[0]:
    s2 = s2.replace(
        "from app.integrations.provider_config import ExternalProviderSettings",
        "from app.integrations.provider_config import (\n"
        "    ExternalProviderSettings,\n"
        "    trust_environment_for_public_providers,\n"
        ")",
        1,
    )
p2.write_text(s2, encoding="utf-8", newline="\n")
import ast; ast.parse(s2)
print("stay_osm.py updated")
